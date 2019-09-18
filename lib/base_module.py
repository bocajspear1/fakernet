import subprocess 
import os

import docker

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

    def build(self):
        pass

    def check_working_dir(self):
        if not os.path.exists("./work/" + self.__SHORTNAME__):
            os.mkdir("./work/" + self.__SHORTNAME__)

    def get_working_dir(self):
        return "{}/work/{}".format(os.getcwd(), self.__SHORTNAME__)

    def validate_params(self, func_def, kwargs):
        for item in func_def:
            if item != "_desc":
                if item not in kwargs:
                    return "'{}' not set".format(item), None
        
        return None, True

    def ovs_set_ip(self, container, bridge, interface, ip_addr, gateway):
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-docker", "add-port", bridge, interface, container, "--ipaddress={}".format(ip_addr), "--gateway={}".format(gateway)])
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
            return "Bepasty server not found in Docker", None
        except docker.errors.APIError:
            return "Could not remove Bepasty server in Docker", None
        
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
