# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import subprocess 
import os
import time
import re

import docker
import pylxd

class BaseModule():
    __SHORTNAME__ = ""
    __FUNCS__ = {}
    __DESC__ = ""
    __AUTHOR__ = "Not Set"
    __SERVER_IMAGE_NAME__ = "IMAGE NOT SET"

    class Holder():
        docker = docker.from_env()

    mm = Holder()
    

    def print(self, data):
        print("[" +  self.__SHORTNAME__ + "] " + data)

    def get_path(self):
        return __file__

    # Some default functions that should be overriden in modules
    def build(self):
        pass

    def get_list(self):
        return []

    def save(self):
        return None

    def restore(self, data):
        pass

    # Adds status info for get_list. Passed list should have data in format ID, ip address, description
    def _list_add_data(self, server_info, instance_template):
        new_list = []
        for server in server_info:
            new_data = [self.__SHORTNAME__]
            new_data += [server[0], server[1], server[2]]
            error, status = self.docker_status(instance_template.format(server[0]))
            if error is None:
                new_data.append(status[1])
            else:
                new_data.append("error")
            new_list.append(new_data)
        return new_list

            
    # Help setup functions
    def check_working_dir(self):
        if not os.path.exists("./work/" + self.__SHORTNAME__):
            os.mkdir("./work/" + self.__SHORTNAME__)

    def get_working_dir(self):
        return "{}/work/{}".format(os.getcwd(), self.__SHORTNAME__)

    def validate_params(self, func_def, kwargs):
        for item in func_def:
            item_type = func_def[item]
            if item == "_desc":
                continue 
            
            if item not in kwargs:
                return "'{}' not set".format(item), None

            item_val = str(kwargs[item])

            if item_type == "INTEGER":
                if re.fullmatch(r"[0-9]+", item_val) == None:
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "ADVTEXT":
                if re.fullmatch(r"[- \t,._A-Za-z0-9!@#$%^&*()_+<>?\"':|\[\]{}]+", item_val) == None and item_val.strip() != "":
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "TEXT" or item_type == "PASSWORD":
                if re.fullmatch(r"[- \t,._A-Za-z0-9:=/#@!*]+", item_val) == None and item_val.strip() != "":
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "SIMPLE_STRING":
                if re.fullmatch(r"[-A-Za-z0-9]+", item_val) == None and item_val.strip() != "":
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "IP" or item_type == "IP_ADDR":
                if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", item_val) == None:
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "IP_NETWORK":
                if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+", item_val) == None:
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "BOOLEAN":
                if item_val.lower() != "true" and item_val.lower() != "false":
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif item_type == "DECIMAL":
                if re.fullmatch(r"[0-9]+\.{0,1}[0-9]*", item_val) == None:
                    return "'{}' is not a valid '{}' for {}".format(item_val, item_type, item), None
            elif isinstance(item_type, list):
                if item_val not in item_type:
                    selection = "|".join(item_type)
                    return "'{}' is not a valid selection from {}".format(item_val, selection), None
            else:
                return "Invalid type '{}'".format(item_type), None
        
        return None, True


