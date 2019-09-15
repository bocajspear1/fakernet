import sys
import os 
from datetime import datetime
import markdown

import_path = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + "/../")
sys.path.append(import_path)

from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(
    loader=PackageLoader('docs', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

from lib.module_manager import ModuleManager

manager = ModuleManager()
manager.load()

modules = manager.list_modules()

for mod_name in modules:
    module = manager[mod_name]

    functions = {}

    for function in module.__FUNCS__:
        description = module.__FUNCS__[function]['_desc']
        del module.__FUNCS__[function]['_desc']
        args = module.__FUNCS__[function]
        if len(args.keys()) == 0:
            args = None
        functions[function] = {
            "args": module.__FUNCS__[function],
            "description": description
        }

    details = "Not set"

    details_path = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + "/modules") + "/{}.md".format(mod_name)
    if os.path.exists(details_path):
        details_file = open(details_path).read()
        details = markdown.markdown(details_file)

    last_edit_seconds = os.path.getmtime(sys.modules[module.__class__.__module__].__file__)
    last_edit = datetime.fromtimestamp(last_edit_seconds).strftime("%B %m, %Y")
    
    template = env.get_template('page.html')
    template_output = template.render(
        module_name=module.__SHORTNAME__, 
        links=modules, 
        short_desc=module.__DESC__, 
        functions=functions,
        author=module.__AUTHOR__,
        last_edit=last_edit,
        details=details
    )

    outfile = open(os.path.dirname(os.path.abspath(__file__)) + "/out/{}.html".format(module.__SHORTNAME__), "w+")
    outfile.write(template_output)
    outfile.close()
