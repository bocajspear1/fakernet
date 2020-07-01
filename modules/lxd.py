import shlex
import time

from lib.base_module import LXDBaseModule
import lib.validate as validate

import pylxd

PULL_SERVER = "https://images.linuxcontainers.org"
PULL_IMAGES = {
    "ubuntu_1804": "ubuntu/18.04",
    "ubuntu_1604": "ubuntu/16.04",
    "centos7": "centos/7",
    "alpine_310": "alpine/3.10"
}

BUILD_BASE_IMAGES = {
    "ubuntu_1804_base": {
        "template": "ubuntu_1804",
        "commands": [
            "apt-get update",
            "apt-get -y dist-upgrade",
            "apt-get -y install openssh-server tmux",
            "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config",
            "service ssh restart",
        ]
    },
    "ubuntu_1604_base": {
        "template": "ubuntu_1604",
        "commands": [
            "apt-get update",
            "apt-get -y dist-upgrade",
            "apt-get -y install openssh-server tmux",
            "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config",
            "service ssh restart",
        ]
    },
    "centos7_base": {
        "template": "centos7",
        "commands": [
            "dhclient",
            "yum -y upgrade",
            "yum -y install openssh-server tmux",
            "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config",
            "systemctl restart sshd",
        ]
    }
}

BUILD_SPECIALIZED_IMAGES = {
    "ubuntu_1804_lamp": {
        "template": "ubuntu_1804_base",
        "commands": [
            "apt-get -y install apache2 mysql-server libapache2-mod-php"
        ]
    },
    "ubuntu_1604_lamp": {
        "template": "ubuntu_1804_base",
        "commands": [
            "apt-get -y install apache2 mysql-server libapache2-mod-php"
        ]
    },
    "centos7_lamp": {
        "template": "centos7_base",
        "commands": [
            "yum -y install httpd php php-mysqlnd php-cli mariadb",
        ]
    },
    "ubuntu_1804_relay": {
        "template": "ubuntu_1804_base",
        "commands": [
            "apt-get -y install socat apache2 libapache2-mod-php"
        ]
    },
}

