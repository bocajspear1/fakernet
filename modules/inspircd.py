import os
import subprocess

import lib.validate as validate
from lib.base_module import BaseModule

SERVER_BASE_DIR = "{}/work/inspircd".format(os.getcwd())
INSTANCE_TEMPLATE = "inspircd-server-{}"

class InspircdIRC(BaseModule):
    
    __FUNCS__ = {
        "list": {
            "_desc": "View all inspircd servers"
        },
        "remove_server": {
            "_desc": "Delete a inspircd server",
            "id": "INTEGER"
        },
        "add_server": {
            "_desc": "Add a inspircd server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "start_server": {
            "_desc": "Start a inspircd server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Start a inspircd server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "inspircd"
    __DESC__ = "inspircd IRC server"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "inspircd"

    def __init__(self, mm):
        self.mm = mm

    def run(self, func, **kwargs):
        dbc = self.mm.db.cursor()
        # Put list of functions here
        if func == "":
            pass
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        # This creates the module's working directory.
        if not os.path.exists(SERVER_BASE_DIR):
            os.mkdir(SERVER_BASE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inspircd';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE inspircd (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()

    def build(self):
        self.print("Building {} server image...".format(self.__SHORTNAME__))
        self.mm.docker.images.build(path="./docker-images/inspircd/", tag=self.__SERVER_IMAGE_NAME__, rm=True)

    def save(self):
        return None, None

    def restore(self, restore_data):
        pass

    def get_list(self):
        return None, []

__MODULE__ = InspircdIRC