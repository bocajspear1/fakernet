import os
import shutil 
from string import Template

import docker

import lib.validate as validate

from lib.base_module import BaseModule

CA_IMAGE_NAME = "minica"
CA_BASE_DIR = "{}/work/minica".format(os.getcwd())


class MiniCAServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "viewall": {
            "_desc": "View all CA servers"
        },
        "delete_ca": {
            "_desc": "Delete a CA server",
            "id": "INTEGER"
        },
        "add_ca": {
            "_desc": "Add a CA server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "get_server": {
            "_desc": "Get info on a CA server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "minica"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "viewall":
            pass 
        elif func == "delete_ca":
            perror, _ = self.validate_params(self.__FUNCS__['delete_ca'], kwargs)
            if perror is not None:
                return perror, None
            
            minica_server_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM minica_server WHERE server_id=?", (minica_server_id,))
            result = dbc.fetchone()
            if not result:
                return "MiniCA server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]

            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            dbc.execute("DELETE FROM minica_server WHERE server_id=?", (minica_server_id,))
            self.mm.db.commit()

            container_name = "minica-server-{}".format(minica_server_id)

            self.ovs_remove_ports(container_name, switch)

            try:
                container = self.mm.docker.containers.get(container_name)
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                return "MiniCA server not found in Docker", None

            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None


            # Remove the host from the DNS server
             # Configure the DNS name
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            return None, True

        elif func == "add_ca":
            perror, _ = self.validate_params(self.__FUNCS__['add_ca'], kwargs)
            if perror is not None:
                return perror, None

            print(kwargs)
            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            dbc.execute("SELECT server_id FROM minica_server WHERE server_fqdn=? OR server_ip=?", (fqdn,server_ip))
            if dbc.fetchone():
                return "CA server already exists of that name or IP", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="MiniCA Server: {}".format(fqdn))
            if error is not None:
                return error, None

            dbc.execute('INSERT INTO minica_server (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            minica_server_id = dbc.lastrowid

            # Create the workign directory for the server
            ca_data_path = "{}/{}".format(CA_BASE_DIR, minica_server_id)

            if os.path.exists(ca_data_path):
                print("Removing old CA directory...")
                shutil.rmtree(ca_data_path)

            os.mkdir(ca_data_path)

            # Start the Docker container
            container_name = "minica-server-{}".format(minica_server_id)

            vols = {
                ca_data_path: {"bind": "/ca/minica/certs", 'mode': 'rw'}
            }

            environment = {
                "DOMAIN": fqdn
            }

            self.mm.docker.containers.run(CA_IMAGE_NAME, volumes=vols, detach=True, name=container_name, network_mode="none", )

            # Configure networking
            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            err, mask = self.mm['netreserve'].run("get_ip_mask", ip_addr=server_ip)
            if err:
                return err, None
            
            err, _ = self.ovs_set_ip(container_name, switch, "{}/{}".format(server_ip, mask), "eth0")
            if err is not None:
                return err, None

            # Configure the DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            return None, True

    
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
        self.mm.docker.images.build(path="./docker-images/minica/", tag=CA_IMAGE_NAME, rm=True, nocache=True)

__MODULE__ = MiniCAServer