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
        "get_network_by_switch": {
            "_desc": "Get the switch for a network",
            "switch": "TEXT"
        },
        "get_ip_switch": {
            "_desc": "Get the switch for a network",
            "ip_addr": "IP"
        },
        "get_ip_network": {
            "_desc": "Get the mask for a network",
            "ip_addr": "IP"
        },
        "is_hop_network_by_switch": {
            "_desc": "Check if a network is a hop network (behind a hop router) by switch name",
            "switch": "TEXT"
        }
    } 

    __SHORTNAME__  = "netreserve"
    __DESC__ = "Manages network reservations and setup"
    __AUTHOR__ = "Jacob Hartman"

    def _set_switch_ip(self, switch, ip_addr):

        try:
            status_data = subprocess.check_output(["/usr/bin/sudo", "/sbin/ip", "addr", "show", "dev", switch]).decode()
            if "UP" in status_data and ip_addr in status_data:
                return None, True
        except subprocess.CalledProcessError:
            return "Failed to get switch status", None
        
        try:
            subprocess.check_output(["/usr/bin/sudo", "/sbin/ip", 'link', 'set', switch, 'up'])
            subprocess.check_output(["/usr/bin/sudo", "/sbin/ip", 'addr', 'add', ip_addr, 'dev', switch])
        except subprocess.CalledProcessError:
            return "Failed to set switch ip", None
              

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM networks;") 
            results = dbc.fetchall()
            return None, {
                "rows": results,
                "columns": ["ID", "Range", "Description", "Switch", 'Is Hop Network']
            }
        elif func == "remove_network":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None
            
            net_id = kwargs['id']

            dbc.execute("SELECT * FROM networks WHERE net_id=?", (net_id,))
            result = dbc.fetchone()
            if result is None:
                return "Network does not exist", None
            
            dbc.execute("DELETE FROM networks WHERE net_id=?", (net_id,))
            self.mm.db.commit()
            
            switch = result[3]
            if switch != "":
                # Ensure the switch exists
                try:
                    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "br-exists", switch])
                except subprocess.CalledProcessError:
                    return "Switch {} does not exit".format(switch), None

                try:
                    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "del-br", switch])
                except subprocess.CalledProcessError:
                    return "Could not delete switch {}".format(switch), None


            return None, True

        elif func == "add_hop_network":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None
            
            new_network = kwargs['net_addr']
            switch = kwargs['switch']
            description = "HOP NETWORK: " + kwargs['description']

            dbc.execute("SELECT * FROM networks WHERE switch_name=?", (switch,))
            if dbc.fetchone():
                return "Switch of that name already exists", None

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
                dbc.execute('INSERT INTO networks (net_address, net_desc, switch_name, is_hop_network) VALUES (?, ?, ?, ?)', (new_network, description, switch, 1))
                self.mm.db.commit()

                if switch == "":
                    return "Switch name is blank", None
                
                # Ensure the switch exists
                try:
                    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "br-exists", switch])
                except:
                    try:
                        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "add-br", switch])
                    except:
                        return "Failed to create OVS bridge", None
                
                try:
                    subprocess.check_output(["/usr/bin/sudo", "/sbin/ip", 'link', 'set', switch, 'up'])
                except subprocess.CalledProcessError:
                    return "Failed to set hop switch to up", None

                return None, True
            else:
                "Invalid network", None

        elif func == "add_network":
            perror, _ = self.validate_params(self.__FUNCS__['add_network'], kwargs)
            if perror is not None:
                return perror, None

            new_network = kwargs['net_addr']
            switch = kwargs['switch']
            description = kwargs['description']

            if switch != "":
                dbc.execute("SELECT * FROM networks WHERE switch_name=?", (switch,))
                if dbc.fetchone():
                    return "Switch of that name already exists", None

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
                
                dbc.execute('INSERT INTO networks (net_address, net_desc, switch_name, is_hop_network) VALUES (?, ?, ?, ?)', (new_network, description, switch, 0))
                self.mm.db.commit()

                network_id = dbc.lastrowid

                # A blank switch means we don't want one
                if switch != "":
                    # Ensure the switch exists
                    try:
                        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "br-exists", switch])
                    except subprocess.CalledProcessError:
                        try:
                            subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "add-br", switch])
                        except subprocess.CalledProcessError:
                            return "Failed to create OVS bridge", None
                        self._set_switch_ip(switch, str(list(new_network_obj.hosts())[0]) + "/" + str(new_network_obj.prefixlen))

                return None, network_id
            else:
                return "Invalid network address", None
        elif func == "get_network_switch":
            pass
        elif func == "get_network_by_switch":
            perror, _ = self.validate_params(self.__FUNCS__[func], kwargs)
            if perror is not None:
                return perror, None

            switch = kwargs['switch']

            dbc.execute("SELECT net_id, net_address, net_desc, switch_name, is_hop_network FROM networks WHERE switch_name=?", (switch,))
            result = dbc.fetchone()
            if not result:
                return "Switch does not exist", None

            return None, {
                "net_id": result[0],
                "net_address": result[1],
                "net_desc": result[2],
                "is_hop": result[3] == 1
            }

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
        elif func == "is_hop_network_by_switch":
            perror, _ = self.validate_params(self.__FUNCS__['is_hop_network_by_switch'], kwargs)
            if perror is not None:
                return perror, None

            switch = kwargs['switch']
            dbc.execute("SELECT is_hop_network FROM networks WHERE switch_name=?", (switch,))
            result = dbc.fetchone()
            if not result:
                return "Switch does not exist", None

            return None, result[0] == 1

        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='networks';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE networks (net_id INTEGER PRIMARY KEY, net_address TEXT, net_desc TEXT, switch_name TEXT, is_hop_network INTEGER);")
            self.mm.db.commit()
        
        dbc.execute("SELECT net_address, switch_name, is_hop_network FROM networks")
        results = dbc.fetchall()
        for network in results:
            net_addr = network[0]
            switch = network[1]
            is_hop = network[2]

            if is_hop != 1 and switch != "":
                new_network_obj = ipaddress.ip_network(net_addr)
                self._set_switch_ip(switch, str(list(new_network_obj.hosts())[0]) + "/" + str(new_network_obj.prefixlen))
               

    def build(self):
        pass

__MODULE__ = NetReservation