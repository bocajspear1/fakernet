import shlex
import textwrap
import sys

from prompt_toolkit import PromptSession, prompt, print_formatted_text, HTML 
from prompt_toolkit.completion import Completer, Completion

from lib.module_manager import ModuleManager
import lib.validate
import lib.prompt_builder as prompt_builder

import tableprint as tp




base_net = None
dns_ip = None


    # base_net = prompt_builder.prompt_get_network(premessage="Welcome to FakerNet, it appears we need to do some setup...\n\nPlease enter the initial network allocation. The main DNS server will be hosted here.")

    # err, result = self.mm['netreserve'].run("add_network", net_addr=base_net, description="The central network for Fakernet. Hosts central DNS server and other critical services.")
    # if err is None:
    #     done = True
    #     print("Network: " + base_net)
    # else:
    #     print(err)

    # print("\nEnter the IP of the main DNS server. This will be the resolver for your FakerNet instance.")
    # print("You will need to point all systems to this DNS server for things to work.")

    # dns_ip = prompt_builder.prompt_get_ip_in_network(base_net)

    # if dns_ip is not None:
    #     err, result = self.mm['ipreserve'].run("add_ip", ip=dns_ip, description="Central DNS server")
    #     if err is None:
    #         done = True
    #         print("DNS IP: " + dns_ip)
    #     else:
    #         print(err)

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

    def __init__(self, mm, global_vars, run_mode=False):
        super().__init__()
        self.mm = mm
        self.global_vars = global_vars
        self.run_mode = run_mode
        self.run_options = {}

    MAIN_COMMANDS = [
        'run',
        'global',
        'uglobal',
        'exit',
        'stats'
    ]

    RUN_COMMANDS = [
        'run',
        'set',
        'unset',
        'execute',
        'info',
        'show',
        'back',
        'global',
        'uglobal',
    ]

    def get_completions(self, document, complete_event):
        command_string = document.text
        if " " not in command_string:
            command_list = self.MAIN_COMMANDS
            if self.run_mode:
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
            elif (command == "set" or command == "unset") and self.run_mode == True:
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

    def __init__(self):

        self.mm = ModuleManager()
        self.mm.load()

        self.session = PromptSession()
        self.global_vars = {
            "AUTO_ADD": False
        }
        self.completer = CommandCompleter(self.mm, self.global_vars)

        err, _ = self.mm['init'].run("verify_permissions")
        if err is not None:
            print_formatted_text(HTML('<ansired>{}</ansired>'.format(err)))
            sys.exit(1)

        print_formatted_text(HTML('<ansigreen>{}</ansigreen>'.format(ASCIIART)))
        print_formatted_text(HTML('<skyblue>Internet-in-a-box\n</skyblue>'))

        if self.mm['init'].init_needed:
            self.setup_prompts()

        self.running = True
        self.current_command = None

    def setup_prompts(self):
        pass
    
    def start(self):
        while self.running:
            try:
                prompt = '> '
                if self.current_command is not None:
                    self.completer.run_mode = True
                    self.completer.run_options = self.current_command['function']
                    prompt = self.current_command['display_name'] + '> '

                command_string = self.session.prompt(prompt, completer=self.completer)

                command_split = []
                try:
                    command_split = shlex.split(command_string)
                except ValueError:
                    print_formatted_text(HTML('<ansired>Invalid quotes or command</ansired>'))

                if len(command_split) > 0:
                    if self.current_command is not None:
                        self.run_mode(command_split)
                    else:
                        self.main_mode(command_split)
            
            except KeyboardInterrupt:
                self.running = False
            except EOFError:
                pass

    def main_mode(self, command_input):
        command = command_input[0].lower()
        if command == "exit":
            self.running = False
        elif command == "run":
            self.command_run(command_input[1:])
        elif command == "global":
            pass
        elif command == "uglobal":
            pass
        else:
            print_formatted_text(HTML('<ansired>Error: Invalid command "{}"</ansired>'.format(command)))

    def run_mode(self, command_input):
        command = command_input[0].lower()
        if command == "exit":
            self.current_command = None
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
            
            error, result = self.mm[module_name].run(function_name, **self.current_command['vars'])
            if error is not None:
                print_formatted_text(HTML('<ansired>Error: {}</ansired>'.format(error)))
            else:
                if isinstance(result, dict) and 'rows' in result and 'columns' in result:
                    print_table(result['rows'], result['columns'])
                else:
                    print_formatted_text(HTML('<ansigreen>OK</ansigreen>'))

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
                if 'rows' in result and 'columns' in result:
                    print_table(result['rows'], result['columns'])
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
    console = FakerNetConsole()
    console.start()
    print('Shutting down console...')

if __name__ == '__main__':
    main()