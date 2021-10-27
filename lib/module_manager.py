# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib
import os 
import json
import re
import logging
import hashlib
from threading import RLock

from lib.version import FAKERNET_VERSION

PORT = 5050
PORT_HTTPS = 5051
SAVES_DIR = "./saves"

class HistoryWriter():

    def __init__(self, path="./history.json"):
        self._outfile = open(path, "a+")

    def add_entry(self, module, func, args):
        self._outfile.write(json.dumps({
            "module": module,
            "func": func,
            "args": args
        }) + "\n")
        self._outfile.flush()

class LockModule():

    def __init__(self, module, mm):
        self._module = module
        self.mm = mm
        
    def __getattr__(self, name):
        if name == "check":
            with self.mm.lock:
                return getattr(self._module, name)
        else:
            return getattr(self._module, name)

    def run(self, func, **kwargs):
        with self.mm.lock:
            self.mm.depth += 1
            error, result = self._module.run(func, **kwargs)
            self.mm.depth -= 1
            if len(kwargs.keys()) > 0 and self.mm.depth == 0:
                self.mm.history_writer.add_entry(self._module.__SHORTNAME__, func, kwargs)
            self.mm.logger.info("Called: %s.%s, args=%s", self._module.__SHORTNAME__, func, str(kwargs))

            return error, result

class RemoteModule():
    
    def __init__(self, mm, url, requests, shortname, funcs, https_ignore=False):
        self.__SHORTNAME__ = shortname
        self.__FUNCS__ = funcs
        self._r = requests
        self._url = url
        self.mm = mm
        self._https_ignore = https_ignore

    def run(self, func, **kwargs):
        resp = self.mm.http_post(self._url + "/" + self.__SHORTNAME__ + "/run/" + func, kwargs)
        self.mm.logger.info("Remote called: %s.%s, args=%s", self.__SHORTNAME__, func, str(kwargs))
        resp_data = resp.json()
        if not resp_data['ok']:
            return resp_data['error'], None 
        else:
            return None, resp_data['result']['output']

