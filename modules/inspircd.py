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
        "add_server": {
            "_desc": "Add a inspircd server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "remove_server": {
            "_desc": "Delete a inspircd server",
            "id": "INTEGER"
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
        if func == "list":
            dbc.execute("SELECT * FROM inspircd;") 
            results = dbc.fetchall()
            new_results = []
            for row in results:
                new_row = list(row)
                container_name = INSTANCE_TEMPLATE.format(row[0])
                _, status = self.docker_status(container_name)
                new_row.append(status[0])
                new_row.append(status[1])
                new_results.append(new_row)

            return None, {
                "rows": new_results,
                "columns": ['ID', "server_fqdn", "server_ip", 'built', 'status']
            }
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            # Extract our variables here
            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            # Check for duplicates 
            dbc.execute("SELECT server_id FROM simplemail WHERE server_fqdn=? OR server_ip=?", (fqdn, server_ip))
            if dbc.fetchone():
                return "inspircd server already exists of that FQDN or IP", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="inspircd Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Allocate our DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            # Add the server to the database
            dbc.execute('INSERT INTO inspircd (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            inspircd_id = dbc.lastrowid

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