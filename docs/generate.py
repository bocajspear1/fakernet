import os 
import sys

import importlib

os.chdir(os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + "/../"))
sys.path.append(os.getcwd())

modules = {}

module_list = os.listdir("./modules")
for module in module_list:
    if not module.endswith(".py"):
        continue
    temp = importlib.import_module("modules." + module.replace(".py", ""))
    shortname = temp.__MODULE__.__SHORTNAME__

    modules[shortname] = temp

    output_page = """.. _module-{}:

{}
{}

    \n""".format(shortname, shortname, "="*len(shortname))

    long_desc_path = "./docs/source/_mod_long/{}.rst".format(shortname)
    if os.path.exists(long_desc_path):
        long_desc_file = open(long_desc_path, "r")
        output_page += long_desc_file.read()
        long_desc_file.close()
    
    functions = {}

    function_list = temp.__MODULE__.__FUNCS__

    for function in function_list:
        description = function_list[function]['_desc']
        del function_list[function]['_desc']
        args = function_list[function]
        if len(args.keys()) == 0:
            args = None
        functions[function] = {
            "args": function_list[function],
            "description": description
        }
    

    for function in functions:
        output_page += "{}\n{}\n\n{}\n\n".format(function, "^"*len(function), functions[function]['description'])
        if len(functions[function]['args']) > 0:

            output_page += "..  csv-table:: Parameters\n"
            output_page += "    :header: \"Name\", \"Type\"\n\n"

            for arg in functions[function]['args']:
                output_page += '    "{}","{}"\n'.format(arg, functions[function]['args'][arg])
                
            output_page += "\n"


    module_list_file = open("./docs/source/modules/{}.rst".format(shortname), "w+")
    module_list_file.write(output_page)
    module_list_file.close()

    modpage_header = """.. _modules:

Modules
========

The following is the currently available FakerNet modules.

..  toctree::
    :maxdepth: 1
    :caption: Modules:

"""

for mod in modules:
    modpage_header += "    modules/{}\n".format(mod)

module_list_file = open("./docs/source/modules.rst", "w+")
module_list_file.write(modpage_header)
module_list_file.close()