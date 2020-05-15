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

INFO_PAGES_PATH = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + "/pages")
info_pages = os.listdir(INFO_PAGES_PATH)

info_links = []

for page in info_pages:
    if ".md" in page:
        info_page_data = open(INFO_PAGES_PATH + "/" + page, "r").read()
        title = info_page_data.strip().split("\n")[0].replace("#", "").strip()
        out_page = page.replace(".md", ".html")
        info_links.append({"title": title, "link": out_page})

for page in info_pages:
    if ".md" in page:
        info_page_data = open(INFO_PAGES_PATH + "/" + page, "r").read()
        title = info_page_data.strip().split("\n")[0].replace("#", "").strip()
        out_page = page.replace(".md", ".html")

        contents = markdown.markdown(info_page_data, extensions=["fenced_code"])

        contents = contents.replace("<code class=\"python\">", "")
        contents = contents.replace("<code>", "")
        contents = contents.replace("</code>", "")

        template = env.get_template('info_page.html')
        template_output = template.render(
            title=title, 
            module_links=modules, 
            info_links=info_links,
            contents=contents
        )

        outfile = open(os.path.dirname(os.path.abspath(__file__)) + "/out/{}".format(out_page), "w+")
        outfile.write(template_output)
        outfile.close()


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
    
    template = env.get_template('module_page.html')
    template_output = template.render(
        module_name=module.__SHORTNAME__, 
        module_links=modules, 
        info_links=info_links,
        short_desc=module.__DESC__, 
        functions=functions,
        author=module.__AUTHOR__,
        last_edit=last_edit,
        details=details
    )

    outfile = open(os.path.dirname(os.path.abspath(__file__)) + "/out/{}.html".format(module.__SHORTNAME__), "w+")
    outfile.write(template_output)
    outfile.close()