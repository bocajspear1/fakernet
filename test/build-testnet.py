import sys
import os 

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

from lib.module_manager import ModuleManager
import lib.validate

manager = ModuleManager()
manager.load()

manager['netreserve'].check()
error, result = manager['netreserve'].run("add_network", description="test_network", net_addr="172.16.3.0/24", switch="testnet0")
print(error, result)

manager['dns'].check()
error, result = manager['dns'].run("add_server", ip_addr="172.16.3.2", description="test_dns", domain="test")
print(error, result)
error, result = manager['dns'].run("add_zone", id=1, direction="fwd", zone="test")
print(error, result)

manager['minica'].check()
error, result = manager['minica'].run("add_ca", fqdn="ca.test", ip_addr="172.16.3.3")
print(error, result)