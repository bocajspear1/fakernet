import os
import shutil 
from string import Template

import dns.reversename
import docker

import lib.easyzone as easyzone
import lib.validate as validate

from lib.base_module import DockerBaseModule

DNS_BASE_DIR = "{}/work/dns".format(os.getcwd())

ZONE_CONFIG_TEMPLATE = """zone "$ZONE" IN {
    type master;
    file "$PATH";
};
"""

INSTANCE_TEMPLATE = "dns-server-{}"

class DNSServer(DockerBaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View all DNS servers"
        },
        "remove_server": {
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
        "smart_add_record": {
            "_desc": "Add a record to a DNS server, detecting server and zone",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "fqdn": "TEXT",
            "value": "TEXT",
            "autocreate": "BOOLEAN"
        },
        "smart_remove_record": {
            "_desc": "Add a record to a DNS server, detecting server and zone",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "fqdn": "TEXT",
            "value": "TEXT"
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
        "remove_record": {
            "_desc": "Remove a record from a DNS server",
            "id": "INTEGER",
            "zone": "TEXT",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "name": "TEXT",
            "value": "TEXT"
        },
        "add_host": {
            "_desc": "Add a host to a DNS server",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "remove_host": {
            "_desc": "Remove a host to a DNS server",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "start_server": {
            "_desc": "Start a DNS server",
            "id": "INTEGER"
        },
        "stop_server": {
            "_desc": "Stop a DNS server",
            "id": "INTEGER"
        },
        "get_server": {
            "_desc": "Get info on a DNS server",
            "id": "INTEGER"
        },
        "list_forwarders": {
            "_desc": "View forwarders for DNS server",
            "id": "INTEGER"
        },
        "add_forwarder": {
            "_desc": "Add forwarder to DNS server",
            "id": "INTEGER",
            "ip_addr": "IP_ADDR"
        },
        "remove_forwarder": {
            "_desc": "Remove forwarder from DNS server",
            "id": "INTEGER",
            "ip_addr": "IP_ADDR"
        }
    } 

    __SHORTNAME__  = "dns"
    __DESC__ = "Creates and manages BIND DNS servers"
    __AUTHOR__ = "Jacob Hartman"
    __SERVER_IMAGE_NAME__ = "fn-dns-server"

    def _get_dns_server(self, fqdn):
        dbc = self.mm.db.cursor()
        # Get our server id by looking through the domains
        fqdn_split = fqdn.split(".")
        parent_domain = ".".join(fqdn_split[1:])
        dbc.execute("SELECT * FROM dns_server WHERE server_domain=?",(parent_domain,))
        result = dbc.fetchone()
        if result is None:
            return None
        else:
            return result[0]

    def _split_fqdn(self, fqdn):
        fqdn_split = fqdn.split(".")
        hostname = fqdn_split[0]
        if fqdn_split[len(fqdn_split)-1] == "":
            del fqdn_split[len(fqdn_split)-1]
        zone = ".".join(fqdn_split[1:])
        return hostname, zone

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

    def _add_host(self, fqdn, ip_addr):

        if not validate.is_ip(ip_addr):
            return "Invalid IP address", None

        # Get our server id by looking through the domains
        dns_server_id = self._get_dns_server(fqdn)
        if dns_server_id is None:
            return "Could not find parent domain for {}".format(fqdn), None 

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
        if not os.path.exists(dns_config_path):
            return "DNS server {} does not exist".format(dns_server_id), None

        hostname, zone = self._split_fqdn(fqdn)

        zone_path =  "{}/zones/{}.{}".format(dns_config_path, zone, "fwd")
        if not os.path.exists(zone_path):
            return "Zone does not exist", None

        error, _ = self.run("add_record", id=dns_server_id, zone=zone, direction="fwd", type="A", name=hostname+"."+zone, value=ip_addr)
        if error is not None:
            return error, None

        # Check for reverse
        rev_name = str(dns.reversename.from_address(str(ip_addr)))[:-1]
        
        last_num, rev_name = self._split_fqdn(rev_name)

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, 1)
        zone_path =  "{}/zones/{}.{}".format(dns_config_path, rev_name, "rev")
        if not os.path.exists(zone_path):
            error, _ = self.run("add_zone", id=1, direction="rev", zone=rev_name)
            if error is not None:
                return error, None

        error, _ = self.run("add_record", id=1, zone=rev_name, direction="rev", type="PTR", name=str(last_num), value=hostname+"."+zone+".")
        if error is not None:
            return error, None

        return None, True

    def _remove_host(self, fqdn, ip_addr):
        
        if not validate.is_ip(ip_addr):
            return "Invalid IP address", None

        # Get our server id by looking through the domains
        dns_server_id = self._get_dns_server(fqdn)
        if dns_server_id is None:
            return "Could not find parent domain for {}".format(fqdn), None 

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
        if not os.path.exists(dns_config_path):
            return "DNS server {} does not exist".format(dns_server_id), None

        hostname, zone = self._split_fqdn(fqdn)

        zone_path =  "{}/zones/{}.{}".format(dns_config_path, zone, "fwd")
        if not os.path.exists(zone_path):
            return "Zone does not exist", None

        error, _ = self.run("remove_record", id=dns_server_id, zone=zone, direction="fwd", type="A", name=hostname+"."+zone, value=ip_addr)
        if error is not None:
            return error, None

        # Check for reverse
        rev_name_full = str(dns.reversename.from_address(str(ip_addr)))[:-1]
        
        last_num, rev_name = self._split_fqdn(rev_name_full)

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, 1)
        zone_path =  "{}/zones/{}.{}".format(dns_config_path, rev_name, "rev")
        if not os.path.exists(zone_path):
            return "Reverse zone does not exist", None

        error, _ = self.run("remove_record", id=1, zone=rev_name, direction="rev", type="PTR", name=rev_name_full + ".", value=hostname+"."+zone+".")
        if error is not None:
            return error, None

        return None, True

    def _parse_forwarders_file(self, path):
        forwarder_file = open(path, "r").read()
            
        forwarder_lines = forwarder_file.split("\n")

        forwarders = []
        for line in forwarder_lines:
            line = line.strip()
            if not ("}" in line or "{" in line) and line != "":
                forwarders.append(line.replace(";", ""))

        return forwarders

    def _write_forwarders_file(self, path, forwarders):
        output = "forwarders {\n"
        for forwarder in forwarders:
            output += "    {};\n".format(forwarder)
        output += "};\n"
        forwarder_file = open(path, "w")
        forwarder_file.write(output)
        forwarder_file.close()

    def _rndc_reload(self, dns_server_id):
        try:
            container = self.mm.docker.containers.get(INSTANCE_TEMPLATE.format(dns_server_id))
            code, output = container.exec_run("rndc reload")
            if code != 0:
                return "'rndc reload' failed", None
        except docker.errors.NotFound:
            return "DNS server not found", None

        return None, True

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()

        if func == "list":
            dbc.execute("SELECT * FROM dns_server;") 
            results = dbc.fetchall()
            new_results = []
            for row in results:
                new_row = list(row)
                
                _, status = self.docker_status(INSTANCE_TEMPLATE.format(row[0]))
                new_row.append(status[0])
                new_row.append(status[1])
                
                
                new_results.append(new_row)

            return None, {
                "rows": new_results,
                "columns": ['ID', "server_ip", 'description', 'domain', 'built', 'status']
            }
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
        elif func == "remove_server":
            perror, _ = self.validate_params(self.__FUNCS__['remove_server'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(dns_server_id)

            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            # Ignore any shutdown errors, maybe the container was stopped externally
            self.run("stop_server", id=dns_server_id)

            server_ip = result[0]
            
            # Deallocate our IP address
            self.mm['ipreserve'].run("remove_ip", ip_addr=server_ip)

            # Remove the container from the database
            dbc.execute("DELETE FROM dns_server WHERE server_id=?", (dns_server_id,))
            self.mm.db.commit()

            return self.docker_delete(container_name)
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

            # Insert server info into the database
            dbc.execute('INSERT INTO dns_server (server_ip, server_desc, server_domain) VALUES (?, ?, ?)', (server_ip, description, domain))
            self.mm.db.commit()

            dns_server_id = dbc.lastrowid
            container_name = INSTANCE_TEMPLATE.format(dns_server_id)

            # Setup config directories
            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)

            if os.path.exists(dns_config_path):
                self.print("Removing old directory...")
                shutil.rmtree(dns_config_path)

            os.mkdir(dns_config_path)
            os.mkdir(dns_config_path + "/conf")
            os.mkdir(dns_config_path + "/zones")
            shutil.copy("./docker-images/dns/config-template", dns_config_path + "/named.conf")

            # Create forwarders file
            open(dns_config_path + "/conf/forwarders.conf", "a").close()

            vols = {
                dns_config_path: {"bind": "/etc/bind", 'mode': 'rw'}
            }

            environment = {}

            # Create the Docker container
            err, _ = self.docker_create(container_name, vols, environment)
            if err is not None:
                return err, None

            # Start the server
            error, result = self.run("start_server", id=dns_server_id)
            if error is not None:
                return error, None

            # If we are the first DNS server, then set us as the default DNS server for LXD containers
            if dns_server_id == 1:
                err, switch = self.mm['netreserve'].run("get_ip_switch", ip_addr=server_ip)
                if err:
                    return err, None
                network = self.mm.lxd.networks.get(switch)
                network.config['raw.dnsmasq'] = 'dhcp-option=option:dns-server,{}'.format(server_ip) 
                network.save()

            return None, True           
        elif func == "add_zone":
            perror, _ = self.validate_params(self.__FUNCS__['add_zone'], kwargs)
            if perror is not None:
                return perror, None

            return self._add_zone(kwargs['id'], kwargs['zone'], kwargs['direction'])
        elif func == "smart_add_record":
            perror, _ = self.validate_params(self.__FUNCS__['smart_add_record'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            direction = kwargs['direction']
            record_type = kwargs['type']
            value = kwargs['value']
            autocreate = kwargs['autocreate']

            found = False
            counter = 0

            fqdn_split = fqdn.split(".")

            while found == False and counter < len(fqdn_split):
                search_domain = '.'.join(fqdn_split[counter:])
                dns_server_id = self._get_dns_server(search_domain)
                if dns_server_id is not None:
                    found = True
                counter += 1

            if found == False:
                return "Could not find a parent domain for {}".format(fqdn), None 

            first, zone = self._split_fqdn(fqdn)

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            zone_path = "{}/zones/{}.{}".format(dns_config_path, zone, direction)

            if not os.path.exists(zone_path):
                if autocreate == True:
                    self._add_zone(dns_server_id, zone, direction)
                else:
                    return "Zone for FQDN {} in server {} not found".format(fqdn, dns_server_id), None

            name = '.'.join(fqdn_split[:-1])

            return self.run('add_record', id=dns_server_id, zone=zone, direction=direction, type=record_type, name=name, value=value)
        elif func == "smart_remove_record":
            perror, _ = self.validate_params(self.__FUNCS__['smart_remove_record'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            direction = kwargs['direction']
            record_type = kwargs['type']
            value = kwargs['value']

            found = False
            counter = 0

            fqdn_split = fqdn.split(".")

            while found == False and counter < len(fqdn_split):
                search_domain = '.'.join(fqdn_split[counter:])
                dns_server_id = self._get_dns_server(search_domain)
                if dns_server_id is not None:
                    found = True
                counter += 1

            if found == False:
                return "Could not find a parent domain for {}".format(fqdn), None 

            first, zone = self._split_fqdn(fqdn)

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            zone_path = "{}/zones/{}.{}".format(dns_config_path, zone, direction)

            if not os.path.exists(zone_path):
                return "Zone for FQDN {} in server {} not found".format(fqdn, dns_server_id), None

            if not fqdn.endswith("."):
                fqdn += "."

            return self.run('remove_record', id=dns_server_id, zone=zone, direction=direction, type=record_type, name=fqdn, value=value)
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
            

            

            if not name.endswith(".") and record_type == "A" and name.endswith(zone):
                name = name + "."

            zone = easyzone.zone_from_file(zone, zone_path)

            zone.add_name(name)
            ns = zone.names[name].records(record_type, create=True)
            ns.add(value)
            zone.save(autoserial=True)

            return self._rndc_reload(dns_server_id)        
        elif func == "remove_record":
            perror, _ = self.validate_params(self.__FUNCS__['remove_record'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']
            zone_name = kwargs['zone']
            direction = kwargs['direction']
            record_type = kwargs['type']
            name = kwargs['name']
            value = kwargs['value']

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            zone_path =  "{}/zones/{}.{}".format(dns_config_path, zone_name, direction)
            zone = easyzone.zone_from_file(zone_name, zone_path)

            if name[len(name)-1] != "." and record_type == "A":
                name = name + "."


            if name not in zone.get_names():
                return "{} not in zone {}".format(name, zone_name), None
            records = zone.names[name].records(record_type, create=True)
            try:
                records.delete(value)
            except easyzone.RecordsError: 
                return "Value '{}' not in records".format(value), None
            zone.save(autoserial=True)

            try:
                container = self.mm.docker.containers.get(INSTANCE_TEMPLATE.format(dns_server_id))
                code, output = container.exec_run("rndc reload")
                if code != 0:
                    return "'rndc reload' failed", None
            except docker.errors.NotFound:
                return "DNS server not found", None

            return None, True
        elif func == "add_host":
            perror, _ = self.validate_params(self.__FUNCS__['add_host'], kwargs)
            if perror is not None:
                return perror, None

            return self._add_host(kwargs['fqdn'], kwargs['ip_addr'])
        elif func == "remove_host":
            perror, _ = self.validate_params(self.__FUNCS__['remove_host'], kwargs)
            if perror is not None:
                return perror, None

            return self._remove_host(kwargs['fqdn'], kwargs['ip_addr'])
        elif func == "start_server":
            perror, _ = self.validate_params(self.__FUNCS__['start_server'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']

            # Ensure server exists
            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None
            
            container_name = INSTANCE_TEMPLATE.format(dns_server_id)
            server_ip = result[0]

            # Start the Docker container
            return self.docker_start(container_name, server_ip)
        elif func == "stop_server":
            perror, _ = self.validate_params(self.__FUNCS__['stop_server'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']
            container_name = INSTANCE_TEMPLATE.format(dns_server_id)

            _, status = self.docker_status(container_name)
            if status is not None and status[1] != "running":
                return "DNS server is not running", None

            # Find the server in the database
            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            server_ip = result[0]
            
            # Stop the container
            return self.docker_stop(container_name, server_ip)
        elif func == "list_forwarders":
            perror, _ = self.validate_params(self.__FUNCS__['list_forwarders'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            forwarder_conf =  "{}/conf/forwarders.conf".format(dns_config_path)

            # Ensure server exists
            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            forwarders = self._parse_forwarders_file(forwarder_conf)

            forwarder_columns = []
            for forwarder in forwarders:
                forwarder_columns.append([forwarder])

            return None, {
                "rows": forwarder_columns,
                "columns": ['forwarder']
            }
        elif func == "add_forwarder":
            perror, _ = self.validate_params(self.__FUNCS__['add_forwarder'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']
            forwarder = kwargs['ip_addr']

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            forwarder_conf =  "{}/conf/forwarders.conf".format(dns_config_path)

            # Ensure server exists
            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            forwarders = self._parse_forwarders_file(forwarder_conf)

            if forwarder in forwarders:
                return "Forwarder already added", None

            forwarders.append(forwarder)

            self._write_forwarders_file(forwarder_conf, forwarders)

            return self._rndc_reload(dns_server_id)

        elif func == "remove_forwarder":
            perror, _ = self.validate_params(self.__FUNCS__['add_forwarder'], kwargs)
            if perror is not None:
                return perror, None

            dns_server_id = kwargs['id']
            forwarder = kwargs['ip_addr']

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)
            forwarder_conf =  "{}/conf/forwarders.conf".format(dns_config_path)

            # Ensure server exists
            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            forwarders = self._parse_forwarders_file(forwarder_conf)

            if not forwarder in forwarders:
                return "Forwarder not added", None

            forwarders.remove(forwarder)

            self._write_forwarders_file(forwarder_conf, forwarders)

            return self._rndc_reload(dns_server_id)
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        self.check_working_dir()

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dns_server';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE dns_server (server_id INTEGER PRIMARY KEY, server_ip TEXT, server_desc TEXT, server_domain TEXT);")
            self.mm.db.commit()
    
    def build(self):
        self.print("Building DNS server image...")
        _, logs = self.mm.docker.images.build(path="./docker-images/dns/", tag=self.__SERVER_IMAGE_NAME__, rm=True)
        # self.print(logs)

    def get_list(self):
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_id, server_ip, server_desc FROM dns_server;")
        results = dbc.fetchall()

        return self._list_add_data(results, INSTANCE_TEMPLATE)

    def save(self):
        dbc = self.mm.db.cursor()
        dbc.execute("SELECT server_id FROM dns_server;")
        results = dbc.fetchall()

        return self._save_add_data(results, INSTANCE_TEMPLATE)

    def restore(self, restore_data):
        dbc = self.mm.db.cursor()
        
        for server_data in restore_data:
            dbc.execute("SELECT server_ip FROM dns_server WHERE server_id=?", (server_data[0],))
            results = dbc.fetchone()
            if results:
                self._restore_server(INSTANCE_TEMPLATE.format(server_data[0]), results[0], server_data[1])


__MODULE__ = DNSServer