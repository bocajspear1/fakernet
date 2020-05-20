import os
import subprocess
import shutil
from string import Template, ascii_letters
import random


import lib.validate as validate
from lib.base_module import DockerBaseModule

SERVER_BASE_DIR = "{}/work/inspircd".format(os.getcwd())
INSTANCE_TEMPLATE = "inspircd-server-{}"

class InspircdIRC(DockerBaseModule):
    
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
            dbc.execute("SELECT server_id FROM inspircd WHERE server_fqdn=? OR server_ip=?", (fqdn, server_ip))
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

            # Create the working directory for the server
            inspircd_working_path = "{}/{}".format(SERVER_BASE_DIR, inspircd_id)

            if os.path.exists(inspircd_working_path):
                self.print("Removing old inspircd server directory...")
                shutil.rmtree(inspircd_working_path)
            
            os.mkdir(inspircd_working_path)

            config_dir = inspircd_working_path + "/config"
            os.mkdir(config_dir)

            # Copy in configs
            build_base = "./docker-images/inspircd/"

            # Generate the necessary passwords
            start_stop_pass = ''.join(random.sample(ascii_letters, 10))
            root_pass = ''.join(random.sample(ascii_letters, 10))

            # For DNS lookups, get the main DNS server by calling dns.get_server, which returns server info
            dns_server = ""
            error, server_data = self.mm['dns'].run("get_server", id=1)
            if error is None:
                dns_server = server_data['server_ip']    

            # Fill in and place the configuration file
            conf_template = open(build_base + "inspircd.conf", "r").read()
            tmplt = Template(conf_template)
            output = tmplt.substitute({"DOMAIN": fqdn, "ROOT_PASS": root_pass, "START_STOP_PASS": start_stop_pass, "DNS_SERVER": dns_server})
            out_file = open(config_dir + "/inspircd.conf", "w+")
            out_file.write(output)
            out_file.close()

            # Place other needed files
            shutil.copyfile(build_base + "inspircd.motd", config_dir + "/inspircd.motd")
            shutil.copyfile(build_base + "inspircd.rules", config_dir + "/inspircd.rules")

            # Setup the volumes
            vols = {
                config_dir: {"bind": "/etc/inspircd", 'mode': 'rw'},
            }

            # Our environemnt is empty this time
            environment = {
            }

            container_name = INSTANCE_TEMPLATE.format(inspircd_id)

            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None
            
            serror, _ = self.run("start_server", id=inspircd_id)
            if serror is not None:
                return serror, None

            return None, inspircd_id 
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None
            
            inspircd_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM inspircd WHERE server_id=?", (inspircd_id,))
            result = dbc.fetchone()
            if not result:
                return "inspircd server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]

            container_name = INSTANCE_TEMPLATE.format(inspircd_id)

            # Ensure the container is stopped
            self.run("stop_server", id=inspircd_id)

            # Remove the host from the DNS server
            self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)

            # Remove the IP allocation
            self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)

            dbc.execute("DELETE FROM inspircd WHERE server_id=?", (inspircd_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            inspircd_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM inspircd WHERE server_id=?", (inspircd_id,))
            result = dbc.fetchone()
            if not result:
                return "inspircd server does not exist", None

            server_ip = result[0]

            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(inspircd_id)

            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            inspircd_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(inspircd_id)

            # Check if the server is running
            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "inspircd server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM inspircd WHERE server_id=?", (inspircd_id,))
            result = dbc.fetchone()
            if not result:
                return "inspircd server does not exist", None

            server_ip = result[0]

            return self.docker_stop(container_name, server_ip)
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
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_id FROM inspircd;")
        results = dbc.fetchall()

        return self._save_add_data(results, INSTANCE_TEMPLATE)

    def restore(self, restore_data):
        dbc = self.mm.db.cursor()
        
        for server_data in restore_data:
            dbc.execute("SELECT server_ip FROM inspircd WHERE server_id=?", (server_data[0],))
            results = dbc.fetchone()
            if results:
                self._restore_server(INSTANCE_TEMPLATE.format(server_data[0]), results[0], server_data[1])
                
    def get_list(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT server_id, server_ip, server_fqdn FROM inspircd;")

        results = dbc.fetchall()
        return self._list_add_data(results, INSTANCE_TEMPLATE)

__MODULE__ = InspircdIRC