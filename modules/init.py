from lib.base_module import BaseModule
import docker 

NETWORK_NAME = "fnexternal0"

class FakernetInit(BaseModule):

    def __init__(self, mm):
        self.mm = mm
        self.init_needed = False
        self.network_needed = False

    __PARAMS__ = {

    } 

    __SHORTNAME__  = "init"
    __DESC__ = "This module runs as the console is started and does any necessary setup and system checks"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "start-network":
            if not "host_ip" in kwargs:
                return "'host_ip' not set", None
            if not "host_net" in kwargs:
                return "'host_net' not set", None
            if not "host_gateway" in kwargs:
                return "'host_gateway' not set", None

            ipam_pool = docker.types.IPAMPool(
                subnet=kwargs['host_net'],
                # gateway=kwargs['host_gateway']
            )
            ipam_config = docker.types.IPAMConfig(
                pool_configs=[ipam_pool]
            )    

            
    def check(self):
        
        err, netallocs = self.mm['netreserve'].run('list')
        if len(netallocs['rows']) == 0:
            self.init_needed = True
        try:
            self.mm.docker.networks.get(NETWORK_NAME)
        except docker.errors.NotFound:
            self.network_needed = True
        
    

__MODULE__ = FakernetInit