class ModuleManager():

    def __init__(self, ip=None, db=None, https=False, https_ignore=False, user=None, password=None):

        self._user = ""
        
        if ip is None:

            import docker
            from pylxd import Client
            import sqlite3

            self._user = "LOCAL"
            self.lock = RLock()
            self.modules = {}
            if db != None:
                self.db = db
            else:
                self.db = sqlite3.connect('fakernet.db') 

            self.docker = docker.from_env()
            self.lxd = Client()
            self.ip = None
            self._https = False
            self._port = 0
            self._https_ignore = https_ignore
            self.history_writer = HistoryWriter()
            
            self.depth = 0
        else:
            import requests
            self.lock = None
            self.modules = {}
            self.db = None
            self.docker = None
            self.lxd = None
            self.ip = ip
            self._https = https
            if https:
                self._port = PORT_HTTPS
            else:
                self._port = PORT
            self._https_ignore = https_ignore
            self._r = requests
            self._user = user 
            self._password = password
            self.history_writer = None

        
        self._logger = logging.getLogger("fakernet")
        fileLog = logging.FileHandler("./logs/fakernet.log")
        formatter = logging.Formatter('%(asctime)s %(levelname)s USER=%(user)s : %(message)s')
        fileLog.setFormatter(formatter)
        self._logger.setLevel(logging.INFO)
        self._logger.handlers = []
        self._logger.addHandler(fileLog)

        self.logger = logging.LoggerAdapter(self._logger, {
            "user": self._user
        })


    def _get_url(self):
        start = "{}:{}/api/v1".format(self.ip, self._port)
        if not self._https:
            return "http://" + start
        else:
            return "https://" + start

    def http_get(self, url):
        if self._user is None:
            return self._r.get(url, verify=not self._https_ignore)
        else:
            return self._r.get(url, verify=not self._https_ignore, auth=(self._user, self._password))

    def http_post(self, url, data):
        if self._user is None:
            return self._r.post(url, verify=not self._https_ignore, data=data)
        else:
            return self._r.post(url, verify=not self._https_ignore, auth=(self._user, self._password), data=data)

    def http_put(self, url, data):
        if self._user is None:
            return self._r.put(url, verify=not self._https_ignore, data=data)
        else:
            return self._r.put(url, verify=not self._https_ignore, auth=(self._user, self._password), data=data)

    def http_delete(self, url, data):
        if self._user is None:
            return self._r.delete(url, verify=not self._https_ignore, data=data)
        else:
            return self._r.delete(url, verify=not self._https_ignore, auth=(self._user, self._password), data=data)

    def _hash_password(self, password, salt=None):
        salt_hex = salt
        if not salt_hex:
            salt_hex = os.urandom(16).hex()
        passhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt_hex.encode(), 10000)
        return passhash.hex(), salt_hex

    def run_json_command(self, json_command):
        if 'module' not in json_command:
            return "Command does not have key 'module'", None
        elif 'func' not in json_command:
            return "Command does not have key 'func'", None
        if json_command['module'] not in self.modules:
            return "Invalid module '{}'".format(json_command['module'])
        return self.modules[json_command['module']].run(json_command['func'], **json_command['args'])

    def check_user(self, username, password):
        if not self.ip:
            with self.lock:
                dbc = self.db.cursor()
                dbc.execute("SELECT username, password, salt FROM fakernet_users WHERE username=?", (username,))
                result = dbc.fetchone()
                if not result:
                    return "Login failed", None
                
                salt = result[2]
                user_hash, _ = self._hash_password(password, salt)
                if user_hash != result[1]:
                    return "Login failed", None
                else:
                    return None, True

    def list_users(self):
        if not self.ip:
            with self.lock:
                dbc = self.db.cursor()
                dbc.execute("SELECT username FROM fakernet_users;") 
                results = dbc.fetchall()
                new_list = []

                for user in results:
                    new_list.append(user[0])
                return None, new_list
        else:
            resp = self.http_get(self._get_url() + "/_users")

            resp_data = resp.json()
            if not resp_data['ok']:
                return resp_data['error'], None 
            else:
                return None, resp_data['result']['users']

    def add_user(self, username, password):
        if not self.ip:
            with self.lock:
                user_hash, salt = self._hash_password(password)

                dbc = self.db.cursor()

                dbc.execute("SELECT user_id FROM fakernet_users WHERE username=?", (username,))
                if dbc.fetchone():
                    return "A user of that username already exists", None

                dbc.execute('INSERT INTO fakernet_users (username, password, salt) VALUES (?, ?, ?)', (username, user_hash, salt))
                self.db.commit()
                return None, True
        else:
            resp = self.http_put(self._get_url() + "/_users", {
                "username": username,
                "password": password
            })

            resp_data = resp.json()
            if not resp_data['ok']:
                return resp_data['error'], None 
            else:
                return None, resp_data['result']['status']
    
    def remove_user(self, username):
        if not self.ip:
            with self.lock:
                dbc = self.db.cursor()
                dbc.execute("DELETE FROM fakernet_users WHERE username=?", (username,))
                self.db.commit()
                return None, True
        else:
            resp = self.http_delete(self._get_url() + "/_users", {
                "username": username
            })

            resp_data = resp.json()
            if not resp_data['ok']:
                return resp_data['error'], None 
            else:
                return None, resp_data['result']['status']

    def get_version(self):
        if not self.ip:
            return FAKERNET_VERSION
        else:
            try:
                resp = self.http_get(self._get_url() + "/_version")
                if resp.status_code != 200:
                    return "Got error code {} from server".format(resp.status_code)
                rmodule_data = resp.json()
                if not rmodule_data['ok']:
                    return "Got error from server: {}".format(rmodule_data['error'])
                return rmodule_data['result']['version']
                
            except self._r.exceptions.SSLError:
                return "Could not connect to {}:{} via HTTPS".format(self.ip, self._port)
            except self._r.exceptions.ConnectionError:
                return "Failed to connect to server at {}:{}".format(self.ip, self._port)

            self.logger.info("Remote ModuleManager loaded successfully")
            return None

    def load(self):
        if not self.ip:

            dbc = self.db.cursor()

            dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fakernet_users';")
            if dbc.fetchone() is None:
                dbc.execute("CREATE TABLE fakernet_users (user_id INTEGER PRIMARY KEY, username TEXT, password TEXT, salt TEXT);")
                self.db.commit()

            module_list = os.listdir("./modules")
            for module in module_list:
                if module.endswith(".py"):
                    temp = importlib.import_module("modules." + module.replace(".py", ""))
                    shortname = temp.__MODULE__.__SHORTNAME__
                    self.modules[shortname] = LockModule(temp.__MODULE__(self), self)
                    if shortname != "init":
                        # fnconsole manually calls init's check
                        self.modules[shortname].check()
            self.logger.info("Local ModuleManager loaded successfully")
            return None
        else:
            try:
                resp = self.http_get(self._get_url() + "/_modules/list")
                if resp.status_code != 200:
                    return "Got error code {} from server".format(resp.status_code)
                rmodule_data = resp.json()
                if not rmodule_data['ok']:
                    return "Got error from server: {}".format(rmodule_data['error'])
                for module_name in rmodule_data['result']:
                    self.modules[module_name] = RemoteModule(self, self._get_url(), self._r, module_name, rmodule_data['result'][module_name], self._https_ignore)
            except self._r.exceptions.SSLError:
                return "Could not connect to {}:{} via HTTPS".format(self.ip, self._port)
            except self._r.exceptions.ConnectionError:
                return "Failed to connect to server at {}:{}".format(self.ip, self._port)

            self.logger.info("Remote ModuleManager loaded successfully")
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
            resp = self.http_get(self._get_url() + "/_servers/list_all").json()
            if resp['ok']:
                return None, resp['result']['servers']
            else:
                return resp['error'], None

    def __getitem__(self, key): 
        return self.modules[key]

    def save_state(self, save_name="default"):

        if re.search(r"[^-a-zA-Z0-9_]", save_name) is not None:
            return "Invalid character in save name", None

        if not self.ip:
            all_save_data = {}

            for module_name in self.modules:
                module = self.modules[module_name]
                save_data = module.save()
                if save_data is not None:
                    all_save_data[module.__SHORTNAME__] = save_data
            
            if not os.path.exists(SAVES_DIR):
                os.mkdir(SAVES_DIR, 0o750)

            out_path = "{}/{}.json".format(SAVES_DIR, save_name)

            if os.path.exists(out_path):
                os.rename(out_path, out_path + ".last")
            
            outdata = json.dumps(all_save_data, sort_keys=True, indent=4, separators=(',', ': '))

            out_file = open(out_path, "w+")
            out_file.write(outdata)
            out_file.close()

            self.logger.info("Local save completed successfully")
            return None, True
        else:
            try:
                resp = self.http_get(self._get_url() + "/_servers/save_state/{}".format(save_name))
                if resp.status_code != 200:
                    return "Got error code {} from server".format(resp.status_code)
                rmodule_data = resp.json()
                if not rmodule_data['ok']:
                    return "Got error from server: {}".format(rmodule_data['error'])
                else:
                    self.logger.info("Remote save completed successfully")
                    return None, True
            except self._r.exceptions.SSLError:
                return "Could not connect to {}:{} via HTTPS".format(self.ip, self._port), None
            except self._r.exceptions.ConnectionError:
                return "Failed to connect to server at {}:{}".format(self.ip, self._port), None

    def restore_state(self, save_name="default"):
        if not self.ip:

            restore_path = "{}/{}.json".format(SAVES_DIR, save_name)

            if not os.path.exists(restore_path):
                return None, True

            restore_file = open(restore_path, "r")
            restore_raw = restore_file.read()
            restore_file.close()

            all_save_data = json.loads(restore_raw)

            for module_name in self.modules:
                module = self.modules[module_name]
                if module.__SHORTNAME__ in all_save_data:
                    module.restore(all_save_data[module.__SHORTNAME__])

            self.logger.info("Local restore completed successfully")
            return None, True
        else:
            try:
                resp = self.http_get(self._get_url() + "/_servers/restore_state/{}".format(save_name))
                if resp.status_code != 200:
                    return "Got error code {} from server".format(resp.status_code)
                rmodule_data = resp.json()
                if not rmodule_data['ok']:
                    return "Got error from server: {}".format(rmodule_data['error'])
                else:
                    self.logger.info("Remote restore completed successfully")
                    return None, True
            except self._r.exceptions.SSLError:
                return "Could not connect to {}:{} via HTTPS".format(self.ip, self._port)
            except self._r.exceptions.ConnectionError:
                return "Failed to connect to server at {}:{}".format(self.ip, self._port)