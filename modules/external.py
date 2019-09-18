import os
import shutil 
from string import Template


import lib.validate as validate
from lib.base_module import BaseModule

class External(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list_hosts": {
            "_desc": "View external hosts"
        },
        "list_networks": {
            "_desc": "View external networks"
        },
        "add_external_host": {
            "_desc": "Add an external host",
            "fqdn": "TEXT",
            "ip_addr": "IP",
            "host_desc": "TEXT"
        },
        "remove_external_host": {
            "_desc": "Remove an external host",
            "id": "INTEGER"
        },
        "add_external_network": {
            "_desc": "Add an external network (wrapper for netreserve)",
            "net_addr": "IP_NETWORK",
            "description": "TEXT"
        },
        "remove_external_network": {
            "_desc": "Remove an external network (wrapper for netreserve)",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "external"
    __DESC__ = "Helpers for external, non-Fakernet systems"
    __AUTHOR__ = "Jacob Hartman"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list_hosts":
            dbc.execute("SELECT * FROM externalhost;") 
            results = dbc.fetchall()
            return None, {
                "rows": results,
                "columns": ["ID", "FQDN", "IP ADDRESS", "Description"]
            }
        elif func == "list_networks":
            err, listing = self.mm['netreserve'].run("list")
            if err is not None:
                return err, None

            new_rows = []
            for row in listing['rows']:
                if row[3] == "":
                    new_rows.append(row[:-1])
            
            return None, {
                "rows": new_rows,
                "columns": ["ID", "Range", "Description"]
            }

        elif func == "add_external_host":
            perror, _ = self.validate_params(self.__FUNCS__['add_external_host'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']
            host_desc = kwargs['host_desc']

            dbc.execute('INSERT INTO externalhost (fqdn, ip_addr, host_desc) VALUES (?, ?, ?)', (fqdn, ip_addr, host_desc))
            self.mm.db.commit()

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=ip_addr, description="External - {}".format(fqdn))
            if error is not None:
                return error, None

            error, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=ip_addr)
            if error is not None:
                return error, None 

            return None, True
        elif func == "remove_external_host":
            perror, _ = self.validate_params(self.__FUNCS__['remove_external_host'], kwargs)
            if perror is not None:
                return perror, None

            external_id = kwargs['id']
            
            # Get server ip from database
            dbc.execute("SELECT * FROM externalhost WHERE host_id=?", (external_id,))
            result = dbc.fetchone()
            if not result:
                return "External host does not exist", None

            # Remove the IP allocation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=ip_addr)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=ip_addr)
            if err is not None:
                return err, None

            # Remove from database
            dbc.execute("DELETE FROM externalhost WHERE host_id=?", (external_id,))
            self.mm.db.commit()

            return None, True
        elif func == "add_external_network":
            perror, _ = self.validate_params(self.__FUNCS__['add_external_network'], kwargs)
            if perror is not None:
                return perror, None

            return self.mm['netreserve'].run("add_network", net_addr=kwargs['net_addr'], description="External Network", switch="")
        elif func == "remove_external_network":
            perror, _ = self.validate_params(self.__FUNCS__['add_external_network'], kwargs)
            if perror is not None:
                return perror, None

            return self.mm['netreserve'].run("remove_network", id=kwargs['id'])

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='externalhost';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE externalhost (host_id INTEGER PRIMARY KEY, fqdn TEXT, ip_addr TEXT, host_desc TEXT);")
            self.mm.db.commit()

    def build(self):
        pass

__MODULE__ = External