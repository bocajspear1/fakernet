import subprocess 

class BaseModule():
    __SHORTNAME__ = ""

    def print(self, data):
        print("[" +  self.__SHORTNAME__ + "] " + data)

    def build(self):
        pass

    def get_working_dir(self):
        return "./work/" + self.__SHORTNAME__

    def validate_params(self, func_def, kwargs):
        for item in func_def:
            if item != "_desc":
                if item not in kwargs:
                    return "'{}' not set".format(item), None
        
        return None, True

    def ovs_set_ip(self, container, bridge, interface, ip_addr, gateway):
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "add-port", bridge, interface, container, "--ipaddress={}".format(ip_addr), "--gateway={}".format(gateway)])
        return None, True

    def ovs_remove_ports(self, container, bridge):
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "del-ports", bridge, container])
        return None, True