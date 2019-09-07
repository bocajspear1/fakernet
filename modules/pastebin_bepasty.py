import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import BaseModule

SERVER_IMAGE_NAME = "bepasty"

class BePastyServer(BaseModule):

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
            "_desc": "Start a pastebin server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "pastebin-bepasty"
    __DESC__ = "PasteBin service using bepasty"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "viewall":
            pass
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            dbc.execute("SELECT server_id FROM bepasty WHERE server_fqdn=?", (fqdn,))
            if dbc.fetchone():
                return "Bepasty server already exists of that FQDN or mail domain", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="Bepasty Server: {}".format(fqdn))
            if error is not None:
                return error, None

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

             # Get the key and cert
            err, (priv_key, cert) = self.mm['minica'].run("generate_host_cert", id=1, fqdn=fqdn)
            if err is not None:
                return err, None

            out_key_path = certs_dir + "/bepasty.key"
            out_key = open(out_key_path, "w+")
            out_key.write(priv_key)
            out_key.close()

            out_cert_path = certs_dir + "/bepasty.crt"
            out_cert = open(out_cert_path, "w+")
            out_cert.write(cert)
            out_cert.close()

            # Write the CA cert
            err, ca_cert_file = self.mm['minica'].run("get_ca_cert", id=1, type="linux")
            if err is not None:
                return err, None

            ca_cert_path = certs_dir + "/fakernet-ca.crt"
            ca_cert = open(ca_cert_path, "w+")
            ca_cert.write(ca_cert_file)
            ca_cert.close()

            err, _ = self.run("start_server", id=bepasty_id)
            if err is not None:
                return err, None

            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None

            bepasty_id = kwargs['id']
            container_name = "bepasty-server-{}".format(bepasty_id)

            # Ignore any shutdown errors, maybe the container was stopped externally
            error, result = self.run("stop_server", id=bepasty_id)
            if error is not None:
                self.print(error)

            dbc.execute("SELECT server_ip FROM bepasty WHERE server_id=?", (bepasty_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            server_ip = result[0]

            # Remove the container from the database
            dbc.execute("DELETE FROM bepasty WHERE server_id=?", (bepasty_id,))
            self.mm.db.commit()

            # Deallocate our IP address
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None

            # Remove the container from Docker
            try:
                container = self.mm.docker.containers.get(container_name)
                container.remove()
            except docker.errors.NotFound:
                return "Bepasty server not found in Docker", None
            except docker.errors.APIError:
                return "Could not remove Bepasty server in Docker", None

            return None, True

        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            bepasty_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip, server_fqdn FROM bepasty WHERE server_id=?", (bepasty_id,))
            result = dbc.fetchone()
            if not result:
                return "Bepasty does not exist", None

            server_ip = result[0]
            fqdn = result[1]
            
            # Start the Docker container
            container_name = "bepasty-server-{}".format(bepasty_id)

            bepasty_data_path = "{}/{}".format(self.get_working_dir(), bepasty_id)
            certs_dir = bepasty_data_path + "/certs"

            vols = {
                certs_dir: {"bind": "/etc/certs", 'mode': 'rw'}
            }

            environment = {
                "DOMAIN": fqdn
            }

            # Get the DNS server
            error, server_data = self.mm['dns'].run("get_server", id=1)
            if error is not None:
                return "No base DNS server has been created", None    

            # Start the Docker container with all our options
            self.mm.docker.containers.run(SERVER_IMAGE_NAME, volumes=vols, environment=environment, detach=True, name=container_name, network_mode="none", dns=[server_data['server_ip']])

            # Configure networking
            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            err, network = self.mm['netreserve'].run("get_ip_network", ip_addr=server_ip)
            if err:
                return err, None
            
            mask = network.prefixlen
            gateway = str(list(network.hosts())[0])

            err, _ = self.ovs_set_ip(container_name, switch, "eth0", "{}/{}".format(server_ip, mask), gateway)
            if err is not None:
                return err, None

            return None, True
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            bepasty_id = kwargs['id']
            container_name = "bepasty-server-{}".format(bepasty_id)

            # Check if the server is running
            _, status = self.get_docker_status(container_name)
            if status is not None and status[1] != "running":
                return "Bepasty server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM bepasty WHERE server_id=?", (bepasty_id,))
            result = dbc.fetchone()
            if not result:
                return "Bepasty server does not exist", None

            server_ip = result[0]

            # Remove port from switch
            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            self.ovs_remove_ports(container_name, switch)

            # Stop container in Docker
            try:
                container = self.mm.docker.containers.get(container_name)
                container.stop()
            except docker.errors.NotFound:
                return "Bepasty server not found in Docker", None

            return None, True

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
        self.mm.docker.images.build(path="./docker-images/pastebin-bepasty/", tag=SERVER_IMAGE_NAME, rm=True, nocache=True)

__MODULE__ = BePastyServer