from lib.base_module import BaseModule
import lib.validate as validate

import pylxd

PULL_SERVER = "https://images.linuxcontainers.org"
PULL_IMAGES = {
    "ubuntu_1804": "ubuntu/18.04",
    "ubuntu_1604": "ubuntu/16.04",
    "alpine_310": "alpine/3.10"
}

class LXDManager(BaseModule):

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
        }
        
    } 

    __SHORTNAME__  = "lxd"
    __DESC__ = "Module for LXD containers"
    __AUTHOR__ = "Jacob Hartman"

    def _get_lxd_status(self, container_name):
        try:
            container = self.mm.lxd.containers.get(container_name)
            return None, ("yes", container.state().status)
        except pylxd.exceptions.LXDAPIException:
            return None, ("no", "unknown")

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM lxd_container;") 
            results = dbc.fetchall()
            new_results = []
            for row in results:
                new_row = list(row)
                container_name = row[1].split(".")[0]
                _, status = self._get_lxd_status(container_name)
                new_row.append(status[0])
                new_row.append(status[1])
                new_results.append(new_row)

            return None, {
                "rows": new_results,
                "columns": ['ID', "container_fqdn", "ip_addr", 'template', 'built', 'status']
            } 
        elif func == "add_container":
            perror, _ = self.validate_params(self.__FUNCS__['add_container'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']
            template = kwargs['template']

            dbc.execute('INSERT INTO lxd_container (fqdn, ip_addr, template) VALUES (?, ?, ?, ?)', (fqdn, ip_addr, template))
            self.mm.db.commit()

            lxd_id = dbc.lastrowid

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=ip_addr, description="LXD - {}".format(fqdn))
            if error is not None:
                return error, None

            error, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=ip_addr)
            if error is not None:
                return error, None 

            fqdn_split = fqdn.split(".")

            if template not in PULL_IMAGES:
                return "Unsupported template", None

            error, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=ip_addr)
            if error:
                return error, None

            try:
                container = self.mm.lxd.containers.create({
                    'name': fqdn_split[0], 
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

            return self.run("start_container", id=lxd_id)
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

            fqdn_split = fqdn.split(".")

            self.run('stop_container', id=lxd_id)

            # Remove from database
            dbc.execute("DELETE FROM lxd_container WHERE lxd_id=?", (lxd_id,))
            self.mm.db.commit()

            try:
                container = self.mm.lxd.containers.get(fqdn_split[0])
                container.delete()
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            # Remove the IP allocation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=ip_addr)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=ip_addr)
            if err is not None:
                return err, None
            
            return None, True
        elif func == "start_container":
            perror, _ = self.validate_params(self.__FUNCS__['start_container'], kwargs)
            if perror is not None:
                return perror, None

            lxd_id = kwargs['id']
            
            # Get server ip from database
            dbc.execute("SELECT fqdn FROM lxd_container WHERE lxd_id=?", (lxd_id,))
            result = dbc.fetchone()
            if not result:
                return "Container does not exist", None

            fqdn = result[0]

            fqdn_split = fqdn.split(".")

            try:
                container = self.mm.lxd.containers.get(fqdn_split[0])
                container.start()
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            return None, True
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

            fqdn_split = fqdn.split(".")

            container_name = fqdn_split[0]
            _, status = self._get_lxd_status(container_name)
            if status[1].lower() == "stopped":
                return "Container is already stopped", None

            try:
                container = self.mm.lxd.containers.get(fqdn_split[0])
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
        for image_name in PULL_IMAGES:
            self.print("Pulling in {} - {}".format(PULL_SERVER, PULL_IMAGES[image_name]))
            image = self.mm.lxd.images.create_from_simplestreams(PULL_SERVER, PULL_IMAGES[image_name])

            found = False
            for alias in image.aliases:
                if alias['name'] == image_name:
                    found = True
            if not found:
                image.add_alias(name=image_name, description=image_name)

__MODULE__ = LXDManager