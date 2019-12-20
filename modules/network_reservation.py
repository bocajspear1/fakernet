import ipaddress
import subprocess 

import pylxd.exceptions

from lib.base_module import BaseModule
import lib.validate as validate

class NetReservation(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View network allocations"
        },
        "get": {
            "_desc": "Get network reservation info",
            "ip_id": "INT"
        },
        "add_hop_network": {
            "_desc": "Add network allocation",
            "net_addr": "IP_NETWORK",
            "description": "TEXT",
            "switch": "TEXT"
        },
        "add_network": {
            "_desc": "Add network allocation",
            "net_addr": "IP_NETWORK",
            "description": "TEXT",
            "switch": "TEXT"
        },
        "remove_network": {
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
        "get_ip_network": {
            "_desc": "Get the mask for a network",
            "ip_addr": "IP"
        }
    } 

    __SHORTNAME__  = "netreserve"
    __DESC__ = "Manages network reservations and setup"
    __AUTHOR__ = "Jacob Hartman"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM networks;") 
            results = dbc.fetchall()
            return None, {
                "rows": results,
                "columns": ["ID", "Range", "Description", "Switch"]
            }
        elif func == "remove_network":
            perror, _ = self.validate_params(self.__FUNCS__['remove_network'], kwargs)
            if perror is not None:
                return perror, None
            
            net_id = kwargs['id']

            dbc.execute("SELECT * FROM networks WHERE net_id=?", (net_id,))
            result = dbc.fetchone()
            if result is None:
                return "Network does not exist", None
            
            dbc.execute("DELETE FROM networks WHERE net_id=?", (net_id,))
            self.mm.db.commit()
            
            switch_name = result[3]
            try:
                lxd_network = self.mm.lxd.networks.get(switch_name)
                lxd_network.delete()
            except pylxd.exceptions.NotFound: 
                return "Switch not found for LXD", None

            return None, True

        elif func == "add_hop_network":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None
            
            new_network = kwargs['net_addr']
            switch = kwargs['switch']
            description = "HOP NETWORK: " + kwargs['description']

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
                dbc.execute('INSERT INTO networks (net_address, net_desc, switch_name) VALUES (?, ?, ?)', (new_network, description, switch))
                self.mm.db.commit()

                if switch == "":
                    return "Switch name is blank", None
                
                # Ensure the switch exists
                try:
                    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "br-exists", switch])
                except:
                    
                    network_hosts = list(new_network_obj.hosts())

                    lxd_net_config = {
                        'ipv4.address': str(network_hosts[len(network_hosts)-1]) + "/" + str(new_network_obj.prefixlen),
                        'ipv4.nat': 'false',
                        'bridge.driver': 'openvswitch',
                        'ipv4.dhcp.ranges': str(network_hosts[0]) + "-" + str(network_hosts[len(network_hosts)-2]),
                        'ipv4.dhcp.gateway': str(network_hosts[0])
                    }

                    # If we have a base dns server, set the networks DNS server
                    error, server_data = self.mm['dns'].run("get_server", id=1)
                    if error is None:
                        lxd_net_config['raw.dnsmasq'] = 'dhcp-option=option:dns-server,{}'.format(server_data['server_ip'])

                    self.mm.lxd.networks.create(switch, config=lxd_net_config)

                return None, True

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

                # A blank switch means we don't want one
                if switch != "":
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
            
            return "Could not find network", None
        elif func == "get_ip_network":
            perror, _ = self.validate_params(self.__FUNCS__['get_ip_network'], kwargs)
            if perror is not None:
                return perror, None

            ip = kwargs['ip_addr']
            

            dbc.execute("SELECT * FROM networks")
            results = dbc.fetchall()
            for network in results:
                if validate.is_ip_in_network(ip, network[1]):
                    return None, ipaddress.ip_network(network[1])
            
            return None, True
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='networks';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE networks (net_id INTEGER PRIMARY KEY, net_address TEXT, net_desc TEXT, switch_name TEXT);")
            self.mm.db.commit()

    def build(self):
        pass

__MODULE__ = NetReservation