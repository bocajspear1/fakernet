import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import BaseModule

SERVER_IMAGE_NAME = "mattermost"
SERVER_BASE_DIR = "{}/work/mattermost".format(os.getcwd())

class MattermostServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all Mattermost servers"
        },
        "remove_server": {
            "_desc": "Delete a Mattermost server",
            "id": "INTEGER"
        },
        "add_server": {
            "_desc": "Add a Mattermost server",
            "fqdn": "TEXT",
            "ip_addr": "IP"
        },
        "start_server": {
            "_desc": "Start a Mattermost server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Stop a Mattermost server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__ = "mattermost"
    __DESC__ = "Mattermost server, similar to Slack"

    def run(self, func, **kwargs):
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM mattermost;") 
            results = dbc.fetchall()
            new_results = []
            for row in results:
                new_row = list(row)
                
                _, status = self.get_docker_status(row[0])
                new_row.append(status[0])
                new_row.append(status[1])
                
                new_results.append(new_row)

            return None, {
                "rows": new_results,
                "columns": ['ID', "server_ip", 'description', 'domain', 'built', 'status']
            } 
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None
            
            mattermost_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM mattermost WHERE server_id=?", (mattermost_id,))
            result = dbc.fetchone()
            if not result:
                return "Mattermost server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]
            container_name = "mattermost-server-{}".format(mattermost_id)

            # Try to stop the server first, ignore errors as the container may have crashed or been killed externally
            self.run("stop_server", id=mattermost_id)

            dbc.execute("DELETE FROM mattermost WHERE server_id=?", (mattermost_id,))
            self.mm.db.commit()

            # Get and remove container in Docker
            try:
                container = self.mm.docker.containers.get(container_name)
                container.remove()
            except docker.errors.NotFound:
                # return "Mattermost server not found in Docker", None
                pass

            # Remove the IP reservation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            return None, True
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']

            # Check a server of this fqdn doesn't already exist
            dbc.execute("SELECT server_id FROM mattermost WHERE server_fqdn=?", (fqdn,))
            if dbc.fetchone():
                return "A Mattermost server already exists of that FQDN or mail domain", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="Mattermost Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Configure the DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            # Add the server to the database
            dbc.execute('INSERT INTO mattermost (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
            self.mm.db.commit()

            # Our new Mattermost server id
            mattermost_id = dbc.lastrowid
            container_name = "mattermost-server-{}".format(mattermost_id)

            # Create the working directory for the server
            mattermost_data_path = "{}/{}".format(SERVER_BASE_DIR, mattermost_id)

            if os.path.exists(mattermost_data_path):
                self.print("Removing old Mattermost server directory...")
                shutil.rmtree(mattermost_data_path)

            os.mkdir(mattermost_data_path)
            certs_dir = mattermost_data_path + "/certs"
            os.mkdir(certs_dir)

            # Get the key and cert
            err, (priv_key, cert) = self.mm['minica'].run("generate_host_cert", id=1, fqdn=fqdn)
            if err is not None:
                return err, None

            out_key_path = certs_dir + "/mattermost.key"
            out_key = open(out_key_path, "w+")
            out_key.write(priv_key)
            out_key.close()

            out_cert_path = certs_dir + "/mattermost.crt"
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

            vols = {
                certs_dir: {"bind": "/etc/certs", 'mode': 'rw'}
            }

            environment = {
                "DOMAIN": fqdn
            }

            error, server_data = self.mm['dns'].run("get_server", id=1)
            if error is not None:
                return "No base DNS server has been created", None    

            self.mm.docker.containers.create(SERVER_IMAGE_NAME, volumes=vols, environment=environment, detach=True, name=container_name, network_mode="none", dns=[server_data['server_ip']])

            return self.run("start_server", id=mattermost_id)

        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            mattermost_server_id = kwargs['id']

            # Ensure server exists
            dbc.execute("SELECT server_ip FROM mattermost WHERE server_id=?", (mattermost_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None
            
            container_name = "mattermost-server-{}".format(mattermost_server_id)
            server_ip = result[0]

            # Get the server and start the Docker image
            try:
                container = self.mm.docker.containers.get(container_name)
                container.start()
            except docker.errors.NotFound:
                return "DNS server not found in Docker", None
            except 	docker.errors.APIError:
                return "Could not start DNS server in Docker", None

            # Get the switch for the network the IP is in
            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            # Get the network for the IP, and default to using the first IP as the default gateway
            err, network = self.mm['netreserve'].run("get_ip_network", ip_addr=server_ip)
            if err:
                return err, None

            mask = network.prefixlen
            gateway = str(list(network.hosts())[0])

            # Ensure no existing interface remains
            self.ovs_remove_ports(container_name, switch)
            
            # Configure eth0 interface
            err, result = self.ovs_set_ip(container_name, switch, "eth0", "{}/{}".format(server_ip, mask), gateway)
            if err is not None:
                return err, None
            

            return None, True
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None
            
            mattermost_id = kwargs['id']

            # Get container data from the database
            dbc.execute("SELECT server_fqdn, server_ip FROM mattermost WHERE server_id=?", (mattermost_id,))
            result = dbc.fetchone()
            if not result:
                return "Mattermost server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]
            container_name = "mattermost-server-{}".format(mattermost_id)

            # Remove the port from the image, it needs to be set each time
            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            self.ovs_remove_ports(container_name, switch)

            # Get and stop the container
            try:
                container = self.mm.docker.containers.get(container_name)
                container.stop()
            except docker.errors.NotFound:
                return "Mattermost server not found in Docker", None
            except docker.errors.APIError:
                return "Mattermost server could not be stopped in Docker", None

            return None, True
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        if not os.path.exists(SERVER_BASE_DIR):
            os.mkdir(SERVER_BASE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mattermost';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE mattermost (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building Mattermost server image...")
        _, logs = self.mm.docker.images.build(path="./docker-images/mattermost/", tag=SERVER_IMAGE_NAME, rm=True)
        print(logs)

__MODULE__ = MattermostServer