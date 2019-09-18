import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import BaseModule


SERVER_BASE_DIR = "{}/work/simplemail".format(os.getcwd())
INSTANCE_TEMPLATE = "simplemail-server-{}"

class SimpleMailServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all SimpleMail servers"
        },
        "remove_server": {
            "_desc": "Delete a SimpleMail server",
            "id": "INTEGER"
        },
        "add_server": {
            "_desc": "Add a SimpleMail server",
            "fqdn": "TEXT",
            "mail_domain": "TEXT",
            "ip_addr": "IP"
        },
        "start_server": {
            "_desc": "Start a SimpleMail server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Start a SimpleMail server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "simplemail"
    __DESC__ = "A simple mail server"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "simplemail"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list":
            dbc.execute("SELECT * FROM simplemail;") 
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
                "columns": ['ID', "server_fqdn", "server_ip", 'mail_domain', 'built', 'status']
            } 
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None
            
            simplemail_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip, mail_domain FROM simplemail WHERE server_id=?", (simplemail_id,))
            result = dbc.fetchone()
            if not result:
                return "SimpleMail server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]
            mail_domain = result[2]

            container_name = INSTANCE_TEMPLATE.format(simplemail_id)

            self.run("stop_server", id=simplemail_id)

            # Remove the IP allocation
            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None

            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            # Remove MX record from DNS server
            mx_value = fqdn
            if not mx_value.endswith("."):
                mx_value += "."
            err, _ = self.mm['dns'].run("smart_remove_record", fqdn=mail_domain, type="MX", direction="fwd", value=(10, mx_value))
            if err is not None:
                return err, None

            dbc.execute("DELETE FROM simplemail WHERE server_id=?", (simplemail_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            server_ip = kwargs['ip_addr']
            mail_domain = kwargs['mail_domain']

            dbc.execute("SELECT server_id FROM simplemail WHERE server_fqdn=? OR mail_domain=?", (fqdn, mail_domain))
            if dbc.fetchone():
                return "SimpleMail server already exists of that FQDN or mail domain", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="SimpleMail Server: {}".format(fqdn))
            if error is not None:
                return error, None

            # Allocate our DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            # Try to add our MX record
            mx_value = fqdn
            if not mx_value.endswith("."):
                mx_value += "."
            err, _ = self.mm['dns'].run("smart_add_record", fqdn=mail_domain, type="MX", direction="fwd", value=(10, mx_value), autocreate=False)
            if err is not None:
                return err, None

            # Add the server to the database
            dbc.execute('INSERT INTO simplemail (server_fqdn, server_ip, mail_domain) VALUES (?, ?, ?)', (fqdn, server_ip, mail_domain))
            self.mm.db.commit()

            simplemail_id = dbc.lastrowid

            # Create the working directory for the server
            mail_data_path = "{}/{}".format(SERVER_BASE_DIR, simplemail_id)

            if os.path.exists(mail_data_path):
                self.print("Removing old SimpleMail server directory...")
                shutil.rmtree(mail_data_path)

            os.mkdir(mail_data_path)
            postfix_dir = mail_data_path + "/postfix"
            os.mkdir(postfix_dir)
            dovecot_dir = mail_data_path + "/dovecot"
            os.mkdir(dovecot_dir)
            certs_dir = mail_data_path + "/certs"
            os.mkdir(certs_dir)

            # Get the key and cert
            err, _ = self.ssl_setup(fqdn, certs_dir, "mail")
            if err is not None:
                return err, None

            # Copy in configs
            build_base = "./docker-images/simplemail/"
            postfix_build_path = build_base + "postfix-etc/"
            dovecot_build_path = build_base + "dovecot-etc/"

            # Copy in Postfix config files
            for conf_file in os.listdir(postfix_build_path):
                full_path = postfix_build_path + conf_file
                out_path = postfix_dir + "/" + conf_file.replace("-template", "")
                
                if conf_file.endswith("-template"):
                    conf_template = open(full_path, "r").read()
                    conf_template = conf_template.replace("DOMAIN.ZONE", mail_domain)
                    conf_template = conf_template.replace("HOSTNAME.DOMAIN", fqdn)
                    open(out_path, "w+").write(conf_template)
                else:
                    shutil.copy(full_path, out_path)
                    
            # Copy in Dovecot config files
            for conf_file in os.listdir(dovecot_build_path):
                full_path = dovecot_build_path + conf_file
                out_path = dovecot_dir + "/" + conf_file.replace("-template", "")
                if conf_file.endswith("-template"):
                    conf_template = open(full_path, "r").read()
                    conf_template = conf_template.replace("DOMAIN.ZONE", mail_domain)
                    conf_template = conf_template.replace("HOSTNAME.DOMAIN", fqdn)
                    open(out_path, "w+").write(conf_template)
                else:
                    shutil.copy(full_path, out_path)

            vols = {
                postfix_dir: {"bind": "/etc/postfix", 'mode': 'rw'},
                dovecot_dir: {"bind": "/etc/dovecot", 'mode': 'rw'},
                certs_dir: {"bind": "/etc/certs", 'mode': 'rw'}
            }

            environment = {
                "DOMAIN": mail_domain
            }

            container_name = INSTANCE_TEMPLATE.format(simplemail_id)

            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None
            
            return self.run("start_server", id=simplemail_id)
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            simplemail_id = kwargs['id']

            # Get server ip from database
            dbc.execute("SELECT server_ip FROM simplemail WHERE server_id=?", (simplemail_id,))
            result = dbc.fetchone()
            if not result:
                return "SimpleMail server does not exist", None

            server_ip = result[0]

            # Start the Docker container
            container_name = INSTANCE_TEMPLATE.format(simplemail_id)

            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            simplemail_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(simplemail_id)

            # Check if the server is running
            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "SimpleMail server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM alpinewebdav WHERE server_id=?", (simplemail_id,))
            result = dbc.fetchone()
            if not result:
                return "SimpleMail server does not exist", None

            server_ip = result[0]

            return self.docker_stop(container_name, server_ip)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    
    def check(self):
        dbc = self.mm.db.cursor()

        if not os.path.exists(SERVER_BASE_DIR):
            os.mkdir(SERVER_BASE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simplemail';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE simplemail (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT, mail_domain TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building SimpleMail server image...")
        self.mm.docker.images.build(path="./docker-images/simplemail/", tag=self.__SERVER_IMAGE_NAME__, rm=True, nocache=True)

__MODULE__ = SimpleMailServer