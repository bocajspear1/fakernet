from lib.base_module import BaseModule
import docker 
import subprocess
from lib.util import clean_ovs

NETWORK_NAME = "fnexternal0"

class FakernetInit(BaseModule):

    def __init__(self, mm):
        self.mm = mm
        self.init_needed = False
        self.network_needed = False

    __PARAMS__ = {
        "verify_permissions": {
            "_desc": "Verify permissions on different components"
        }
    } 

    __SHORTNAME__  = "init"
    __DESC__ = "This module runs as the console is started and does any necessary setup and system checks"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "verify_permissions":
            errors = []

            try:
                subprocess.check_output(["/usr/bin/sudo", "-n", "/sbin/iptables", "-vL"], stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                errors.append("'sudo' for iptables not set. Add permissions to run this command using 'visudo'")

            try:
                subprocess.check_output(["/usr/bin/sudo", "-n", "/usr/bin/ovs-docker"], stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                errors.append("'sudo' for ovs-docker not set. Add permissions to run this command using 'visudo'")

            try:
                subprocess.check_output(["docker", "ps"], shell=True, stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                errors.append("Cannot access Docker. Add this user to the `docker` group and re-login")

            try:
                subprocess.check_output(["lxc", "list"], shell=True, stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                errors.append("Cannot access LXD. Add this user to the `lxd` group and re-login")

            try:
                subprocess.check_output(['vtysh -c "show version"'], shell=True, stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                errors.append("Cannot access Quagga. Add this user to the `quaggavty` group and re-login")

            try:
                subprocess.check_output(["/usr/bin/sudo", "-n", "/sbin/iptables", "-P", "FORWARD", "ACCEPT"], stderr=subprocess.DEVNULL)     
            except subprocess.CalledProcessError:
                errors.append("Could not enable ACCEPT on FORWARD table")


            if len(errors) > 0:
                return "\n".join(errors), None
            else:
                return None, True

            
    def check(self):
        
        err, netallocs = self.mm['netreserve'].run('list')
        if len(netallocs['rows']) == 0:
            self.init_needed = True
        else:
            clean_ovs()
        try:
            self.mm.docker.networks.get(NETWORK_NAME)
        except docker.errors.NotFound:
            self.network_needed = True

        
    def restore(self, restore_data):
        pass

    def save(self):
        pass
        
    

__MODULE__ = FakernetInit