class DockerBaseModule(BaseModule):

    class Holder():
        docker = docker.from_env()

    mm = Holder()

    def ovs_set_ip(self, container, bridge, interface, ip_addr, gateway):
        if gateway is not None:
            subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "add-port", bridge, interface, container, "--ipaddress={}".format(ip_addr), "--gateway={}".format(gateway)])
        else:
            subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "add-port", bridge, interface, container, "--ipaddress={}".format(ip_addr)])
        return None, True

    def ovs_remove_ports(self, container, bridge):
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "del-ports", bridge, container])
        return None, True

    def docker_status(self, container):
        try:
            container = self.mm.docker.containers.get(container)
            return None, ("yes", container.status)        
        except docker.errors.NotFound:
            return None, ("no", "n/a")

    def docker_create(self, container_name, vols, environment):
        error, server_data = self.mm['dns'].run("get_server", id=1)
        if error is not None:
            return "No base DNS server has been created", None

        # Create the server in Docker
        self.mm.docker.containers.create(self.__SERVER_IMAGE_NAME__, volumes=vols, environment=environment, detach=True, name=container_name, network_mode="none", dns=[server_data['server_ip']])

        return None, True
    
    def docker_delete(self, container_name):
        # Remove the container from Docker
        try:
            container = self.mm.docker.containers.get(container_name)
            container.remove()
        except docker.errors.NotFound:
            return "Server not found in Docker", None
        except docker.errors.APIError:
            return "Could not remove server in Docker", None
        
        return None, True
    
    def docker_run(self, container_name, cmd):
        # Run command on the Docker instance
        try:
            container = self.mm.docker.containers.get(container_name)
            return container.exec_run(cmd)
        except docker.errors.NotFound:
            return "Server not found in Docker", None
        except docker.errors.APIError:
            return "Could not remove server in Docker", None
        
        return None, True

    def docker_start(self, container_name, server_ip):
        # Get the server
        try:
            container = self.mm.docker.containers.get(container_name)
            container.start()
        except docker.errors.NotFound:
            return "Server not found in Docker", None
        except 	docker.errors.APIError:
            return "Could not start server in Docker", None

        if server_ip is not None:
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

    def docker_stop(self, container_name, server_ip):
        if server_ip is not None:
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
            return "Server not found in Docker", None

        return None, True

    def ssl_setup(self, fqdn, certs_dir, keyname, server_id=1):
        # Get the key and cert
        err, (priv_key, cert) = self.mm['minica'].run("generate_host_cert", id=server_id, fqdn=fqdn)
        if err is not None:
            return err, None

        out_key_path = certs_dir + "/{}.key".format(keyname)
        out_key = open(out_key_path, "w+")
        out_key.write(priv_key)
        out_key.close()

        out_cert_path = certs_dir + "/{}.crt".format(keyname)
        out_cert = open(out_cert_path, "w+")
        out_cert.write(cert)
        out_cert.close()

        # Write the CA cert
        err, ca_cert_file = self.mm['minica'].run("get_ca_cert", id=server_id, type="linux")
        if err is not None:
            return err, None

        ca_cert_path = certs_dir + "/fakernet-ca.crt"
        ca_cert = open(ca_cert_path, "w+")
        ca_cert.write(ca_cert_file)
        ca_cert.close()

        return None, True

    def _restore_server(self, container_name, server_ip, new_status):

        error, status = self.docker_status(container_name)
        if error is not None:
            return error, None
        if new_status == "running" and status[1] == "running":
            print("Server {} already running".format(container_name))
        elif new_status == "running":
            print("Restoring {}".format(container_name))
            error, _ = self.docker_start(container_name, server_ip)
            if error is not None:
                print("Got error: {}".format(error))
        elif new_status == "stopped" and status[1] == "running":
            print("Stopping {}".format(container_name))
            error, _ = self.docker_stop(container_name, server_ip)
            if error is not None:
                print("Got error: {}".format(error))
    
        return None, True

    def _save_add_data(self, server_ids, instance_template):
        save_data = []
        for server in server_ids:
            server_id = server[0]
            error, status = self.docker_status(instance_template.format(server_id))
            
            if status[0] == 'yes':
                if error is None and status[1] == "running":
                    save_data.append([server_id, "running"])
                else:
                    save_data.append([server_id, "stopped"])
        return save_data


