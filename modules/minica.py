import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import BaseModule

CA_IMAGE_NAME = ""
CA_BASE_DIR = "{}/work/minica".format(os.getcwd())

DEFAULT_COUNTRY = "US"
DEFAULT_STATE = "NP"
DEFAULT_CITY = "Someplace"
DEFAULT_ORG = "FakerNet Org"
DEFAULT_DIV = "Servers"

INSTANCE_TEMPLATE = "minica-server-{}"

class MiniCAServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all CA servers"
        },
        "remove_server": {
            "_desc": "Delete a CA server",
            "id": "INTEGER"
        },
        "add_server": {
            "_desc": "Add a CA server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "get_server": {
            "_desc": "Get info on a CA server",
            "id": "INTEGER"
        },
        "generate_host_cert": {
            "_desc": "Generate a key and signed certificate",
            "id": "INTEGER",
            "fqdn": "TEXT"
        },
        "get_ca_cert": {
            "_desc": "Get a server's CA cert",
            "id": "INTEGER",
            "type": "TEXT"
        },
        "start_server": {
            "_desc": "Start a CA server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Stop a CA server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "minica"
    __DESC__ = "A small, web accessible CA for labs"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "minica"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            pass 
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None
            
            minica_server_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM minica_server WHERE server_id=?", (minica_server_id,))
            result = dbc.fetchone()
            if not result:
                return "MiniCA server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]
            container_name = INSTANCE_TEMPLATE.format(minica_server_id)

            self.run("stop_server", id=minica_server_id)

            # Remove the IP allocation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            dbc.execute("DELETE FROM minica_server WHERE server_id=?", (minica_server_id,))
            self.mm.db.commit()

            self.docker_stop(container_name, server_ip)

            return None, True
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            dbc.execute("SELECT server_id FROM minica_server WHERE server_fqdn=? OR server_ip=?", (fqdn,server_ip))
            if dbc.fetchone():
                return "CA server already exists of that name or IP", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="MiniCA Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Configure the DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            dbc.execute('INSERT INTO minica_server (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            minica_server_id = dbc.lastrowid

            # Create the working directory for the server
            ca_data_path = "{}/{}".format(CA_BASE_DIR, minica_server_id)

            if os.path.exists(ca_data_path):
                print("Removing old CA directory...")
                shutil.rmtree(ca_data_path)

            os.mkdir(ca_data_path)

            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(minica_server_id)

            vols = {
                ca_data_path: {"bind": "/ca/minica/certs", 'mode': 'rw'}
            }

            environment = {
                "DOMAIN": fqdn,
                "IP": server_ip
            }

            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None
            
            return self.run("start_server", id=minica_server_id)
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            ca_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM minica_server WHERE server_id=?", (ca_id,))
            result = dbc.fetchone()
            if not result:
                return "CA server does not exist", None

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
                return "CA server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM minica_server WHERE server_id=?", (ca_id,))
            result = dbc.fetchone()
            if not result:
                return "CA server does not exist", None

            server_ip = result[0]

            return self.docker_stop(container_name, server_ip)
        elif func == "get_ca_cert":
            perror, _ = self.validate_params(self.__FUNCS__['get_ca_cert'], kwargs)
            if perror is not None:
                return perror, None
            
            minica_server_id = kwargs['id']
            cert_type = kwargs['type']

            dbc.execute("SELECT server_ip FROM minica_server WHERE server_id=?", (minica_server_id,))
            result = dbc.fetchone()
            if result is None:
                return "CA server not found", None

            ca_data_path = "{}/{}".format(CA_BASE_DIR, minica_server_id)

            get_path = "https://{}/static/certs/fakernet-ca."
            if cert_type == "windows":
                get_path += "p7b"
            else:
                get_path += "crt"

            resp = requests.get(get_path.format(result[0]), verify="{}/ca.crt".format(ca_data_path))
            if resp.status_code != 200:
                return "CA cert not found", None 
            
            ca_cert = resp.text
            return None, str(ca_cert)

        elif func == "generate_host_cert":
            perror, _ = self.validate_params(self.__FUNCS__['generate_host_cert'], kwargs)
            if perror is not None:
                return perror, None

            minica_server_id = kwargs['id']
            fqdn = kwargs['fqdn']

            dbc.execute("SELECT server_ip FROM minica_server WHERE server_id=?", (minica_server_id,))
            result = dbc.fetchone()
            if result is None:
                return "CA server not found", None

            # TODO: Filter fqdn
            if ";" in fqdn or " " in fqdn or "{" in fqdn:
                return "Invalid FQDN", None

            csr_path = "/tmp/{}.csr".format(fqdn)

            new_key = crypto.PKey()
            new_key.generate_key(crypto.TYPE_RSA, 2048)

            new_key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, new_key)

            csr_req = crypto.X509Req()
            csr_req.get_subject().CN = fqdn
            csr_req.get_subject().C = DEFAULT_COUNTRY
            csr_req.get_subject().ST = DEFAULT_STATE
            csr_req.get_subject().L = DEFAULT_CITY
            csr_req.get_subject().O = DEFAULT_ORG
            csr_req.get_subject().OU = DEFAULT_DIV
            csr_req.set_pubkey(new_key)
            csr_req.sign(new_key, "sha256")

            csr_out = open(csr_path, "wb")
            csr_out.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr_req))
            csr_out.close()

            ca_data_path = "{}/{}".format(CA_BASE_DIR, minica_server_id)

            # Get the server key
            ca_key = open("{}/ca.pass".format(ca_data_path), "r").read().strip()

            files = {
                "csrfile": open(csr_path,'rb')
            }

            post_data = {
                "password": ca_key
            }
            
            resp = requests.post("https://{}".format(result[0]), files=files, data=post_data, verify="{}/ca.crt".format(ca_data_path))
            if resp.status_code != 200:
                return "Signing failed", None 
            
            signed_cert = resp.text

            return None, (new_key_pem.decode(), signed_cert)



        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        if not os.path.exists(CA_BASE_DIR):
            os.mkdir(CA_BASE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='minica_server';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE minica_server (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building MiniCA server image...")
        self.mm.docker.images.build(path="./docker-images/minica/", tag=self.__SERVER_IMAGE_NAME__, rm=True, nocache=True)

__MODULE__ = MiniCAServer