import ipaddress
import subprocess 
import time

import pylxd.exceptions

from lib.base_module import LXDBaseModule
import lib.validate as validate

INSTANCE_TEMPLATE = "nethop-{}"
PULL_SERVER = "https://images.linuxcontainers.org"
TEMPLATE_NAME = "hop_alpine_313"
PRETEMPLATE_NAME = "alpine_313"

class NetReservation(LXDBaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View network hops"
        },
        "add_network_hop": {
            "_desc": "Add a network hop",
            "front_ip": "IP",
            "fqdn": "TEXT",
            "net_addr": "IP_NETWORK",
            "description": "TEXT",
            "switch": "TEXT"
        },
        "remove_network_hop": {
            "_desc": "Remove a network hop",
            'id': "INTEGER"
        },
        "start_hop": {
            "_desc": "Start a hop router between networks",
            'id': "INTEGER"
        },
        "stop_hop": {
            "_desc": "Stop a hop router between networks. Will cut off communications.",
            'id': "INTEGER"
        },
    } 

    __SHORTNAME__  = "nethop"
    __DESC__ = "Manages creating networks that are behind a next hop"
    __AUTHOR__ = "Jacob Hartman"

    def _vtysh_exec(self, commands):
        vtyshPath = subprocess.check_output(["/bin/sh", '-c', 'which vtysh']).strip().decode()
        full_command = [vtyshPath]
        for command in commands:
            full_command += ['-c', command]
        
        try:
            return subprocess.check_output(full_command).strip().decode()
        except subprocess.CalledProcessError as e:
            print(e)
            return None

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM nethop;") 
            results = dbc.fetchall()
            return None, {
                "rows": results,
                "columns": ["ID", "Range", "Description", "Switch"]
            }
        elif func == "add_network_hop":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None
            
            front_ip = kwargs['front_ip']
            fqdn = kwargs['fqdn']
            new_network = kwargs['net_addr']
            new_switch = kwargs['switch']
            description = kwargs['description']

            dbc.execute("SELECT hop_id FROM nethop WHERE fqdn=? OR front_ip=?", (fqdn,front_ip))
            if dbc.fetchone():
                return "A hop server already exists of that FQDN or IP", None

            # See if the switch for the front ip exists
            error, front_switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=front_ip)

            if error is not None:
                return error, None

            # Allocate the front the IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=front_ip, description="Hop for network {}".format(new_network))
            if error is not None:
                return error, None

            # Configure the DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=front_ip)
            if err is not None:
                return err, None
                
            # Add the hop network in netreserve
            error, _ = self.mm['netreserve'].run("add_hop_network", net_addr=new_network, description=description, switch=new_switch)
            if error is not None:
                return error, None

            # Add the hop to the database
            dbc.execute('INSERT INTO nethop (fqdn, front_ip, switch_name) VALUES (?, ?, ?)', (fqdn, front_ip, new_switch))
            self.mm.db.commit()

            # Our new hop id
            hop_id = dbc.lastrowid
            container_name = INSTANCE_TEMPLATE.format(hop_id)

            # Create the hop container
            try:
                container = self.mm.lxd.containers.create({
                    'name': container_name, 
                    'source': {'type': 'image', 'alias': TEMPLATE_NAME},
                    'config': {

                    },
                    "devices": {
                        "eth0": {
                            "type": "nic",
                            "nictype": "bridged",
                            "parent": front_switch,
                            "name": "eth0"
                        },
                        "eth1": {
                            "type": "nic",
                            "nictype": "bridged",
                            "parent": new_switch,
                            "name": "eth1"
                        }
                    },
                }, wait=True)
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            error, _ =  self.run("start_hop", id=hop_id)
            if error != None:
                return error, None

            time.sleep(10)
            self.lxd_execute(container_name, "echo '' >> /etc/quagga/zebra.conf")
            self.lxd_execute(container_name, "echo 'router rip' >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, "echo ' version 2' >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, "echo ' network eth0' >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, "echo ' network eth1' >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, "echo ' redistribute connected' >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, "service zebra restart")
            self.lxd_execute(container_name, "service ripd restart")
            self.lxd_execute(container_name, "service zebra restart")
            self.lxd_execute(container_name, "service ripd restart")
            
            nerror, is_hop = self.mm['netreserve'].run("is_hop_network_by_switch", switch=front_switch)
            if nerror is not None:
                return nerror, None

            if not is_hop:
                self.print("Not a hop, configuring local quagga...")

                self._vtysh_exec([
                    'config t',
                    'router rip',
                    'version 2',
                    'network {}'.format(front_switch),
                ])

                self._vtysh_exec([
                    'write mem'
                ])

            return None, hop_id

        elif func == "remove_network_hop":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None 

            hop_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(hop_id)

            dbc.execute("SELECT front_ip, fqdn, switch_name FROM nethop WHERE hop_id=?", (hop_id,))
            result = dbc.fetchone()
            if not result:
                return "The hop does not exist", None

            front_ip = result[0]
            fqdn = result[1]
            switch_name = result[2]

            # Stop the hop
            self.run('stop_hop', id=hop_id)

            # Deallocate our IP address
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=front_ip)

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=front_ip)

            # Delete the hop container itself
            del_err, _ = self.lxd_delete(container_name)

            time.sleep(2)

            # Remove the container from the database
            dbc.execute("DELETE FROM nethop WHERE hop_id=?", (hop_id,))
            self.mm.db.commit()

            # Delete the switch if possible
            err, network_data = self.mm['netreserve'].run("get_network_by_switch", switch=switch_name)
            if err is not None:
                return err, None

            if del_err is not None:
                return del_err, None

            return self.mm['netreserve'].run("remove_network", id=network_data['net_id'])

        elif func == "start_hop":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None

            hop_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(hop_id)

            dbc.execute("SELECT front_ip, fqdn, switch_name FROM nethop WHERE hop_id=?", (hop_id,))
            result = dbc.fetchone()
            if not result:
                return "The hop does not exist", None

            front_ip = result[0]
            switch_name = result[2]

            serror, _ = self.lxd_start(container_name, front_ip)
            if serror is not None:
                return serror, None

            # Add second switch interface
            err, network_data = self.mm['netreserve'].run("get_network_by_switch", switch=switch_name)
            if err is not None:
                return err, None

            network_obj = ipaddress.ip_network(network_data['net_address'])

            err, _ = self.lxd_execute(container_name, "ip addr add {}/{} dev eth1".format(str(list(network_obj.hosts())[0]), str(network_obj.prefixlen)))
            if err is not None:
                return err, None

            return None, True
        elif func == "stop_hop":
            perror, _ = self.validate_params(self.__FUNCS__['stop_hop'], kwargs)
            if perror is not None:
                return perror, None

            hop_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(hop_id)

            return self.lxd_stop(container_name)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='nethop';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE nethop (hop_id INTEGER PRIMARY KEY, front_ip TEXT, fqdn TEXT, switch_name TEXT);")
            self.mm.db.commit()

    def build(self):

        self.print("Pulling down LXC image for hop...")
        
        remote_name = "alpine/3.13"

        try:
            self.mm.lxd.images.get_by_alias(PRETEMPLATE_NAME)
        except pylxd.exceptions.NotFound:

            self.print("Pulling in {} - {}".format(PULL_SERVER, remote_name))
            image = self.mm.lxd.images.create_from_simplestreams(PULL_SERVER, remote_name)

            found = False
            for alias in image.aliases:
                if alias['name'] == TEMPLATE_NAME:
                    found = True
            if not found:
                image.add_alias(name=PRETEMPLATE_NAME, description=PRETEMPLATE_NAME)

        lxd_net_config = {
            'ipv4.address': "10.100.10.1/24",
            'ipv4.nat': 'true',
            'ipv4.dhcp': 'true'
        }

        BUILD_SWITCH = "buildnet0"
        self.mm.lxd.networks.create(BUILD_SWITCH, config=lxd_net_config)

        hop_commands = [
            "apk add quagga openssh-server",
            "echo '' > /etc/network/interfaces",
            "echo 'auto eth0' >> /etc/network/interfaces",
            "echo 'iface eth0 inet manual' >> /etc/network/interfaces",
            "echo '' >> /etc/network/interfaces",
            "echo 'auto eth1' >> /etc/network/interfaces",
            "echo 'iface eth1 inet manual' >> /etc/network/interfaces",
            "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config",
            "rc-update add zebra",
            "rc-update add ripd"
        ]

        ok = self.lxd_build_image(TEMPLATE_NAME, PRETEMPLATE_NAME, BUILD_SWITCH, hop_commands)
        if not ok:
            print(ok)

        lxd_network = self.mm.lxd.networks.get(BUILD_SWITCH)
        lxd_network.delete()

    def get_list(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT hop_id, front_ip, fqdn FROM nethop;")

        results = dbc.fetchall()
        new_list = []
        for container in results:
            new_data = ["nethop"]
            new_data += [container[0], container[1], container[2]]
            container_name = container[2].split(".")[0]
            _, status = self.lxd_get_status(container_name)
            new_data.append(status[1])
            new_list.append(new_data)
        return new_list

__MODULE__ = NetReservation