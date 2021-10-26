# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import shlex
import textwrap
import sys
import argparse
import os
import json

from prompt_toolkit import PromptSession, prompt, print_formatted_text, HTML 
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory

from lib.module_manager import ModuleManager
import lib.validate
import lib.prompt_builder as prompt_builder
from lib.version import FAKERNET_VERSION

import tableprint as tp
import animation

from getpass import getpass


import html
ASCIIART = html.escape("""
______    _             _   _      _   
|  ___|  | |           | \ | |    | |  
| |_ __ _| | _____ _ __|  \| | ___| |_ 
|  _/ _` | |/ / _ \ '__| . ` |/ _ \ __|
| || (_| |   <  __/ |  | |\  |  __/ |_ 
\_| \__,_|_|\_\___|_|  \_| \_/\___|\__|
""")


def print_table(data, headers):
    if len(data) == 0:
        print_formatted_text(HTML('<ansiyellow>No results</ansiyellow>'))
        return
    
    widths = []
    row_len = len(headers)

    for i in range(row_len):
        longest = 0
        for row in data:
            longest = max(len(str(row[i])), longest)
        longest = max(len(str(headers[i])), longest)
        widths.append(longest)

    tp.table(data, headers, width=widths)

class CommandCompleter(Completer):

    def __init__(self, mm, global_vars, in_func_level=False):
        super().__init__()
        self.mm = mm
        self.global_vars = global_vars
        self.in_func_level = in_func_level
        self.run_options = {}

    MAIN_COMMANDS = [
        'run',
        # 'global',
        # 'uglobal',
        'exit',
        'stats',
        'list_all',
        # 'list_running',
        'save',
        'restore',
        'useradd',
        'userls',
        'userdel'
    ]

    RUN_COMMANDS = [
        'run',
        'set',
        'unset',
        'execute',
        # 'info',
        'show',
        'back',
        # 'global',
        # 'uglobal',
    ]

    def get_completions(self, document, complete_event):
        command_string = document.text
        if " " not in command_string:
            command_list = self.MAIN_COMMANDS
            if self.in_func_level:
                command_list = self.RUN_COMMANDS
            
            for command in command_list:
                if command_string in command:
                    yield Completion(command, start_position=-(document.cursor_position))
            return
        else:
            command_split = []
            command = ""

            command_split = command_string.split(" ", 1)
            

            if len(command_split) >= 1:
                command = command_split[0]
            else:
                return

            arg_split = []
            try:
                arg_split = shlex.split(command_split[1])
            except ValueError:
                return

            if command_string[len(command_string)-1] == " ":
                arg_split.append('')

            if command == "run":
                # print_formatted_text(HTML('<b>' + str(command_split) + '</b>'))
                if len(arg_split) == 0 or len(arg_split) == 1:
                    for module in self.mm.list_modules():
                        if len(arg_split) == 0 or arg_split[0] == "" or module.startswith(arg_split[0]):
                            yield Completion(module, start_position=-(document.cursor_position)+len(command)+1)
                elif len(arg_split) == 2:
                    module_name = arg_split[0]
                    in_function = arg_split[1]
                    if module_name not in self.mm.list_modules():
                        return
                    module = self.mm[module_name]
                    pos = -(document.cursor_position)+len(command)+2+len(module_name)
                    all_entries = list(module.__FUNCS__.keys())
                    all_entries.append("help")
                    for func in all_entries:
                        if in_function == "" or func.startswith(in_function):
                            yield Completion(func, start_position=pos)
                else:
                    return
            elif command == "global":
                if len(arg_split) > 1 :
                    return 
                for global_var in self.global_vars:
                    if len(arg_split) == 0 or arg_split[0] == "" or global_var.startswith(arg_split[0]):
                        yield Completion(global_var, start_position=-(document.cursor_position)+len(command)+1)
            elif (command == "set" or command == "unset") and self.in_func_level == True:
                if len(arg_split) > 1 :
                    return 
                for variable in self.run_options:
                    if variable == "_desc":
                        continue
                    if len(arg_split) == 0 or arg_split[0] == "" or variable.startswith(arg_split[0]):
                        yield Completion(variable, start_position=-(document.cursor_position)+len(command)+1)
            else:
                return

