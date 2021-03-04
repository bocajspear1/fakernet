import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import DockerBaseModule

pwndrop_IMAGE_NAME = ""
pwndrop_BASE_DIR = "{}/work/pwndrop".format(os.getcwd())

DEFAULT_COUNTRY = "US"
DEFAULT_STATE = "NP"
DEFAULT_CITY = "Someplace"
DEFAULT_ORG = "FakerNet Org"
DEFAULT_DIV = "Servers"

INSTANCE_TEMPLATE = "pwndrop-server-{}"

class PwndropServer(DockerBaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all pwndrop servers"
        },
        "remove_server": {
            "_desc": "Delete a pwndrop server",
            "id": "INTEGER"
        },
        "add_server": {
            "_desc": "Add a pwndrop server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "start_server": {
            "_desc": "Start a pwndrop server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Stop a pwndrop server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "pwndrop"
    __DESC__ = "pwndrop: https://github.com/kgretzky/pwndrop"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "pwndrop"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM pwndrop_server;") 
            results = dbc.fetchall()
            new_results = []
            for row in results:
                new_row = list(row)
                
                _, status = self.docker_status(INSTANCE_TEMPLATE.format(row[0]))
                new_row.append(status[0])
                new_row.append(status[1])
                new_results.append(new_row)

            return None, {
                "rows": new_results,
                "columns": ['ID', "server_fqdn", "server_ip", 'built', 'status']
            }
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None
            
            pwndrop_server_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM pwndrop_server WHERE server_id=?", (pwndrop_server_id,))
            result = dbc.fetchone()
            if not result:
                return "pwndrop server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]
            container_name = INSTANCE_TEMPLATE.format(pwndrop_server_id)

            # Ignore any shutdown errors, maybe the container was stopped externally
            self.run("stop_server", id=pwndrop_server_id)

            # Remove the IP allocation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)

            dbc.execute("DELETE FROM pwndrop_server WHERE server_id=?", (pwndrop_server_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            dbc.execute("SELECT server_id FROM pwndrop_server WHERE server_fqdn=? OR server_ip=?", (fqdn,server_ip))
            if dbc.fetchone():
                return "pwndrop server already exists of that name or IP", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="pwndrop Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Configure the DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            dbc.execute('INSERT INTO pwndrop_server (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            pwndrop_server_id = dbc.lastrowid

            # Create the working directory for the server
            base_path = "{}/{}".format(pwndrop_BASE_DIR, pwndrop_server_id)
            data_path = "{}/{}".format(base_path, "data")
            admin_path = "{}/{}".format(base_path, "admin")

            if os.path.exists(base_path):
                self.print("Removing old pwndrop directory...")
                shutil.rmtree(base_path)

            os.mkdir(base_path)
            os.mkdir(data_path)
            os.mkdir(admin_path)

            err, _ = self.ssl_setup(fqdn, data_path, "pwndrop")
            if err is not None:
                return err, None

            shutil.move(data_path + "/pwndrop.crt", data_path + "/public.crt")
            shutil.move(data_path + "/pwndrop.key", data_path + "/private.key")

            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(pwndrop_server_id)

            vols = {
                data_path: {"bind": "/pwndrop/build/data", 'mode': 'rw'},
                admin_path: {"bind": "/pwndrop/build/admin", 'mode': 'rw'}
            }

            environment = {
            }

            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None
            
            err, _ = self.run("start_server", id=pwndrop_server_id)
            if err is not None:
                return err, None
            
            return None, pwndrop_server_id
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            ca_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM pwndrop_server WHERE server_id=?", (ca_id,))
            result = dbc.fetchone()
            if not result:
                return "pwndrop server does not exist", None

            server_ip = result[0]
            
            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(ca_id)

            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            ca_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(ca_id)

            # Check if the server is running
            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "pwndrop server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM pwndrop_server WHERE server_id=?", (ca_id,))
            result = dbc.fetchone()
            if not result:
                return "pwndrop server does not exist", None

            server_ip = result[0]

            return self.docker_stop(container_name, server_ip)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        if not os.path.exists(pwndrop_BASE_DIR):
            os.mkdir(pwndrop_BASE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pwndrop_server';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE pwndrop_server (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building pwndrop server image...")
        self.mm.docker.images.build(path="./docker-images/pwndrop/", tag=self.__SERVER_IMAGE_NAME__, rm=True)

    def get_list(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT server_id, server_ip, server_fqdn FROM pwndrop_server;")

        results = dbc.fetchall()
        return self._list_add_data(results, INSTANCE_TEMPLATE)

    def save(self):
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_id FROM pwndrop_server;")
        results = dbc.fetchall()

        return self._save_add_data(results, INSTANCE_TEMPLATE)

    def restore(self, restore_data):
        dbc = self.mm.db.cursor()
        
        for server_data in restore_data:
            dbc.execute("SELECT server_ip FROM pwndrop_server WHERE server_id=?", (server_data[0],))
            results = dbc.fetchone()
            if results:
                self._restore_server(INSTANCE_TEMPLATE.format(server_data[0]), results[0], server_data[1])

__MODULE__ = PwndropServer