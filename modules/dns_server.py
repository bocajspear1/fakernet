import os
import shutil 
from string import Template

import dns.reversename
import docker

import lib.easyzone as easyzone
import lib.validate as validate

from lib.base_module import BaseModule

DNS_IMAGE_NAME = "fn-dns-server"
DNS_BASE_DIR = "{}/work/dns".format(os.getcwd())

ZONE_CONFIG_TEMPLATE = """zone "$ZONE" IN {
    type master;
    file "$PATH";
};
"""

class DNSServer(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "viewall": {
            "_desc": "View all DNS servers"
        },
        "delete_server": {
            "_desc": "Delete a DNS server",
            "id": "IP"
        },
        "add_server": {
            "_desc": "Add a DNS server",
            "ip_addr": "IP",
            "description": "TEXT",
            "domain": "TEXT"
        },
        "add_zone": {
            "_desc": "Add a DNS zone",
            "id": "INTEGER",
            "zone": "TEXT",
            "direction": ['fwd', 'rev']
        },
        "add_record": {
            "_desc": "Add a record to a DNS server",
            "id": "INTEGER",
            "zone": "TEXT",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "name": "TEXT",
            "value": "TEXT"
        },
        "add_host": {
            "_desc": "Add a host to a DNS server",
            "id": "INTEGER",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "get_server": {
            "_desc": "Get info on a DNS server",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "dns"

    def _add_zone(self, dns_server_id, zone, direction):
        if direction != "fwd" and direction != "rev":
            return "Invalid zone direction", None

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)

        zone_path =  "{}/zones/{}.{}".format(dns_config_path, zone, direction)
        zone_config_path = "{}/conf/{}.conf".format(dns_config_path, zone)

        # TODO: Filter zone name

        if os.path.exists(zone_path) and os.path.exists(zone_config_path):
            return "Zone already exists", None
        

        zone_file = open("./docker-images/dns/zone-template", "r").read()
        zone_file = zone_file.replace("TEMPLATE.ZONE", zone)
        out_zone = open(zone_path, "w+")
        out_zone.write(zone_file)
        out_zone.close()

        t = Template(ZONE_CONFIG_TEMPLATE) 
        config_file = open(zone_config_path, "w+")
        config_file.write(t.substitute({'ZONE' : zone, 'PATH': "/etc/bind/zones/{}.{}".format(zone, direction)})) 
        config_file.close()

        full_zone_name = zone

        if full_zone_name[len(full_zone_name)-1] != ".":
            full_zone_name = full_zone_name + "."

        zone_file = easyzone.zone_from_file(zone, zone_path)
        zone_ns = "ns1." + full_zone_name

        # Set up the NS to point to the server correctly
        
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
        result = dbc.fetchone()
        if not result:
            return "DNS server does not exist in database", None

        zone_file.delete_name(zone_ns)
        zone_file.add_name(zone_ns)

        ns_a = zone_file.names[zone_ns].records("A", create=True)
        ns_a.add(result[0])


        zone_file.save(autoserial=True)

        main_config_contents = open(dns_config_path + "/named.conf", "r").read()
        if not "include \"/etc/bind/conf/{}.conf\";\n".format(zone) in main_config_contents:
            main_config_file = open(dns_config_path + "/named.conf", "a")
            main_config_file.write("\ninclude \"/etc/bind/conf/{}.conf\";\n".format(zone))

        return None, True

    def _add_host(self, dns_server_id, fqdn, ip_addr):

        if not validate.is_ip(ip_addr):
            return "Invalid IP address", None

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
        if not os.path.exists(dns_config_path):
            return "DNS server {} does not exist".format(dns_server_id), None

        fqdn_split = fqdn.split(".")
        hostname = fqdn_split[0]
        if fqdn_split[len(fqdn_split)-1] == "":
            del fqdn_split[len(fqdn_split)-1]
        zone = ".".join(fqdn_split[1:])

        zone_path =  "{}/zones/{}.{}".format(dns_config_path, zone, "fwd")
        if not os.path.exists(zone_path):
            return "Zone does not exist", None

        self.run("add_record", id=dns_server_id, zone=zone, direction="fwd", type="A", name=hostname+"."+zone, value=ip_addr)

        # Check for reverse
        rev_name = str(dns.reversename.from_address(str(ip_addr)))[:-1]
        
        rev_split = rev_name.split(".")
        last_num = rev_split[0]
        rev_name = ".".join(rev_split[1:])
        print(rev_name, last_num)
        
        dns_config_path = "{}/{}".format(DNS_BASE_DIR, 1)
        zone_path =  "{}/zones/{}.{}".format(dns_config_path, rev_name, "rev")
        if not os.path.exists(zone_path):
            error, _ = self.run("add_zone", id=1, direction="rev", zone=rev_name)
            if error is not None:
                return error, None

        self.run("add_record", id=1, zone=rev_name, direction="rev", type="PTR", name=str(last_num), value=hostname+"."+zone+".")


        return None, True

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "viewall":
            pass 
        elif func == "get_server":
            perror, _ = self.validate_params(self.__FUNCS__['get_server'], kwargs)
            if perror is not None:
                return perror, None
            
            dns_server_id = kwargs['id']
            dbc.execute("SELECT * FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None
            else:
                return None, {
                    "server_ip": result[1],
                    "description": result[2],
                    "domain": result[3],
                }

        elif func == "delete_server":
            perror, _ = self.validate_params(self.__FUNCS__['delete_server'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']

            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None
            print(result)
            server_ip = result[0]

            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            dbc.execute("DELETE FROM dns_server WHERE server_id=?", (dns_server_id,))
            self.mm.db.commit()

            container_name = "dns-server-{}".format(dns_server_id)

            self.ovs_remove_ports(container_name, switch)

            try:
                container = self.mm.docker.containers.get("dns-server-{}".format(dns_server_id))
                container.stop()
                container.remove()
                
            except docker.errors.NotFound:
                return "DNS server not found in Docker", None

            return None, True

        elif func == "add_server":
            perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
            if perror is not None:
                return perror, None

            domain = kwargs['domain']
            server_ip = kwargs['ip_addr']
            description = kwargs['description']

            # Check for our parent
            if domain != ".":
                pass

            # Check this domain is not already taken
            dbc.execute("SELECT server_id FROM dns_server WHERE server_domain=?", (domain,))
            if dbc.fetchone():
                return "Domain already exists", None

            # Allocate our IP address
            error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description=description)
            if error is not None:
                return error, None

            dbc.execute('INSERT INTO dns_server (server_ip, server_desc, server_domain) VALUES (?, ?, ?)', (server_ip, description, domain))
            self.mm.db.commit()

            dns_server_id = dbc.lastrowid

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)

            if os.path.exists(dns_config_path):
                print("Removing old directory...")
                shutil.rmtree(dns_config_path)

            os.mkdir(dns_config_path)
            os.mkdir(dns_config_path + "/conf")
            os.mkdir(dns_config_path + "/zones")
            shutil.copy("./docker-images/dns/config-template", dns_config_path + "/named.conf")

            open(dns_config_path + "/conf/empty.conf", "w+")

            vols = {
                dns_config_path: {"bind": "/etc/bind", 'mode': 'rw'}
            }

            container_name = "dns-server-{}".format(dns_server_id)

            self.mm.docker.containers.run(DNS_IMAGE_NAME, volumes=vols, detach=True, name=container_name, network_mode="none")

            err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
            if err:
                return err, None

            err, mask = self.mm['netreserve'].run("get_ip_mask", ip_addr=server_ip)
            if err:
                return err, None
            
            err, result = self.ovs_set_ip(container_name, switch, "{}/{}".format(server_ip, mask), "eth0")

            if err is not None:
                return err, None

            # If we are the first DNS server, then set us as the default DNS server for LXD containers
            if dns_server_id == 1:

                network = self.mm.lxd.networks.get(switch)
                network.config['raw.dnsmasq'] = 'dhcp-option=option:dns-server,{}'.format(server_ip) 
                network.save()


            return None, True
            
        elif func == "add_zone":
            perror, _ = self.validate_params(self.__FUNCS__['add_zone'], kwargs)
            if perror is not None:
                return perror, None

            return self._add_zone(kwargs['id'], kwargs['zone'], kwargs['direction'])

        elif func == "add_record":
            perror, _ = self.validate_params(self.__FUNCS__['add_record'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']
            zone = kwargs['zone']
            direction = kwargs['direction']
            record_type = kwargs['type']
            name = kwargs['name']
            value = kwargs['value']

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            zone_path =  "{}/zones/{}.{}".format(dns_config_path, zone, direction)
            

            zone = easyzone.zone_from_file(zone, zone_path)

            print("name: ", name)
            if name[len(name)-1] != "." and record_type == "A":
                name = name + "."

            zone.add_name(name)
            ns = zone.names[name].records(record_type, create=True)
            ns.add(value)
            zone.save(autoserial=True)

            try:
                container = self.mm.docker.containers.get("dns-server-{}".format(dns_server_id))
                code, output = container.exec_run("rndc reload")
                if code != 0:
                    return "'rndc reload' failed", None
            except docker.errors.NotFound:
                return "DNS server not found", None
        elif func == "add_host":
            perror, _ = self.validate_params(self.__FUNCS__['add_host'], kwargs)
            if perror is not None:
                return perror, None

            return self._add_host(kwargs['id'], kwargs['fqdn'], kwargs['ip_addr'])
        else:
            return "Invalid function '{}'".format(func), None

    def check(self):
        dbc = self.mm.db.cursor()

        if not os.path.exists("./work/dns"):
            os.mkdir("./work/dns")

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dns_server';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE dns_server (server_id INTEGER PRIMARY KEY, server_ip TEXT, server_desc TEXT, server_domain TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building DNS server image...")
        self.mm.docker.images.build(path="./docker-images/dns/", tag=DNS_IMAGE_NAME, rm=True)

__MODULE__ = DNSServer