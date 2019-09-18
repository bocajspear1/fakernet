import os
import shutil 
import subprocess
from lib.base_module import BaseModule



class RedirectModule(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "enable_dns_redirect": {
            "_desc": "Enable redirecting all DNS to primary DNS server",
            "interface": "STRING"
        },
        "disable_dns_redirect": {
            "_desc": "Disable redirecting all DNS to primary DNS server",
            "interface": "STRING"
        }
    } 

    __SHORTNAME__  = "redirect"
    __DESC__ = "Helper for setting up redirections"
    __AUTHOR__ = "Jacob Hartman"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "enable_dns_redirect":
            perror, _ = self.validate_params(self.__FUNCS__['enable_dns_redirect'], kwargs)
            if perror is not None:
                return perror, None

            interface = kwargs['interface']

            error, server_data = self.mm['dns'].run("get_server", id=1)
            if error is not None:
                return "No base DNS server has been created", None

            try:
                subprocess.check_output(["/usr/bin/sudo", "-n", "/sbin/iptables", "-C", "-t", "nat", "-A", "PREROUTING", "-i", interface, "-p", "udp", "-m", "udp", "--dport", "53", "-j", "DNAT", "--to-destination", server_data['server_ip'] + ":53"], stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                return "Could not enable DNS redirect", None

            return None, True

        elif func == "disable_dns_redirect":
            perror, _ = self.validate_params(self.__FUNCS__['disable_dns_redirect'], kwargs)
            if perror is not None:
                return perror, None

            interface = kwargs['interface']

            error, server_data = self.mm['dns'].run("get_server", id=1)
            if error is not None:
                return "No base DNS server has been created", None

            try:
                subprocess.check_output(["/usr/bin/sudo", "-n", "/sbin/iptables", "-t", "nat", "-D", "PREROUTING", "-i", interface, "-p", "udp", "-m", "udp", "--dport", "53", "-j", "DNAT", "--to-destination", server_data['server_ip'] + ":53"], stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                return "Could not disable DNS redirect", None

            return None, True
            

        
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        # self.check_working_dir()

        # dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bepasty';")
        # if dbc.fetchone() is None:
        #     dbc.execute("CREATE TABLE bepasty (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
        #     self.mm.db.commit()
    
    def build(self):
        pass

__MODULE__ = RedirectModule