import shlex
import textwrap

from prompt_toolkit import PromptSession, prompt, print_formatted_text, HTML 
from prompt_toolkit.completion import Completer, Completion

from lib.module_manager import ModuleManager
import lib.validate
import lib.prompt_builder as prompt_builder

import tableprint as tp


manager = ModuleManager()
manager.load()

base_net = None
dns_ip = None

# Check for init
if manager['init'].init_needed:


    base_net = prompt_builder.prompt_get_network(premessage="Welcome to FakerNet, it appears we need to do some setup...\n\nPlease enter the initial network allocation. The main DNS server will be hosted here.")

    err, result = manager['netreserve'].run("add_network", net_addr=base_net, description="The central network for Fakernet. Hosts central DNS server and other critical services.")
    if err is None:
        done = True
        print("Network: " + base_net)
    else:
        print(err)

    print("\nEnter the IP of the main DNS server. This will be the resolver for your FakerNet instance.")
    print("You will need to point all systems to this DNS server for things to work.")

    dns_ip = prompt_builder.prompt_get_ip_in_network(base_net)

    if dns_ip is not None:
        err, result = manager['ipreserve'].run("add_ip", ip=dns_ip, description="Central DNS server")
        if err is None:
            done = True
            print("DNS IP: " + dns_ip)
        else:
            print(err)

    



modules_loaded = manager.list_modules()

def print_table(data, headers):
    widths = []
    row_len = len(data[0])

    for i in range(row_len):
        longest = 0
        for row in data:
            longest = max(len(str(row[i])), longest)
        longest = max(len(str(headers[i])), longest)
        widths.append(longest)

    tp.table(data, headers, width=widths)

class CommandCompleter(Completer):

    def __init__(self, mm, vars):
        super().__init__()
        self.mm = mm
        self.vars = vars

    MAIN_COMMANDS = [
        'run',
        'global',
        'uglobal',
        'exit'
    ]

    def get_completions(self, document, complete_event):
        command_string = document.text
        if " " not in command_string:
            for command in self.MAIN_COMMANDS:
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
                    module = manager[module_name]
                    pos = -(document.cursor_position)+len(command)+2+len(module_name)
                    all_entries = list(module.__FUNCS__.keys())
                    all_entries.append("help")
                    for func in all_entries:
                        if in_function == "" or func.startswith(in_function):
                            yield Completion(func, start_position=pos)
                else:
                    return
            else:
                return

def main():
    session = PromptSession()
    prompt_vars = {

    }
    completer = CommandCompleter(manager, prompt_vars)

    running = True
    current_command = None
    while running:
        
        try:
            if current_command is None:
                command_string = session.prompt('> ', completer=completer)

                command_split = []
                try:
                    command_split = shlex.split(command_string)
                except ValueError:
                    print_formatted_text(HTML('<ansired>Could not parse</ansired>'))

                if len(command_split) > 0:
                    command = command_split[0].lower()
                    if command == "exit":
                        running = False
                    elif command == "run":
                        if len(command_split) < 3:
                            print_formatted_text(HTML('<ansiyellow>run MODULE FUNCTION</ansiyellow>'))
                            continue
                        module_name = command_split[1]
                        if module_name not in manager.list_modules():
                            print_formatted_text(HTML('<ansired>Error: Invalid module "{}"</ansired>'.format(module_name)))
                        else:
                            module = manager[module_name]
                            function = command_split[2]
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
                                    print_formatted_text(HTML('<ansigreen>{}</ansigreen>'.format(show_name)))
                                    # current_command = {
                                    #     show_name: module.__FUNCS__[function]
                                    # }
                            else:
                                print_formatted_text(HTML('<ansired>Error: Invalid function "{}"</ansired>'.format(function)))
            
        except KeyboardInterrupt:
            running = False
        except EOFError:
            break

    print('Shutting down console...')

if __name__ == '__main__':
    main()