class LXDBaseModule(BaseModule):
    class Holder():
        
        lxd = None
        def __init__(self):
            from pylxd import Client
            self.lxd = Client()

    mm = Holder()

    def lxd_execute(self, container_name, command):
        try:
            container = self.mm.lxd.containers.get(container_name)
            status, stdout, stderr = container.execute(["/bin/sh", "-c", command])
            if status != 0:
                return stdout + "\n---\n" + stderr, None
            else:
                return None, stdout
        except pylxd.exceptions.LXDAPIException as e:
            return str(e), None

    def lxd_start(self, container_name, server_ip):
        try:
            container = self.mm.lxd.containers.get(container_name)
            container.start()
            time.sleep(10)
        except pylxd.exceptions.LXDAPIException as e:
            return str(e), None

        # Configure networking
        err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
        if err:
            return err, None

        err, network = self.mm['netreserve'].run("get_ip_network", ip_addr=server_ip)
        if err:
            return err, None
        
        mask = network.prefixlen
        gateway = str(list(network.hosts())[0])

        err, _ = self.lxd_execute(container_name, "ip addr add {}/{} dev eth0".format(server_ip, mask))
        if err is not None:
            return "Setting IP: " + err, None

        err, _ = self.lxd_execute(container_name, "ip route add default via {}".format(gateway))
        if err is not None:
            return "Adding route: " + err, None

        error, server_data = self.mm['dns'].run("get_server", id=1)
        if error is None:
            err, _ = self.lxd_execute(container_name, "echo 'nameserver {}' > /etc/resolv.conf".format(server_data['server_ip']))
            if err is not None:
                return "Setting DNS nameserver: " + err, None
        else:
            return "Could not find nameserver in FakerNet:" + error, None

        return None, True

    def lxd_stop(self, container_name):
        _, status = self.lxd_get_status(container_name)
        if status[1].lower() == "stopped":
            return "Container is already stopped", None

        try:
            container = self.mm.lxd.containers.get(container_name)
            container.stop()
        except pylxd.exceptions.LXDAPIException as e:
            return str(e), None

        return None, True

    def lxd_delete(self, container_name):
        try:
            container = self.mm.lxd.containers.get(container_name)
            container.delete()
        except pylxd.exceptions.LXDAPIException as e:
            return str(e), None
        return None, True

    def lxd_build_image(self, image_name, template, switch, commands):
        try:
            self.mm.lxd.images.get_by_alias(image_name)
        except pylxd.exceptions.NotFound:
            container_name = (image_name + "_temp").replace("_", "-")

            self.print("Building {}".format(image_name))
            temp_container = self.mm.lxd.containers.create({
                'name': container_name, 
                'source': {
                    'type': 'image', 
                    'alias': template,
                    'mode': 'pull'
                },
                'config': {

                },
                "devices": {
                    "eth0": {
                        "type": "nic",
                        "nictype": "bridged",
                        "parent": switch
                    }
                },
            }, wait=True)

            temp_container.start(wait=True)
            status, stdout, stderr = temp_container.execute(["/bin/sh", "-c", "sleep 5"])
            for command in commands:
                self.print("Ran: " + command)
                status, stdout, stderr = temp_container.execute(["/bin/sh", "-c", command])
                if status != 0:
                    self.print("Command failed!")
                    self.print(stdout)
                    self.print(stderr)
                    temp_container.stop(wait=True)
                    temp_container.delete(wait=True)

                    return False

            temp_container.stop(wait=True)
            temp_container.type = 'container'

            image = temp_container.publish(wait=True)
            image.add_alias(name=image_name, description=image_name)
            temp_container.delete(wait=True)
        return True

    def lxd_get_status(self, container_name):
        try:
            container = self.mm.lxd.containers.get(container_name)
            status = container.state().status
            return None, ("yes", status.lower())
        except pylxd.exceptions.LXDAPIException as e:
            return e, ("no", "unknown")

    def _restore_server(self, container_name, server_ip, new_status):

        error, status = self.lxd_get_status(container_name)
        if error is not None:
            return error, None
        if new_status == "running" and status[1] == "running":
            print("Server {} already running".format(container_name))
        elif new_status == "running":
            print("Restoring {}".format(container_name))
            error, _ = self.lxd_start(container_name, server_ip)
            if error is not None:
                print("Got error: {}".format(error))
        elif new_status == "stopped" and status[1] == "running":
            print("Stopping {}".format(container_name))
            error, _ = self.lxd_stop(container_name)
            if error is not None:
                print("Got error: {}".format(error))
    
        return None, True

    def _save_add_data(self, server_ids):
        save_data = []
        for server in server_ids:
            server_id = server[0]
            container_name = server[1]
            error, status = self.lxd_get_status(container_name)
            
            if status[0] == 'yes':
                if error is None and status[1] == "running":
                    save_data.append([server_id, "running"])
                else:
                    save_data.append([server_id, "stopped"])
        return save_data
