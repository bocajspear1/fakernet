import os
import shutil 
import time
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
    forwarders { };
};
"""

ZONE_FORWARDING_CONFIG_TEMPLATE = """zone "$ZONE" {
    type forward;
    forward only;
    forwarders { $FORWARDER; };
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
            "id": "INTEGER"
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
            "value": "ADVTEXT",
            "autocreate": "BOOLEAN"
        },
        "smart_remove_record": {
            "_desc": "Add a record to a DNS server, detecting server and zone",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "fqdn": "TEXT",
            "value": "ADVTEXT"
        },
        "add_record": {
            "_desc": "Add a record to a DNS server",
            "id": "INTEGER",
            "zone": "TEXT",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "name": "TEXT",
            "value": "ADVTEXT"
        },
        "remove_record": {
            "_desc": "Remove a record from a DNS server",
            "id": "INTEGER",
            "zone": "TEXT",
            "direction": ['fwd', 'rev'],
            "type": "TEXT",
            "name": "TEXT",
            "value": "ADVTEXT"
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
        },
        "smart_add_subdomain_server": {
            "_desc": "Add subdomain server, automatically setting up root server to point to it",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "smart_remove_subdomain_server": {
            "_desc": "Remove subdomain server, automatically deleting entries in the parent server",
            "id": "INTEGER"
        },
        "smart_add_root_server": {
            "_desc": "Add a new root domain server (e.g. .com or .net), automatically setting up root server to point to it",
            "root_name": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "smart_remove_root_server": {
            "_desc": "Remove root domain server (e.g. .com or .net), automatically deleting entries in the parent server",
            "id": "INTEGER"
        },
        "smart_add_external_subdomain": {
            "_desc": "Add subdomain that points to an external DNS server",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "smart_remove_external_subdomain": {
            "_desc": "Add subdomain that points to an external DNS server",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "add_override": {
            "_desc": "Add a single domain override",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
        "remove_override": {
            "_desc": "Remove a single domain override",
            "fqdn": "TEXT",
            "ip_addr": "IP_ADDR"
        },
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

    def _add_forwarding_zone(self, dns_server_id, zone, forwarder):

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)

        zone_config_path = "{}/conf/forward-{}.conf".format(dns_config_path, zone)

        t = Template(ZONE_FORWARDING_CONFIG_TEMPLATE) 
        config_file = open(zone_config_path, "w+")
        config_file.write(t.substitute({'ZONE' : zone, 'FORWARDER': forwarder})) 
        config_file.close()

        main_config_contents = open(dns_config_path + "/named.conf", "r").read()
        if not "include \"/etc/bind/conf/{}.conf\";\n".format(zone) in main_config_contents:
            main_config_file = open(dns_config_path + "/named.conf", "a")
            main_config_file.write("\ninclude \"/etc/bind/conf/forward-{}.conf\";\n".format(zone))

        return None, True

    def _remove_forwarding_zone(self, dns_server_id, zone):

        dns_config_path = "{}/{}".format(DNS_BASE_DIR, dns_server_id)

        zone_config_path = "{}/conf/forward-{}.conf".format(dns_config_path, zone)

        os.remove(zone_config_path)

        main_config = open(dns_config_path + "/named.conf", "r+")
        main_config_contents = main_config.read()
        config_lines = main_config_contents.split("\n")
        new_contents = ""
        for line in config_lines:
            if "include \"/etc/bind/conf/forward-{}.conf\";".format(zone) not in line:
                new_contents += line + "\n"
        
        main_config.seek(0)
        main_config.truncate()
        main_config.write(new_contents)
        main_config.close()

        return None, True

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

    def _check_serial(self, dns_server_id, zone, zonefile, serial):
        try:
            container = self.mm.docker.containers.get(INSTANCE_TEMPLATE.format(dns_server_id))

            ok = False 
            while not ok:
                code, output = container.exec_run("rndc zonestatus {}".format(zone))
                if code != 0:
                    return "'rndc zonestatus' failed: {}".format(output), None

                if str(serial) not in output.decode():
                    print("reload did't load new serial")
                    err, _ = self._rndc_reload(dns_server_id, zonefile)
                    if err is not None:
                        return err, None
                else:
                    ok = True
        except docker.errors.NotFound:
            return "DNS server not found", None
        
        return None, True

    def _rndc_reload(self, dns_server_id, zonefile=None):
        try:
            time.sleep(3)
            container = self.mm.docker.containers.get(INSTANCE_TEMPLATE.format(dns_server_id))
            if zonefile is not None:
                code, output = container.exec_run("cat /etc/bind/zones/{}".format(zonefile))
                if code != 0:
                    return "Reading zonefile {} failed".format(zonefile), None
                code, output = container.exec_run("touch /etc/bind/zones/{}".format(zonefile))
                if code != 0:
                    return "Running touch on zonefile {} failed".format(zonefile), None
                # print("ran touch")
                time.sleep(3)
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

            # Prepare the override zone
            override_zone_path = dns_config_path + "/zones/fn.rpz"
            zone_file = open("./docker-images/dns/zone-template", "r").read()
            zone_file = zone_file.replace("TEMPLATE.ZONE", "fn.rpz")
            zone_file = zone_file.replace("1.1.1.1", "127.0.0.1")
            out_zone = open(override_zone_path, "w+")
            out_zone.write(zone_file)
            out_zone.close()

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

            return None, dns_server_id           
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

            zoneobj = easyzone.zone_from_file(zone, zone_path)

            zoneobj.add_name(name)
            ns = zoneobj.names[name].records(record_type, create=True)
            ns.add(value)
            new_serial = zoneobj.save(autoserial=True)

            zonefile = "{}.{}".format(zone, direction)
            err, _ = self._rndc_reload(dns_server_id, zonefile=zonefile) 
            if err is not None:
                return err, None

            time.sleep(4)

            return self._check_serial(dns_server_id, zone, zonefile, new_serial)
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

            self._rndc_reload(dns_server_id, zonefile="{}.{}".format(zone_name, direction))

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
        elif func == "smart_add_subdomain_server":
            perror, _ = self.validate_params(self.__FUNCS__['smart_add_subdomain_server'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']

            found = False
            counter = 0
            fqdn_split = fqdn.split(".")
            found_domain = ""
            parent_server_id = None

            while found == False and counter < len(fqdn_split):
                search_domain = '.'.join(fqdn_split[counter:])
                parent_server_id = self._get_dns_server(search_domain)
                if parent_server_id is not None:
                    found = True
                    search_split = search_domain.split(".")
                    
                    found_domain = '.'.join(search_split[1:])
                counter += 1

            if found == False:
                return "Could not find a parent domain for {}".format(fqdn), None 

            error, new_server_id = self.run('add_server', ip_addr=ip_addr, description="Automatically generated subdomain server for {}".format(fqdn), domain=fqdn)
            if error is not None:
                return error, None

            zerror, _ = self.run('add_zone', id=new_server_id, direction="fwd", zone=fqdn)
            if zerror is not None:
                return zerror, None

            if not fqdn.endswith("."):
                fqdn = fqdn + "."
            ns_name = "ns1.{}".format(fqdn)
            
            rerror, _ = self.run("add_record", id=parent_server_id, zone=found_domain, direction="fwd", type='NS', name=fqdn, value=ns_name)
            if rerror is not None:
                return rerror, None

            rerror, _ = self.run("add_record", id=parent_server_id, zone=found_domain, direction="fwd", type='A', name=ns_name, value=ip_addr)
            if rerror is not None:
                return rerror, None

            error, _ = self._rndc_reload(new_server_id, zonefile="{}fwd".format(fqdn))
            if error is not None:
                return error, None
            error, _ = self._rndc_reload(parent_server_id, zonefile="{}.fwd".format(found_domain))
            if error is not None:
                return error, None

            return None, new_server_id
        elif func == "smart_remove_subdomain_server":
            perror, _ = self.validate_params(self.__FUNCS__['smart_remove_subdomain_server'], kwargs)
            if perror is not None:
                return perror, None
            
            dns_server_id = kwargs['id']
            dbc.execute("SELECT server_ip,server_domain FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            ip_addr = result[0]
            server_domain = result[1]

            # Remove the server
            derror,_ = self.run("remove_server", id=dns_server_id)
            if derror is not None:
                return derror, None

            # Find the parent server, this will now go to the parent since the child server has been deleted
            found = False
            counter = 0
            fqdn_split = server_domain.split(".")
            found_domain = ""
            parent_server_id = None

            while found == False and counter < len(fqdn_split):
                search_domain = '.'.join(fqdn_split[counter:])
                parent_server_id = self._get_dns_server(search_domain)
                if parent_server_id is not None:
                    found = True
                    search_split = search_domain.split(".")
                    found_domain = '.'.join(search_split[1:])
                counter += 1

            if not server_domain.endswith("."):
                server_domain = server_domain + "."
            ns_name = "ns1.{}".format(server_domain)
            
            rerror, _ = self.run("remove_record", id=parent_server_id, zone=found_domain, direction="fwd", type='NS', name=server_domain, value=ns_name)
            if rerror is not None:
                return rerror, None

            rerror, _ = self.run("remove_record", id=parent_server_id, zone=found_domain, direction="fwd", type='A', name=ns_name, value=ip_addr)
            if rerror is not None:
                return rerror, None

            error, _ = self._rndc_reload(parent_server_id, zonefile="{}.fwd".format(found_domain))
            if error is not None:
                return error, None
            
            return None, True
        elif func == "smart_add_root_server":
            perror, _ = self.validate_params(self.__FUNCS__['smart_add_root_server'], kwargs)
            if perror is not None:
                return perror, None

            root_name = kwargs['root_name']
            ip_addr = kwargs['ip_addr']

            if len(root_name.split(".")) > 2 or (len(root_name.split(".")) == 2 and not root_name.endswith(".")):
                return "root_name should be a new root domain (e.g. .net or .com), not a fqdn", None
            
            # Add the new root domain server
            error, new_server_id = self.run('add_server', ip_addr=ip_addr, description="Automatically generated root server for {}".format(root_name), domain=root_name)
            if error is not None:
                return error, None

            # Add the root domain zone to new server
            zerror, _ = self.run('add_zone', id=new_server_id, direction="fwd", zone=root_name)
            if zerror is not None:
                return zerror, None

            ferror, _ = self._add_forwarding_zone(1, root_name, ip_addr)
            if ferror is not None:
                return ferror, None

            error, _ = self._rndc_reload(1)
            if error is not None:
                return error, None
            
            error, _ = self._rndc_reload(new_server_id)
            if error is not None:
                return error, None
            

            return None, new_server_id
        elif func == "smart_remove_root_server":
            perror, _ = self.validate_params(self.__FUNCS__['smart_remove_root_server'], kwargs)
            if perror is not None:
                return perror, None
            
            dns_server_id = kwargs['id']
            dbc.execute("SELECT server_ip,server_domain FROM dns_server WHERE server_id=?", (dns_server_id,))
            result = dbc.fetchone()
            if not result:
                return "DNS server does not exist", None

            ip_addr = result[0]
            server_domain = result[1]

            # Remove the server
            derror,_ = self.run("remove_server", id=dns_server_id)
            if derror is not None:
                return derror, None

            self._remove_forwarding_zone(1, server_domain)
            
            error, _ = self._rndc_reload(1)
            if error is not None:
                return error, None

            return None, True
        elif func == "smart_add_external_subdomain":
            perror, _ = self.validate_params(self.__FUNCS__['smart_add_external_subdomain'], kwargs)
            if perror is not None:
                return perror, None

            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']

            found = False
            counter = 0
            fqdn_split = fqdn.split(".")
            found_domain = ""
            parent_server_id = None

            while found == False and counter < len(fqdn_split):
                search_domain = '.'.join(fqdn_split[counter:])
                parent_server_id = self._get_dns_server(search_domain)
                if parent_server_id is not None:
                    found = True
                    search_split = search_domain.split(".")
                    
                    found_domain = '.'.join(search_split[1:])
                counter += 1

            if found == False:
                return "Could not find a parent domain for {}".format(fqdn), None 

            if not fqdn.endswith("."):
                fqdn = fqdn + "."
            ns_name = "ns1.{}".format(fqdn)
            
            rerror, _ = self.run("add_record", id=parent_server_id, zone=found_domain, direction="fwd", type='NS', name=fqdn, value=ns_name)
            if rerror is not None:
                return rerror, None

            rerror, _ = self.run("add_record", id=parent_server_id, zone=found_domain, direction="fwd", type='A', name=ns_name, value=ip_addr)
            if rerror is not None:
                return rerror, None

            error, _ = self._rndc_reload(parent_server_id, zonefile="{}.fwd".format(found_domain))
            if error is not None:
                return error, None
            
            return None, True
        elif func == "smart_remove_external_subdomain":
            perror, _ = self.validate_params(self.__FUNCS__['smart_remove_external_subdomain'], kwargs)
            if perror is not None:
                return perror, None
            
            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']

            # Find the parent server, this will now go to the parent since the child server has been deleted
            found = False
            counter = 0
            fqdn_split = fqdn.split(".")
            found_domain = ""
            parent_server_id = None

            while found == False and counter < len(fqdn_split):
                search_domain = '.'.join(fqdn_split[counter:])
                parent_server_id = self._get_dns_server(search_domain)
                if parent_server_id is not None:
                    found = True
                    search_split = search_domain.split(".")
                    found_domain = '.'.join(search_split[1:])
                counter += 1

            if not fqdn.endswith("."):
                fqdn = fqdn + "."
            ns_name = "ns1.{}".format(fqdn)
            
            rerror, _ = self.run("remove_record", id=parent_server_id, zone=found_domain, direction="fwd", type='NS', name=fqdn, value=ns_name)
            if rerror is not None:
                return rerror, None

            rerror, _ = self.run("remove_record", id=parent_server_id, zone=found_domain, direction="fwd", type='A', name=ns_name, value=ip_addr)
            if rerror is not None:
                return rerror, None

            error, _ = self._rndc_reload(parent_server_id, zonefile="{}.fwd".format(found_domain))
            if error is not None:
                return error, None
            
            return None, True
        elif func == "add_override":
            perror, _ = self.validate_params(self.__FUNCS__['add_override'], kwargs)
            if perror is not None:
                return perror, None
            
            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']

            if fqdn.endswith("."):
                fqdn = fqdn[:-1]

            # Python DNS module does not support zones with names not in the subdomain.
            # We just do rudimentary manual records

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, 1)
            override_zone = "{}/zones/fn.rpz".format(dns_config_path)

            override_file = open(override_zone, "r")
            lines = override_file.readlines()
            override_file.close()

            found = False 

            override_file = open(override_zone, "w")
            for line in lines:
                line_split = line.split(" ")
                if line_split[0] == fqdn:
                    line_split[4] = ip_addr
                    found = True
                override_file.write(" ".join(line_split))
            
            if not found:
                override_file.write("\n")
                override_file.write(" ".join([
                    fqdn, "604800", "IN", "A", ip_addr
                ]))
                override_file.write("\n")
            
            override_file.close()

            error, _ = self._rndc_reload(1, zonefile="fn.rpz")
            if error is not None:
                return error, None

            return None, True
        elif func == "remove_override":
            perror, _ = self.validate_params(self.__FUNCS__['remove_override'], kwargs)
            if perror is not None:
                return perror, None
            
            fqdn = kwargs['fqdn']
            ip_addr = kwargs['ip_addr']

            if fqdn.endswith("."):
                fqdn = fqdn[:-1]

            # Python DNS module does not support zones with names not in the subdomain.
            # We just do rudimentary manual records

            dns_config_path = "{}/{}".format(DNS_BASE_DIR, 1)
            override_zone = "{}/zones/fn.rpz".format(dns_config_path)

            override_file = open(override_zone, "r")
            lines = override_file.readlines()
            override_file.close()
            override_file = open(override_zone, "w")

            for line in lines:
                line_split = line.split(" ")
                if line_split[0] != fqdn and line_split[4] != ip_addr:
                    override_file.write(" ".join(line_split))

            override_file.close()

            error, _ = self._rndc_reload(1, zonefile="fn.rpz")
            if error is not None:
                return error, None

            return None, True
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