class LXDManager(LXDBaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View containers"
        },
        "add_container": {
            "_desc": "Add a new container",
            'fqdn': "TEXT",
            "ip_addr": "IP_ADDR",
            "password": "PASSWORD",
            "template": "TEXT",
        },
        "remove_container": {
            "_desc": "",
            'id': "INTEGER"
        },
        "start_container": {
            "_desc": "",
            'id': "INTEGER"
        },
        "stop_container": {
            "_desc": "",
            'id': "INTEGER"
        },
        "list_templates": {
            "_desc": ""
        }
        
    } 

    __SHORTNAME__  = "lxd"
    __DESC__ = "Module for LXD containers"
    __AUTHOR__ = "Jacob Hartman"


    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM lxd_container;") 
            results = dbc.fetchall()
            new_results = []
            for row in results:
                new_row = list(row)
                container_name = row[1].split(".")[0]
                _, status = self.lxd_get_status(container_name)
                new_row.append(status[0])
                new_row.append(status[1])
                new_results.append(new_row)

            return None, {
                "rows": new_results,
                "columns": ['ID', "container_fqdn", "ip_addr", 'template', 'built', 'status']
            } 
        elif func == "list_templates":
            template_list = []

            for item in BUILD_SPECIALIZED_IMAGES:
                template_list.append([item])

            for item in BUILD_BASE_IMAGES:
                template_list.append([item])
            return None, {
                "rows": template_list,
                "columns": ["template"]
            }
        elif func == "add_container":
            perror, _ = self.validate_params(self.__FUNCS__['add_container'], kwargs)
            if perror is not None:
                return perror, None


            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']
            template = kwargs['template']
            password = kwargs['password']

            dbc.execute('SELECT * FROM lxd_container WHERE ip_addr=? OR fqdn=?', (ip_addr, fqdn))
            result = dbc.fetchone()
            if result:
                return "A container of that name or IP already exists", None

            dbc.execute('INSERT INTO lxd_container (fqdn, ip_addr, template) VALUES (?, ?, ?)', (fqdn, ip_addr, template))
            self.mm.db.commit()

            lxd_id = dbc.lastrowid

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=ip_addr, description="LXD - {}".format(fqdn))
            if error is not None:
                return error, None

            error, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=ip_addr)
            if error is not None:
                return error, None 

            container_name = fqdn.replace(".", "-")

            if template not in BUILD_BASE_IMAGES and template not in BUILD_SPECIALIZED_IMAGES:
                return "Unsupported template", None

            error, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=ip_addr)
            if error:
                return error, None

            try:
                container = self.mm.lxd.containers.create({
                    'name': container_name, 
                    'source': {'type': 'image', 'alias': template},
                    'config': {

                    },
                    "devices": {
                        "eth0": {
                            "ipv4.address": ip_addr,
                            "type": "nic",
                            "nictype": "bridged",
                            "parent": switch
                        }
                    },
                }, wait=True)
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            error, _ =  self.run("start_container", id=lxd_id)
            if error != None:
                return error, None

            time.sleep(5)
            serror, _ =  self.lxd_execute(container_name, "echo root:{} | chpasswd".format(password))
            if serror is not None:
                return serror, None
            return None, lxd_id
            
        elif func == "remove_container":
            perror, _ = self.validate_params(self.__FUNCS__['start_container'], kwargs)
            if perror is not None:
                return perror, None

            lxd_id = kwargs['id']
            
            # Get server ip from database
            dbc.execute("SELECT fqdn, ip_addr FROM lxd_container WHERE lxd_id=?", (lxd_id,))
            result = dbc.fetchone()
            if not result:
                return "Container does not exist", None

            fqdn = result[0]
            ip_addr = result[1]

            container_name = fqdn.replace(".", "-")

            self.run('stop_container', id=lxd_id)

            # Remove the IP allocation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=ip_addr)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=ip_addr)
            if err is not None:
                return err, None

            # Remove from database
            dbc.execute("DELETE FROM lxd_container WHERE lxd_id=?", (lxd_id,))
            self.mm.db.commit()

            try:
                container = self.mm.lxd.containers.get(container_name)
                container.delete()
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            
            
            return None, True
        elif func == "start_container":
            perror, _ = self.validate_params(self.__FUNCS__['start_container'], kwargs)
            if perror is not None:
                return perror, None

            lxd_id = kwargs['id']
            
            # Get server ip from database
            dbc.execute("SELECT fqdn, ip_addr FROM lxd_container WHERE lxd_id=?", (lxd_id,))
            result = dbc.fetchone()
            if not result:
                return "Container does not exist", None

            fqdn = result[0]
            ip_addr = result[1]

            container_name = fqdn.replace(".", "-")

            return self.lxd_start(container_name, ip_addr)

            
        elif func == "stop_container":
            perror, _ = self.validate_params(self.__FUNCS__['stop_container'], kwargs)
            if perror is not None:
                return perror, None

            lxd_id = kwargs['id']
            
            # Get server ip from database
            dbc.execute("SELECT ip_addr, fqdn FROM lxd_container WHERE lxd_id=?", (lxd_id,))
            result = dbc.fetchone()
            if not result:
                return "Container does not exist", None

            server_ip = result[0]
            fqdn = result[1]

            container_name = fqdn.replace(".", "-")


            _, status = self.lxd_get_status(container_name)
            if status[1].lower() == "stopped":
                return "Container is already stopped", None

            try:
                container = self.mm.lxd.containers.get(container_name)
                container.stop()
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            return None, True
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='lxd_container';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE lxd_container (lxd_id INTEGER PRIMARY KEY, fqdn TEXT, ip_addr TEXT, template TEXT);")
            self.mm.db.commit()

    
    def build(self):

        self.print("Pulling down LXC images...")
        for image_name in PULL_IMAGES:
            try:
                self.mm.lxd.images.get_by_alias(image_name)
            except pylxd.exceptions.NotFound:

                self.print("Pulling in {} - {}".format(PULL_SERVER, PULL_IMAGES[image_name]))
                image = self.mm.lxd.images.create_from_simplestreams(PULL_SERVER, PULL_IMAGES[image_name])

                found = False
                for alias in image.aliases:
                    if alias['name'] == image_name:
                        found = True
                if not found:
                    image.add_alias(name=image_name, description=image_name)

        lxd_net_config = {
            'ipv4.address': "10.100.10.1/24",
            'ipv4.nat': 'true',
            'ipv4.dhcp': 'true'
        }

        BUILD_SWITCH = "buildnet0"
        self.mm.lxd.networks.create(BUILD_SWITCH, config=lxd_net_config)

        self.print("Creating base images...")
        for image_name in BUILD_BASE_IMAGES:
            base_data = BUILD_BASE_IMAGES[image_name]
            ok = self.lxd_build_image(image_name, base_data['template'], BUILD_SWITCH, base_data['commands'])
            if not ok:
                lxd_network = self.mm.lxd.networks.get(BUILD_SWITCH)
                lxd_network.delete()
                return

        self.print("Creating specialized images...")
        for image_name in BUILD_SPECIALIZED_IMAGES:
            base_data = BUILD_SPECIALIZED_IMAGES[image_name]
            ok = self.lxd_build_image(image_name, base_data['template'], BUILD_SWITCH, base_data['commands'])
            if not ok:
                lxd_network = self.mm.lxd.networks.get(BUILD_SWITCH)
                lxd_network.delete()
                return
            

        lxd_network = self.mm.lxd.networks.get(BUILD_SWITCH)
        lxd_network.delete()

    def get_list(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT lxd_id, ip_addr, fqdn FROM lxd_container;")

        results = dbc.fetchall()
        new_list = []
        for container in results:
            new_data = ["lxd"]
            new_data += [container[0], container[1], container[2]]
            container_name = container[2].split(".")[0]
            _, status = self.lxd_get_status(container_name)
            new_data += status[1]
            new_list.append(new_data)
        return new_list

__MODULE__ = LXDManager