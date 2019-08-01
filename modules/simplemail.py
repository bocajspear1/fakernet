import os
import shutil 
from string import Template

import docker
from OpenSSL import crypto
import requests

import lib.validate as validate
from lib.base_module import BaseModule

SERVER_IMAGE_NAME = "simplemail"
SERVER_BASE_DIR = "{}/work/simplemail".format(os.getcwd())


class SimpleMailServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "viewall": {
            "_desc": "View all simplemail servers"
        },
        "delete_mail_server": {
            "_desc": "Delete a CA server",
            "id": "INTEGER"
        },
        "add_mail_server": {
            "_desc": "Add a CA server",
            "fqdn": "TEXT",
            "mail_domain": "TEXT",
            "ip_addr": "IP"
        },
    } 

    __SHORTNAME__  = "simplemail"
    __DESC__ = "A simple mail server"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "viewall":
            pass 
        elif func == "delete_mail_server":
            perror, _ = self.validate_params(self.__FUNCS__['delete_mail_server'], kwargs)
            if perror is not None:
                return perror, None
            
            simplemail_id = kwargs['id']

            dbc.execute("SELECT server_fqdn, server_ip FROM simplemail WHERE server_id=?", (simplemail_id,))
            result = dbc.fetchone()
            if not result:
                return "SimpleMail server does not exist", None
            
            server_ip = result[1]
            fqdn = result[0]

            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            dbc.execute("DELETE FROM simplemail WHERE server_id=?", (simplemail_id,))
            self.mm.db.commit()

            container_name = "simplemail-server-{}".format(simplemail_id)

            self.ovs_remove_ports(container_name, switch)

            try:
                container = self.mm.docker.containers.get(container_name)
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                # return "SimpleMail server not found in Docker", None
                pass

            error, _ = self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)
            if error is not None:
                return error, None


            # Remove the host from the DNS server
            err, _ = self.mm['dns'].run("remove_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            return None, True
        elif func == "add_mail_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_mail_server'], kwargs)
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
            err, (priv_key, cert) = self.mm['minica'].run("generate_host_cert", id=1, fqdn=fqdn)
            if err is not None:
                return err, None

            out_key_path = certs_dir + "/mail.key"
            out_key = open(out_key_path, "w+")
            out_key.write(priv_key)
            out_key.close()

            out_cert_path = certs_dir + "/mail.crt"
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

            # Copy in configs
            build_base = "./docker-images/simplemail/"
            postfix_build_path = build_base + "postfix-etc/"
            dovecot_build_path = build_base + "dovecot-etc/"

            # Copy in Postfix config files
            for conf_file in os.listdir(postfix_build_path):
                full_path = postfix_build_path + conf_file
                out_path = postfix_dir + "/" + conf_file.replace("-template", "")
                print(out_path)
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

            # Start the Docker container
            container_name = "simplemail-server-{}".format(simplemail_id)

            vols = {
                postfix_dir: {"bind": "/etc/postfix", 'mode': 'rw'},
                dovecot_dir: {"bind": "/etc/dovecot", 'mode': 'rw'},
                certs_dir: {"bind": "/etc/certs", 'mode': 'rw'}
            }

            environment = {
            }

            error, server_data = self.mm['dns'].run("get_server", id=1)
            if error is not None:
                return "No base DNS server has been created", None    

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

            # Configure the DNS name
            err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
            if err is not None:
                return err, None

            return None, True

        else:
            return "Invalid function"

    
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
        self.mm.docker.images.build(path="./docker-images/simplemail/", tag=SERVER_IMAGE_NAME, rm=True, nocache=True)

__MODULE__ = SimpleMailServer