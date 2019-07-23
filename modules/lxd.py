from lib.base_module import BaseModule
import lib.validate as validate

import pylxd

PULL_SERVER = "https://images.linuxcontainers.org"
PULL_IMAGES = {
    "ubuntu_1804": "ubuntu/18.04",
    "ubuntu_1604": "ubuntu/16.04",
}

class LXDManager(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "viewall": {
            "_desc": "View containers"
        },
        "add_container": {
            "_desc": "Add a new container",
            'fqdn': "TEXT",
            "ip_addr": "IP_ADDR",
            "template": "TEXT",
        },
        
    } 

    __SHORTNAME__  = "lxd"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "add_container":
            perror, _ = self.validate_params(self.__FUNCS__['add_container'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']
            template = kwargs['template']

            # Allocate our IP address
            # error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=ip_addr, description="LXD - {}".format(fqdn))
            # if error is not None:
            #     return error, None

            # error, _ = self.mm['dns'].run("easy_add_host", fqdn=fqdn, ip_addr=ip_addr)
            # if error is not None:
            #     return error, None 

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

            dbc.execute('INSERT INTO lxd_container (fqdn, ip_addr, template) VALUES (?, ?, ?)', (fqdn, ip_addr, template))
            self.mm.db.commit()

            return None, True
        elif func == "delete_container":
            pass
        else:
            return "Invalid function", None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='lxd_container';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE lxd_container (lxd_id INTEGER PRIMARY KEY, fqdn TEXT, ip_addr TEXT, template TEXT);")
            self.mm.db.commit()

    def build(self):
        for image_name in PULL_IMAGES:
            print("Pulling in {} - {}".format(PULL_SERVER, PULL_IMAGES[image_name]))
            image = self.mm.lxd.images.create_from_simplestreams(PULL_SERVER, PULL_IMAGES[image_name])

            found = False
            for alias in image.aliases:
                if alias['name'] == image_name:
                    found = True
            if not found:
                image.add_alias(name=image_name, description=image_name)

__MODULE__ = LXDManager