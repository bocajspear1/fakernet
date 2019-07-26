import sys
import os 

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

from lib.module_manager import ModuleManager
import lib.validate

manager = ModuleManager()
manager.load()

manager['minica'].check()
error, result = manager['minica'].run("delete_ca", id=1)
print(error, result)

manager['dns'].check()
error, result = manager['dns'].run("delete_server", id=1)
print(error, result)