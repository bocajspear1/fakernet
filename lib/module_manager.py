import importlib
import os 
from threading import Lock

PORT = 5050

class LockModule():

    def __init__(self, module, lock):
        self._module = module
        self._lock = lock
        
    def __getattr__(self, name):
        if name == "run" or name == "check":
            with self._lock:
                return getattr(self._module, name)
        else:
            return getattr(self._module, name)

class RemoteModule():
    
    def __init__(self, url, requests, shortname, funcs):
        self.__SHORTNAME__ = shortname
        self.__FUNCS__ = funcs
        self._r = requests
        self._url = url

    def run(self, func, **kwargs):
        resp = self._r.post(self._url + "/" + self.__SHORTNAME__ + "/run/" + func, data=kwargs)
        resp_data = resp.json()
        if not resp_data['ok']:
            return resp_data['error'], None 
        else:
            return None, resp_data['result']


class ModuleManager():

    def __init__(self, ip=None, db=None, https=False):
        if ip is None:

            import docker
            from pylxd import Client
            import sqlite3

            self._lock = Lock()
            self.modules = {}
            if db != None:
                self.db = db
            else:
                self.db = sqlite3.connect('fakernet.db') 

            self.docker = docker.from_env()
            self.lxd = Client()
            self.ip = None
            self._https = False
        else:
            import requests
            self._lock = None
            self.modules = {}
            self.db = None
            self.docker = None
            self.lxd = None
            self.ip = ip
            self._https = https
            self._r = requests

    def _get_url(self):
        start = "{}:{}/api/v1".format(self.ip, PORT)
        if not self._https:
            return "http://" + start
        else:
            return "https://" + start

    def load(self):
        if not self.ip:
            module_list = os.listdir("./modules")
            for module in module_list:
                if module.endswith(".py"):
                    temp = importlib.import_module("modules." + module.replace(".py", ""))
                    shortname = temp.__MODULE__.__SHORTNAME__
                    self.modules[shortname] = LockModule(temp.__MODULE__(self), self._lock)
                    if shortname != "init":
                        # fnconsole manually calls init's check
                        self.modules[shortname].check()
            return None
        else:
            try:
                resp = self._r.get(self._get_url() + "/_modules/list")
                if resp.status_code != 200:
                    return "Got error code {} from server".format(resp.status_code)
                rmodule_data = resp.json()
                if not rmodule_data['ok']:
                    return "Got error from server: {}".format(rmodule_data['error'])
                for module_name in rmodule_data['result']:
                    self.modules[module_name] = RemoteModule(self._get_url(), self._r, module_name, rmodule_data['result'][module_name])
            except self._r.exceptions.SSLError:
                return "Could not connect to {}:{} via HTTPS".format(self.ip, PORT)
            except self._r.exceptions.ConnectionError:
                return "Failed to connect to server at {}:{}".format(self.ip, PORT)

            return None

    def build_all(self):
        module_list = os.listdir("./modules")
        for module in module_list:
            if module.endswith(".py"):
                temp = importlib.import_module("modules." + module.replace(".py", ""))
                temp.__MODULE__(self).build()

    def list_modules(self):
        return self.modules.keys()

    def list_all_servers(self):
        if self.ip is None:
            full_list = []
            for module_name in self.modules:
                module = self.modules[module_name]
                full_list += module.get_list()
            return None, full_list
        else:
            resp = self._r.get(self._get_url() + "/_servers/list_all").json()
            if resp['ok']:
                return None, resp['result']
            else:
                return resp['error'], None

    def __getitem__(self, key): 
        return self.modules[key]