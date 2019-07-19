import ipaddress
import subprocess 

from lib.base_module import BaseModule
import lib.validate as validate

class NetReservation(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "viewall": {
            "_desc": "View network allocations"
        },
        "get": {
            "_desc": "Get network reservation info",
            "ip_id": "INT"
        },
        "add_network": {
            "_desc": "Add network allocation",
            "net_addr": "IP_NETWORK",
            "description": "TEXT",
            "switch": "TEXT"
        },
        "delete": {
            "_desc": "Delete a network allocation",
            "id": "INTEGER"
        },
        "get_network_switch": {
            "_desc": "Get the switch for a network",
            "net_addr": "IP_NETWORK"
        },
        "get_ip_switch": {
            "_desc": "Get the switch for a network",
            "ip_addr": "IP"
        },
        "get_ip_mask": {
            "_desc": "Get the mask for a network",
            "ip_addr": "IP"
        }
    } 

    __SHORTNAME__  = "netreserve"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "viewall":
            dbc.execute("SELECT * FROM networks;") 
            results = dbc.fetchall()
            return None, results
        elif func == "add_network":
            perror, _ = self.validate_params(self.__FUNCS__['add_network'], kwargs)
            if perror is not None:
                return perror, None

            new_network = kwargs['net_addr']

            if validate.is_ipnetwork(new_network):
                # Check if the network already exists
                dbc.execute("SELECT * FROM networks;") 
                results = dbc.fetchall()

                new_network_obj = ipaddress.ip_network(new_network)

                for network in results:
                    network_obj = ipaddress.ip_network(network[1])
                    if new_network_obj.overlaps(network_obj):
                        return "{} network is already part of network {}".format(new_network, str(new_network_obj)), None

                # Insert our new network
                switch = kwargs['switch']
                dbc.execute('INSERT INTO networks (net_address, net_desc, switch_name) VALUES (?, ?, ?)', (new_network, kwargs['description'], switch))
                self.mm.db.commit()

                # Ensure the switch exists
                try:
                    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "br-exists", switch])
                except:
                    
                    lxd_net_config = {
                        'ipv4.address': str(list(new_network_obj.hosts())[0]) + "/" + str(new_network_obj.prefixlen),
                        'ipv4.nat': 'false',
                        'bridge.driver': 'openvswitch'
                    }

                    # If we have a base dns server, set the networks DNS server
                    error, server_data = self.mm['dns'].run("get_server", id=1)
                    if error is None:
                        lxd_net_config['raw.dnsmasq'] = 'dhcp-option=option:dns-server,{}'.format(server_data['server_ip'])

                    self.mm.lxd.networks.create(switch, config=lxd_net_config)

                    

                return None, True
            else:
                return "Invalid network address", None
        elif func == "get_network_switch":
            pass
        elif func == "get_ip_switch":
            perror, _ = self.validate_params(self.__FUNCS__['get_ip_switch'], kwargs)
            if perror is not None:
                return perror, None

            ip = kwargs['ip_addr']
            

            dbc.execute("SELECT * FROM networks")
            results = dbc.fetchall()
            for network in results:
                if validate.is_ip_in_network(ip, network[1]):
                    return None, network[3]
            print(results)
            
            return "Could not find network", None
        elif func == "get_ip_mask":
            perror, _ = self.validate_params(self.__FUNCS__['get_ip_mask'], kwargs)
            if perror is not None:
                return perror, None

            ip = kwargs['ip_addr']
            

            dbc.execute("SELECT * FROM networks")
            results = dbc.fetchall()
            for network in results:
                if validate.is_ip_in_network(ip, network[1]):
                    return None, ipaddress.ip_network(network[1]).prefixlen
            print(results)
            
            return None, True
        else:
            return "Invalid function", None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='networks';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE networks (net_id INTEGER PRIMARY KEY, net_address TEXT, net_desc TEXT, switch_name TEXT);")
            self.mm.db.commit()

    def build(self):
        pass

__MODULE__ = NetReservation