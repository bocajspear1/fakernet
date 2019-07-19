from lib.base_module import BaseModule
import lib.validate as validate

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
            perror, _ = self.validate_params(self.__FUNCS__['get_ip_mask'], kwargs)
            if perror is not None:
                return perror, None

        fqdn = kwargs['fqdn']
        ip_addr = kwargs['ip_addr']
        template = kwargs['template']

        

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='lxd_container';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE lxd_container (lxd_id INTEGER PRIMARY KEY, fqdn TEXT, net_desc TEXT, ip_addr TEXT, template TEXT);")
            self.mm.db.commit()

    def build(self):
        pass

__MODULE__ = LXDManager