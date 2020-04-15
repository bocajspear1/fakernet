import ipaddress
import subprocess 
import time

import pylxd.exceptions

from lib.base_module import LXDBaseModule
import lib.validate as validate

INSTANCE_TEMPLATE = "nethop-{}"
PULL_SERVER = "https://images.linuxcontainers.org"
TEMPLATE_NAME = "hop_alpine_310"
PRETEMPLATE_NAME = "alpine_310"

class NetReservation(LXDBaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list_hops": {
            "_desc": "View network hops"
        },
        "add_network_hop": {
            "_desc": "Get network reservation info",
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
            "_desc": "",
            'id': "INTEGER"
        },
        "stop_hop": {
            "_desc": "",
            'id': "INTEGER"
        },
    } 

    __SHORTNAME__  = "nethop"
    __DESC__ = "Manages creating networks that are behind a next hop"
    __AUTHOR__ = "Jacob Hartman"

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

            network_obj = ipaddress.ip_network(new_network)

            # Create the hop container
            try:
                container = self.mm.lxd.containers.create({
                    'name': container_name, 
                    'source': {'type': 'image', 'alias': TEMPLATE_NAME},
                    'config': {

                    },
                    "devices": {
                        "eth0": {
                            "ipv4.address": front_ip,
                            "type": "nic",
                            "nictype": "bridged",
                            "parent": front_switch
                        },
                        "eth1": {
                            "ipv4.address": str(list(network_obj.hosts())[0]),
                            "type": "nic",
                            "nictype": "bridged",
                            "parent": new_switch
                        }
                    },
                }, wait=True)
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            error, _ =  self.run("start_hop", id=hop_id)
            if error != None:
                return error, None

            time.sleep(5)
            self.lxd_execute(container_name, "echo router rip >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, " network eth0 >> /etc/quagga/ripd.conf")
            self.lxd_execute(container_name, " network eth1 >> /etc/quagga/ripd.conf")

            return None, True

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

            # Deallocate our IP address
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=front_ip)
            # if error is not None:
            #     return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=front_ip)
            # if err is not None:
            #     return err, None

            # Delete the hop container itself
            try:
                container = self.mm.lxd.containers.get(container_name)
                container.stop()
                container.delete()
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            time.sleep(2)

            # Remove the container from the database
            dbc.execute("DELETE FROM nethop WHERE hop_id=?", (hop_id,))
            self.mm.db.commit()

            # Delete the switch if possible
            err, network_data = self.mm['netreserve'].run("get_network_by_switch", switch=switch_name)
            if err is not None:
                return err, None

            return self.mm['netreserve'].run("remove_network", id=network_data[0])

        elif func == "start_hop":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None

            hop_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(hop_id)

            try:
                container = self.mm.lxd.containers.get(container_name)
                container.start()
            except pylxd.exceptions.LXDAPIException as e:
                return str(e), None

            return None, True
        elif func == "stop_hop":
            perror, _ = self.validate_params(self.__FUNCS__['stop_container'], kwargs)
            if perror is not None:
                return perror, None

            container_name = INSTANCE_TEMPLATE.format(hop_id)

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

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='nethop';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE nethop (hop_id INTEGER PRIMARY KEY, front_ip TEXT, fqdn TEXT, switch_name TEXT);")
            self.mm.db.commit()

    def build(self):

        self.print("Pulling down LXC image for hop...")
        
        remote_name = "alpine/3.10"

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
            "echo '' >> /etc/network/interfaces",
            "echo 'auto eth1' >> /etc/network/interfaces",
            "echo 'iface eth1 inet dhcp' >> /etc/network/interfaces",
            "echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config"
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
            new_data = ["lxd"]
            new_data += [container[0], container[1], container[2]]
            container_name = container[2].split(".")[0]
            _, status = self.lxd_get_status(container_name)
            new_data += status[1]
            new_list.append(new_data)
        return new_list

__MODULE__ = NetReservation