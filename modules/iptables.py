import os
import subprocess
import shutil
from string import Template, ascii_letters
import random
import shlex


import lib.validate as validate
from lib.base_module import BaseModule

STORAGE_DIR = "{}/work/iptables".format(os.getcwd())
INT_IFACE_PATH = STORAGE_DIR + "/int_iface"
EXT_IFACE_PATH = STORAGE_DIR + "/ext_iface"

class Iptables(BaseModule):
    
    __FUNCS__ = {
        "list": {
            "_desc": "View iptables rules"
        },
        "list_order": {
            "_desc": "View iptables rules in order they will appear (opposite of addition)"
        },
        "show_ifaces": {
            "_desc": "Show configured interfaces"
        },
        "set_external_iface": {
            "_desc": "Set the external interface (used for NAT)",
            "iface": "SIMPLE_STRING",
        },
        "set_internal_iface": {
            "_desc": "Set the internal inferface",
            "iface": "SIMPLE_STRING"
        },
        "add_nat_allow": {
            "_desc": "Add NAT rule (adds to top of chain). Use ! to negate, and * for allow all",
            "range": "TEXT"
        },
        "add_raw": {
            "_desc": "Add raw rule (adds to top of chain)",
            "cmd": "ADVTEXT",
            "chain": "SIMPLE_STRING"
        },
        "add_raw_to_table": {
            "_desc": "Add rule to table (adds to top of chain)",
            "cmd": "ADVTEXT",
            "table": "SIMPLE_STRING",
            "chain": "SIMPLE_STRING"
        },
        "remove_rule": {
            "_desc": "Remove a iptables rule",
            "id": "INTEGER"
        }
    } 

    __SHORTNAME__  = "iptables"
    __DESC__ = "iptables rules"
    __AUTHOR__ = "Jacob Hartman"

    def __init__(self, mm):
        self.mm = mm
        self.ext_iface = ""
        self.int_iface = ""

    def run(self, func, **kwargs):
        dbc = self.mm.db.cursor()
        # Put list of functions here
        if func == "list":
            dbc.execute("SELECT * FROM iptables;") 
            results = dbc.fetchall()

            return None, {
                "rows": results,
                "columns": ['ID', "Table", "Chain", "Command"]
            }
        elif func == "list_order":
            dbc.execute("SELECT * FROM iptables;") 
            results = dbc.fetchall()
            results.reverse()

            return None, {
                "rows": results,
                "columns": ['ID', "Table", "Chain", "Command"]
            }
        elif func == "show_ifaces":
            iface_list = [
                ("External", self.ext_iface),
                ("Internal", self.int_iface)
            ]

            return None, {
                "rows": iface_list,
                "columns": ['Role', "Interface"]
            }
        elif func == "remove_rule":
            perror, _ = self.validate_params(self.__FUNCS__['remove_rule'], kwargs)
            if perror is not None:
                return perror, None

            rule_id = kwargs['id']

            return self._remove_iptables_cmd(rule_id)
        elif func == "set_external_iface":
            perror, _ = self.validate_params(self.__FUNCS__['set_external_iface'], kwargs)
            if perror is not None:
                return perror, None

            # Extract our variables here
            iface = kwargs['iface']

            self.ext_iface = iface 

            ext_iface_file = open(EXT_IFACE_PATH, "w+")
            ext_iface_file.write(iface)
            ext_iface_file.close()

            return None, True 

        elif func == "set_internal_iface":
            perror, _ = self.validate_params(self.__FUNCS__['set_internal_iface'], kwargs)
            if perror is not None:
                return perror, None

            # Extract our variables here
            iface = kwargs['iface']

            self.int_iface = iface 

            int_iface_file = open(INT_IFACE_PATH, "w+")
            int_iface_file.write(iface)
            int_iface_file.close()

            return None, True 

        elif func == "add_nat_allow":
            perror, _ = self.validate_params(self.__FUNCS__['add_nat_allow'], kwargs)
            if perror is not None:
                return perror, None

            # Extract our variables here
            ip_range = kwargs['range']

            if self.ext_iface == "":
                return "External interface must be set", None

            if ip_range.startswith("!"):
                ip_range = ip_range[1:].strip()
                return self._add_iptables_cmd("nat","POSTROUTING", "! -s {} -o {} -j MASQUERADE".format(ip_range, self.ext_iface))
            elif ip_range.strip() == "*":
                return self._add_iptables_cmd("nat","POSTROUTING", "-o {} -j MASQUERADE".format(ip_range, self.ext_iface))
            else:
                return self._add_iptables_cmd("nat","POSTROUTING", "-s {} -o {} -j MASQUERADE".format(ip_range, self.ext_iface))
        
        elif func == "add_raw":
            perror, _ = self.validate_params(self.__FUNCS__['add_raw'], kwargs)
            if perror is not None:
                return perror, None

            # Extract our variables here
            chain = kwargs['chain']
            raw_command = kwargs['cmd']

            return self._add_iptables_cmd("",chain, raw_command)

        elif func == "add_raw_to_table":
            perror, _ = self.validate_params(self.__FUNCS__['add_raw'], kwargs)
            if perror is not None:
                return perror, None

            # Extract our variables here
            chain = kwargs['chain']
            itable = kwargs['table']
            raw_command = kwargs['cmd']

            return self._add_iptables_cmd(itable,chain, raw_command)

        
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def _add_iptables_cmd(self, table, chain, command):
        dbc = self.mm.db.cursor()

        # Add the rule to the database
        dbc.execute('INSERT INTO iptables (itable, chain, command) VALUES (?, ?, ?)', (table, chain, command))
        self.mm.db.commit()

        rule_id = dbc.lastrowid

        return self._add_rule(table, chain, command, rule_id)


    def _add_rule(self, table, chain, command, rule_id):
        iptables_cmd = []
        if table is not None and table != "":
            iptables_cmd += ["-t", table]
        else:
            table = ""
    
        iptables_cmd += ["-I", chain, "1"]
        iptables_cmd += shlex.split(command)
        iptables_cmd += ["-m", "comment", "--comment", "FakerNet Iptables rule {}".format(rule_id)]


        str_cmd = " ".join(["/usr/bin/sudo", "-n", "/sbin/iptables"] + iptables_cmd)
        try:
            subprocess.check_output(["/usr/bin/sudo", "-n", "/sbin/iptables"] + iptables_cmd, stderr=subprocess.DEVNULL)     
        except subprocess.CalledProcessError as ex:
            return "Command failed: " + str_cmd, ""

        return None, rule_id

    def _remove_iptables_cmd(self, rule_id):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT itable, chain, command FROM iptables WHERE rule_id=?", (rule_id,))
        result = dbc.fetchone()
        if not result:
            return "Rule does not exist", None

        table = result[0]
        chain = result[1]
        command = result[2]

        dbc.execute("DELETE FROM iptables WHERE rule_id=?", (rule_id,))
        self.mm.db.commit()

        return self._remove_rule(table, chain, command, rule_id)

    def _remove_rule(self, table, chain, command, rule_id):
        iptables_cmd = []
        if table is not None and table != "":
            iptables_cmd += ["-t", table]
        else:
            table = ""
        
        iptables_cmd += ["-D", chain]
        iptables_cmd += ["-m", "comment", "--comment", "FakerNet Iptables rule {}".format(rule_id)]
        iptables_cmd += shlex.split(command)
        try:
            subprocess.check_output(["/usr/bin/sudo", "-n", "/sbin/iptables"] + iptables_cmd, stderr=subprocess.DEVNULL)     
        except subprocess.CalledProcessError:
            return "Command failed, you may need to manually remove rule", None

        return None, True

    def check(self):
        dbc = self.mm.db.cursor()

        # This creates the module's working directory.
        if not os.path.exists(STORAGE_DIR):
            os.mkdir(STORAGE_DIR)

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='iptables';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE iptables (rule_id INTEGER PRIMARY KEY, itable TEXT, chain TEXT, command TEXT);")
            self.mm.db.commit()

        if os.path.exists(INT_IFACE_PATH):
            int_iface_file = open(INT_IFACE_PATH, "r")
            self.int_iface = int_iface_file.read().strip()
            int_iface_file.close()

        if os.path.exists(EXT_IFACE_PATH):
            ext_iface_file = open(EXT_IFACE_PATH, "r")
            self.ext_iface = ext_iface_file.read().strip()
            ext_iface_file.close()

        dbc.execute("SELECT * FROM iptables;") 
        results = dbc.fetchall()

        for result in results:
            rule_id = result[0]
            table = result[1]
            chain = result[2]
            command = result[3]

            self._remove_rule(table, chain, command, rule_id)
            self._add_rule(table, chain, command, rule_id)

    def build(self):
        pass

    def save(self):
        pass

    def restore(self, restore_data):
        pass


__MODULE__ = Iptables