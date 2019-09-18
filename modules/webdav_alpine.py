import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import BaseModule

INSTANCE_TEMPLATE = "alpinewebdav-server-{}"

class AlpineWebDAVServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all WebDAV servers"
        },
        "add_server": {
            "_desc": "Delete a WebDAV server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "remove_server": {
            "_desc": "Remove a WebDAV server",
            "id": "INTEGER"
        },
        "start_server": {
            "_desc": "Start a WebDAV server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Start a WebDAV server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "webdavalpine"
    __DESC__ = "An Alpine Linux-based WebDAV Apache Server"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "alpinewebdav"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM alpinewebdav;") 
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

            dbc.execute("SELECT server_id FROM alpinewebdav WHERE server_fqdn=?", (fqdn,))
            if dbc.fetchone():
                return "WebDAV server already exists of that FQDN", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="WebDAV Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Allocate our DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

             # Add the server to the database
            dbc.execute('INSERT INTO alpinewebdav (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            alpinewebdav_id = dbc.lastrowid

            # Create the working directory for the server
            alpinewebdav_data_path = "{}/{}".format(self.get_working_dir(), alpinewebdav_id)

            if os.path.exists(alpinewebdav_data_path):
                self.print("Removing old WebDAV server directory...")
                shutil.rmtree(alpinewebdav_data_path)

            os.mkdir(alpinewebdav_data_path)

            certs_dir = alpinewebdav_data_path + "/certs"
            os.mkdir(certs_dir)
            data_dir = alpinewebdav_data_path + "/webdav"
            os.mkdir(data_dir)

            # Setup SSL certificates
            err, _ = self.ssl_setup(fqdn, certs_dir, "alpinewebdav")
            if err is not None:
                return err, None

            container_name = INSTANCE_TEMPLATE.format(alpinewebdav_id)

            vols = {
                certs_dir: {"bind": "/etc/certs", 'mode': 'rw'},
                data_dir: {"bind": "/etc/webdav", 'mode': 'rw'},
            }

            environment = {
                "DOMAIN": fqdn
            }

            # Create the Docker container
            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None

            return self.run("start_server", id=alpinewebdav_id)
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None

            alpinewebdav_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(alpinewebdav_id)

            dbc.execute("SELECT server_ip, server_fqdn FROM alpinewebdav WHERE server_id=?", (alpinewebdav_id,))
            result = dbc.fetchone()
            if not result:
                return "WebDAV server does not exist", None

            # Ignore any shutdown errors, maybe the container was stopped externally
            self.run("stop_server", id=alpinewebdav_id)

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
            dbc.execute("DELETE FROM alpinewebdav WHERE server_id=?", (alpinewebdav_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            alpinewebdav_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM alpinewebdav WHERE server_id=?", (alpinewebdav_id,))
            result = dbc.fetchone()
            if not result:
                return "WebDAV does not exist", None

            server_ip = result[0]
            container_name = INSTANCE_TEMPLATE.format(alpinewebdav_id)
            
            # Start the Docker container
            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            alpinewebdav_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(alpinewebdav_id)

            # Check if the server is running
            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "WebDAV server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM alpinewebdav WHERE server_id=?", (alpinewebdav_id,))
            result = dbc.fetchone()
            if not result:
                return "WebDAV server does not exist", None

            server_ip = result[0]

            # Stop the container
            return self.docker_stop(container_name, server_ip)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        self.check_working_dir()

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alpinewebdav';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE alpinewebdav (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building Alpine WebDAV server image...")
        self.mm.docker.images.build(path="./docker-images/webdav_alpine/", tag=self.__SERVER_IMAGE_NAME__, rm=True)

__MODULE__ = AlpineWebDAVServer