class FakerNetConsole():

    def __init__(self, ip="127.0.0.1"):

        wait = animation.Wait(text="Looking for local FakerNet server")
        wait.start()
        self.mm = ModuleManager(ip=ip)
        error = self.mm.load()
        wait.stop()
        if error is not None:
            self.mm = ModuleManager(ip=ip, https=True, https_ignore=True)
            error = self.mm.load()
            wait.stop()
            if error is not None:
                if ip == "127.0.0.1":
                    print_formatted_text(HTML('\n\n<ansired>{}</ansired>'.format(error)))
                    wait = animation.Wait(text="FakerNet console is starting")
                    wait.start()
                    self.mm = ModuleManager()
                    self.mm.load()
                    wait.stop()

                    self.mm['init'].check()
                    self.host = "local"
                else:
                    print_formatted_text(HTML('<ansired>Failed to connect to the server at {}</ansired>'.format(ip)))
                    sys.exit(1)
            else:
                self.host = self.mm.ip
        else:
            self.host = self.mm.ip
            
        file_history = FileHistory(".fnhistory")
        self.session = PromptSession(history=file_history)
        self.global_vars = {
            "AUTO_ADD": False
        }

        self.completer = CommandCompleter(self.mm, self.global_vars)

        if self.mm.ip == None:
            err, _ = self.mm['init'].run("verify_permissions")
            if err is not None:
                print_formatted_text(HTML('<ansired>{}</ansired>'.format(err)))
                sys.exit(1)

        
        print_formatted_text(HTML('<ansigreen>{}</ansigreen>'.format(ASCIIART)))
        print_formatted_text(HTML('<skyblue>[v{}] Internet-in-a-box, \n</skyblue>'.format(self.mm.get_version())))

        if self.mm.ip == None:
            print_formatted_text(HTML('<ansigreen>NOTE: In non-server mode!</ansigreen>'))
            if self.mm['init'].init_needed:
                self.setup_prompts()
        else:
            print_formatted_text(HTML('<ansigreen>Connected to {}</ansigreen>'.format(self.mm.ip)))

            

        self.running = True
        self.current_command = None
        self.mm.logger.info("Started console")
        

    def setup_prompts(self):
        print_formatted_text(HTML('<skyblue>Welcome to FakerNet. We need to setup the base of your fake internet.</skyblue>'))

        base_net = None

        # Setup network
        premessage="Please enter the initial network allocation. The main DNS server will be hosted here."
        ok = False
        while not ok:

            print_formatted_text(HTML('<slateblue>{}</slateblue>'.format(premessage)))
            base_net = prompt_builder.prompt_get_network(prompt_text="network>")

            err, _ = self.mm['netreserve'].run("add_network", net_addr=base_net, description="The central network for Fakernet. Hosts central DNS server and other critical services.", switch="fakernet0")
            if err is None:
                ok = True
            else:
                print_formatted_text(HTML('<ansired>{}</ansired>'.format(err)))

        # Setup DNS server

        dns_root = None

        ok = False
        while not ok:
            premessage="Please enter the root name for the DNS server, this could be 'test', 'fake' or something else."
            print_formatted_text(HTML('<slateblue>{}</slateblue>'.format(premessage)))

            dns_root = prompt_builder.prompt_get_dns_name(prompt_text="dns name>")

            premessage="Enter the IP of the main DNS server. This will be the main resolver for your FakerNet instance.\n\n(You will need to point all systems to this DNS server for things to work.)"
            print_formatted_text(HTML('<slateblue>{}</slateblue>'.format(premessage)))

            dns_ip = prompt_builder.prompt_get_ip_in_network(base_net, prompt_text="dns ip>")

            err, _ = self.mm['dns'].run("add_server", ip_addr=dns_ip, description="FakerNet Main DNS Resolver", domain=dns_root)
            if err is None:
                ok = True
                err, _ = self.mm['dns'].run("add_zone", id=1, direction="fwd", zone=dns_root)
                if err is not None:
                    print_formatted_text(HTML('<ansired>{}</ansired>'.format(err)))
                    ok = False

            else:
                print_formatted_text(HTML('<ansired>{}</ansired>'.format(err)))
            
        # Setup CA
        ok = False
        while not ok:
            premessage="Please enter the IP of the main CA server. Services will auto-generate their certificates from here."
            print_formatted_text(HTML('<slateblue>{}</slateblue>'.format(premessage)))

            ca_ip = prompt_builder.prompt_get_ip_in_network(base_net, prompt_text="ca ip>")

            err, _ = self.mm['minica'].run("add_server", fqdn="ca." + dns_root, ip_addr=ca_ip)
            if err is None:
                ok = True
            else:
                print_formatted_text(HTML('<ansired>{}</ansired>'.format(err)))
            
        print_formatted_text(HTML('<ansigreen>{}</ansigreen>'.format("Setup complete!")))

    def print_result(self, error, result):
        if error is not None:
            print_formatted_text(HTML('<ansired>Error: {}</ansired>'.format(error)))
        else:
            if isinstance(result, dict) and 'rows' in result and 'columns' in result:
                print_table(result['rows'], result['columns'])
            else:
                print_formatted_text(HTML('<ansigreen>OK</ansigreen>'))

    def run_module_function(self, module_name, function_name, args):
        error, result = self.mm[module_name].run(function_name, **args)
        self.print_result(error, result)

    def start(self):
        while self.running:
            try:
                prompt = self.host + '> '
                if self.current_command is not None:
                    self.completer.in_func_level = True
                    self.completer.run_options = self.current_command['function']
                    prompt = self.host + "(" + self.current_command['display_name'] + ')> '

                command_string = self.session.prompt(prompt, completer=self.completer)

                command_split = []
                try:
                    command_split = shlex.split(command_string)
                except ValueError:
                    print_formatted_text(HTML('<ansired>Invalid quotes or command</ansired>'))

                if len(command_split) > 0:
                    if self.current_command is not None:
                        self.func_level(command_split)
                    else:
                        self.main_level(command_split)
            
            except KeyboardInterrupt:
                self.running = False
            except EOFError:
                pass

    def main_level(self, command_input):
        command = command_input[0].lower()
        if command == "exit":
            self.running = False
        elif command == "run":
            self.command_run(command_input[1:])
        elif command == "global":
            pass
        elif command == "uglobal":
            pass
        elif command == "userls":
            error, users = self.mm.list_users()
            for user in users:
                print(" * " + user)
        elif command == "useradd":
            username = input("username> ")
            ok = False
            while not ok:
                password1 = getpass(prompt="password> ")
                password2 = getpass(prompt="password (again)> ")
                if password1 != password2:
                    print("Passwords do not match")
                else:
                    ok = True
            
            self.mm.add_user(username, password1)
            
        elif command == "list_all":
            error, server_list = self.mm.list_all_servers()
            if error is None:
                print_table(server_list, ["Module", "ID", "IP", "Description", "status"])
            else:
                print_formatted_text(HTML('<ansired>Error: "{}"</ansired>'.format(error)))
        elif command == "save":
            error = None
            if len(command_input) > 1:
                self.mm.save_state(save_name=command_input[1])
            else:
                self.mm.save_state()
            
            if error is None:
                print_formatted_text(HTML('<ansigreen>Save OK</ansigreen>'))
            else:
                print_formatted_text(HTML('<ansired>Save Error: "{}"</ansired>'.format(error)))
        elif command == "restore":
            error = None
            if len(command_input) > 1:
                error, _ = self.mm.restore_state(save_name=command_input[1])
            else:
                error, _ = self.mm.restore_state()

            if error is None:
                print_formatted_text(HTML('<ansigreen>Restore OK</ansigreen>'))
            else:
                print_formatted_text(HTML('<ansired>Restore Error: "{}"</ansired>'.format(error)))
        else:
            print_formatted_text(HTML('<ansired>Error: Invalid command "{}"</ansired>'.format(command)))

    def func_level(self, command_input):
        command = command_input[0].lower()
        if command == "exit":
            self.current_command = None
            self.completer.in_func_level = False
        elif command == "run":
            self.command_run(command_input[1:])
        elif command == "set":
            if len(command_input) < 3:
                print_formatted_text(HTML('<ansiyellow>set VAR VALUE</ansiyellow>'))
                return
            
            var_name = command_input[1]
            value = command_input[2]

            if var_name not in self.current_command['function']:
                print_formatted_text(HTML('<ansired>Error: Invalid variable "{}"</ansired>'.format(var_name)))
                return

            self.current_command['vars'][var_name] = value
        elif command == "unset":
            if len(command_input) < 2:
                print_formatted_text(HTML('<ansiyellow>unset VAR</ansiyellow>'))
                return

            var_name = command_input[1]

            if var_name not in self.current_command['function']:
                print_formatted_text(HTML('<ansired>Error: Invalid variable "{}"</ansired>'.format(var_name)))
                return

            del self.current_command['vars'][var_name]

        elif command == "show":
            if "_desc" in self.current_command['function']:
                print_formatted_text(HTML('<ansigreen>{}</ansigreen>'.format(self.current_command['function']['_desc'])))
            rows = []
            for variable in self.current_command['function']:
                if variable == "_desc":
                    continue
                if variable in self.current_command['vars']:
                    rows.append([variable, self.current_command['vars'][variable]])
                else:
                    rows.append([variable, "NULL"])
            print_table(rows, ["Variables", "Values"])
        elif command == "execute":
            for variable in self.current_command['function']:
                if variable == "_desc":
                    continue
                if variable not in self.current_command['vars']:
                    print_formatted_text(HTML('<ansired>Error: Variable "{}" not set</ansired>'.format(variable)))
                    return
            
            module_name = self.current_command['module_name']
            if module_name not in self.mm.list_modules():
                print_formatted_text(HTML('<ansired>Error: Got invalid module "{}"</ansired>'.format(module_name)))

            function_name = self.current_command['function_name']
            
            self.run_module_function(module_name, function_name, self.current_command['vars'])

        else:
            print_formatted_text(HTML('<ansired>Error: Invalid command "{}"</ansired>'.format(command)))


    def command_run(self, args):
        if len(args) < 2:
            print_formatted_text(HTML('<ansiyellow>run MODULE FUNCTION</ansiyellow>'))
            return
        
        module_name = args[0]
        if module_name not in self.mm.list_modules():
            print_formatted_text(HTML('<ansired>Error: Invalid module "{}"</ansired>'.format(module_name)))
            return
        
        module = self.mm[module_name]
        function = args[1]
        # Special function "help" lists all available functions
        if function == "help":
            rows = []
            for function in module.__FUNCS__.keys():
                description = ""
                if "_desc" in module.__FUNCS__[function]:
                    description = module.__FUNCS__[function]['_desc']
                rows.append([function, description])
            print_table(rows, ["Functions", "Descriptions"])
        elif function in module.__FUNCS__.keys():
            # If there are not parameters, just run the function
            if len(module.__FUNCS__[function]) == 0 or len(module.__FUNCS__[function]) == 1 and "_desc" in module.__FUNCS__[function]:
                error, result = module.run(function)
                if error is None:
                    if 'rows' in result and 'columns' in result:
                        print_table(result['rows'], result['columns'])
                else:
                    print_formatted_text(HTML('<ansired>Error: {}</ansired>'.format(error)))
            else:
                show_name = module_name + '.' + function

                out = show_name
                if "_desc" in module.__FUNCS__[function]:
                    out += ": " + module.__FUNCS__[function]['_desc']

                print_formatted_text(HTML('<ansigreen>{}</ansigreen>'.format(out)))
                self.current_command = {
                    "module_name": module_name,
                    "display_name": show_name,
                    "function_name": function,
                    "function": module.__FUNCS__[function],
                    "vars":{

                    }
                }
        else:
            print_formatted_text(HTML('<ansired>Error: Invalid function "{}"</ansired>'.format(function)))

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-j', '--json', help='Run commands from a JSON file and go to the console')
    parser.add_argument('-s', '--server', help='Server to connect to (defaults to 127.0.0.1)')
    args = parser.parse_args()

    console = None
    if args.server:
        console = FakerNetConsole(ip=args.server)
    else:
        console = FakerNetConsole()

    
    if args.json:
        if os.path.exists(args.json):
            print("Running commands from file '{}'".format(args.json))
            json_file = open(args.json, "r")
            lines = json_file.read().split("\n")
            json_file.close()
            counter = 1
            for line in lines:
                line = line.strip()
                json_line = json.loads(line)
                
                error, result = console.mm.run_json_command(json_line)
                if error is not None:
                    print_formatted_text(HTML("<ansired>Line {} error: {}</ansired>".format(counter, error)))
                else:
                    console.print_result(error, result)
                counter += 1
        else:
            print_formatted_text(HTML("<ansired>!!! - ERROR: JSON file '{}' not found</ansired>".format(args.json)))
    console.start()

    
    
    print('Shutting down console...')

if __name__ == '__main__':
    main()