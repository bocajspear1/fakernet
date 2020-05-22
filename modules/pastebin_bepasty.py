import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import DockerBaseModule

INSTANCE_TEMPLATE = "bepasty-server-{}"

class BePastyServer(DockerBaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all Bepasty servers"
        },
        "add_server": {
            "_desc": "Delete a pastebin server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "remove_server": {
            "_desc": "Remove a Pastebin server",
            "id": "INTEGER"
        },
        "start_server": {
            "_desc": "Start a pastebin server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Stop a pastebin server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "pastebin-bepasty"
    __DESC__ = "PasteBin service using bepasty"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "bepasty"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM bepasty;") 
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
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            dbc.execute("SELECT server_id FROM bepasty WHERE server_fqdn=?", (fqdn,))
            if dbc.fetchone():
                return "Bepasty server already exists of that FQDN", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="Bepasty Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Setup our DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

             # Add the server to the database
            dbc.execute('INSERT INTO bepasty (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            bepasty_id = dbc.lastrowid

            # Create the working directory for the server
            bepasty_data_path = "{}/{}".format(self.get_working_dir(), bepasty_id)

            if os.path.exists(bepasty_data_path):
                self.print("Removing old Bepasty server directory...")
                shutil.rmtree(bepasty_data_path)

            os.mkdir(bepasty_data_path)

            certs_dir = bepasty_data_path + "/certs"
            os.mkdir(certs_dir)
            conf_dir = bepasty_data_path + "/conf"
            os.mkdir(conf_dir)
            storage_dir = bepasty_data_path + "/storage"
            os.mkdir(storage_dir)

            # Setup SSL certificates
            err, _ = self.ssl_setup(fqdn, certs_dir, "bepasty")
            if err is not None:
                return err, None

            vols = {
                certs_dir: {"bind": "/etc/certs", 'mode': 'rw'},
                conf_dir: {"bind": "/opt/bepasty/conf/", 'mode': 'rw'},
                storage_dir: {"bind": "/opt/bepasty/storage", 'mode': 'rw'}
            }

            environment = {
                "DOMAIN": fqdn
            }

            container_name = INSTANCE_TEMPLATE.format(bepasty_id)

            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None

            return self.run("start_server", id=bepasty_id)
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None

            bepasty_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(bepasty_id)

            # Ignore any shutdown errors, maybe the container was stopped externally
            self.run("stop_server", id=bepasty_id)

            dbc.execute("SELECT server_ip, server_fqdn FROM bepasty WHERE server_id=?", (bepasty_id,))
            result = dbc.fetchone()
            if not result:
                return "Bepasty server does not exist", None

            server_ip = result[0]
            fqdn = result[1]

            # Deallocate our IP address
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            # Remove the container from the database
            dbc.execute("DELETE FROM bepasty WHERE server_id=?", (bepasty_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            bepasty_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM bepasty WHERE server_id=?", (bepasty_id,))
            result = dbc.fetchone()
            if not result:
                return "Bepasty server does not exist", None

            server_ip = result[0]
            
            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(bepasty_id)

            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            bepasty_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(bepasty_id)

            # Check if the server is running
            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "Bepasty server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM bepasty WHERE server_id=?", (bepasty_id,))
            result = dbc.fetchone()
            if not result:
                return "Bepasty server does not exist", None

            server_ip = result[0]

            return self.docker_stop(container_name, server_ip)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        self.check_working_dir()

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bepasty';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE bepasty (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building PasteBin Bepasty server image...")
        self.mm.docker.images.build(path="./docker-images/pastebin-bepasty/", tag=self.__SERVER_IMAGE_NAME__, rm=True)

    def get_list(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT server_id, server_ip, server_fqdn FROM bepasty;")

        results = dbc.fetchall()
        return self._list_add_data(results, INSTANCE_TEMPLATE)

    def save(self):
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_id FROM bepasty;")
        results = dbc.fetchall()

        return self._save_add_data(results, INSTANCE_TEMPLATE)

    def restore(self, restore_data):
        dbc = self.mm.db.cursor()
        
        for server_data in restore_data:
            dbc.execute("SELECT server_ip FROM bepasty WHERE server_id=?", (server_data[0],))
            results = dbc.fetchone()
            if results:
                self._restore_server(INSTANCE_TEMPLATE.format(server_data[0]), results[0], server_data[1])

__MODULE__ = BePastyServer