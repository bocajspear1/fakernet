import os
import subprocess
import shutil
from string import Template, ascii_letters
import random


import lib.validate as validate
from lib.base_module import DockerBaseModule

SERVER_BASE_DIR = "{}/work/tinyproxy".format(os.getcwd())
INSTANCE_TEMPLATE = "tinyproxy-server-{}"

class tinyproxyIRC(DockerBaseModule):
    
    __FUNCS__ = {
        "list": {
            "_desc": "View all tinyproxy servers"
        },
        "add_server": {
            "_desc": "Add a tinyproxy server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "remove_server": {
            "_desc": "Delete a tinyproxy server",
            "id": "INTEGER"
        },
        "start_server": {
            "_desc": "Start a tinyproxy server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Start a tinyproxy server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "tinyproxy"
    __DESC__ = "tinyproxy HTTP Proxy"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "tinyproxy"

    def __init__(self, mm):
        self.mm = mm

    def run(self, func, **kwargs):
        dbc = self.mm.db.cursor()
        # Put list of functions here
        if func == "list":
            dbc.execute("SELECT * FROM tinyproxy;") 
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
            dbc.execute("SELECT server_id FROM tinyproxy WHERE server_fqdn=? OR server_ip=?", (fqdn, server_ip))
            if dbc.fetchone():
                return "tinyproxy server already exists of that FQDN or IP", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="tinyproxy Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Allocate our DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            # Add the server to the database
            dbc.execute('INSERT INTO tinyproxy (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            tinyproxy_id = dbc.lastrowid

            # Create the working directory for the server
            tinyproxy_working_path = "{}/{}".format(SERVER_BASE_DIR, tinyproxy_id)

            if os.path.exists(tinyproxy_working_path):
                self.print("Removing old tinyproxy server directory...")
                shutil.rmtree(tinyproxy_working_path)
            
            os.mkdir(tinyproxy_working_path)

            config_dir = tinyproxy_working_path + "/config"
            os.mkdir(config_dir)

            # Copy in config
            build_base = "./docker-images/tinyproxy/"


            # Place other needed files
            shutil.copyfile(build_base + "tinyproxy.conf", config_dir + "/tinyproxy.conf")

            # Setup the volumes
            vols = {
                config_dir: {"bind": "/etc/tinyproxy", 'mode': 'rw'}
            }

            # Our environemnt is empty this time
            environment = {
            }

            container_name = INSTANCE_TEMPLATE.format(tinyproxy_id)

            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None
            
            serror, _ = self.run("start_server", id=tinyproxy_id)
            if serror is not None:
                return serror, None

            return None, tinyproxy_id 
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None
            
            tinyproxy_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM tinyproxy WHERE server_id=?", (tinyproxy_id,))
            result = dbc.fetchone()
            if not result:
                return "tinyproxy server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]

            container_name = INSTANCE_TEMPLATE.format(tinyproxy_id)

            # Ensure the container is stopped
            self.run("stop_server", id=tinyproxy_id)

            # Remove the host from the DNS server
            self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)

            # Remove the IP allocation
            self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)

            dbc.execute("DELETE FROM tinyproxy WHERE server_id=?", (tinyproxy_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            tinyproxy_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM tinyproxy WHERE server_id=?", (tinyproxy_id,))
            result = dbc.fetchone()
            if not result:
                return "tinyproxy server does not exist", None

            server_ip = result[0]

            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(tinyproxy_id)

            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            tinyproxy_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(tinyproxy_id)

            # Check if the server is running
            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "tinyproxy server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM tinyproxy WHERE server_id=?", (tinyproxy_id,))
            result = dbc.fetchone()
            if not result:
                return "tinyproxy server does not exist", None

            server_ip = result[0]

            return self.docker_stop(container_name, server_ip)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        # This creates the module's working directory.
        if not os.path.exists(SERVER_BASE_DIR):
            os.mkdir(SERVER_BASE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tinyproxy';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE tinyproxy (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()

    def build(self):
        self.print("Building {} server image...".format(self.__SHORTNAME__))
        self.mm.docker.images.build(path="./docker-images/tinyproxy/", tag=self.__SERVER_IMAGE_NAME__, rm=True)

    def save(self):
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_id FROM tinyproxy;")
        results = dbc.fetchall()

        return self._save_add_data(results, INSTANCE_TEMPLATE)

    def restore(self, restore_data):
        dbc = self.mm.db.cursor()
        
        for server_data in restore_data:
            dbc.execute("SELECT server_ip FROM tinyproxy WHERE server_id=?", (server_data[0],))
            results = dbc.fetchone()
            if results:
                self._restore_server(INSTANCE_TEMPLATE.format(server_data[0]), results[0], server_data[1])
                
    def get_list(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT server_id, server_ip, server_fqdn FROM tinyproxy;")

        results = dbc.fetchall()
        return self._list_add_data(results, INSTANCE_TEMPLATE)

__MODULE__ = tinyproxyIRC