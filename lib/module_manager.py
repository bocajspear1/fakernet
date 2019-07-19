import sqlite3
import importlib
import os 
import docker
from pylxd import Client

class ModuleManager():

    def __init__(self):
        self.modules = {}
        self.db = sqlite3.connect('fakernet.db')
        self.docker = docker.from_env()
        self.lxd = Client()

    def load(self):
        module_list = os.listdir("./modules")
        for module in module_list:
            if module.endswith(".py"):
                temp = importlib.import_module("modules." + module.replace(".py", ""))
                shortname = temp.__MODULE__.__SHORTNAME__
                self.modules[shortname] = temp.__MODULE__(self)
                self.modules[shortname].check()

    def build_all(self):
        module_list = os.listdir("./modules")
        for module in module_list:
            if module.endswith(".py"):
                temp = importlib.import_module("modules." + module.replace(".py", ""))
                temp.__MODULE__(self).build()

    def list_modules(self):
        return self.modules.keys()

    def __getitem__(self, key):
        return self.modules[key]