import sys 
import sqlite3
import sys

from flask import Flask, g, jsonify, current_app, request

from lib.module_manager import ModuleManager

def create_app():
    app = Flask(__name__)

    with app.app_context():
        current_app.db = sqlite3.connect('fakernet.db')
        current_app.mm = ModuleManager(db=current_app.db)
        current_app.mm.load()

        current_app.mm['init'].check()
        if current_app.mm['init'].init_needed:
            print("FakerNet is not yet configured. Please run `fnconsole` first to configure your setup.")
            sys.exit()

        error, _ = current_app.mm.restore_state(save_name="default")
        if error is not None:
            print(error)
            sys.exit(1)

    return app

app = create_app()

@app.route('/')
def authenticate():
    return 'FakerNet API'

@app.route('/api/v1/<module_name>/run/<function>', methods = ['POST'])
def run_command(module_name, function):
    if not module_name in current_app.mm.list_modules():
        return jsonify({"ok": False, "error": "Invalid module"})
    
    fnmodule = current_app.mm[module_name]

    if function not in fnmodule.__FUNCS__:
        return jsonify({"ok": False, "error": "Invalid function"})

    # Check if a no-parameter function
    if len(fnmodule.__FUNCS__[function]) == 0 or len(fnmodule.__FUNCS__[function]) == 1 and "_desc" in fnmodule.__FUNCS__[function]:
        error, result = fnmodule.run(function)
        if error is None:
            return jsonify({
                "ok": True,
                "result": result
            }) 
        else:
            return jsonify({"ok": False, "error": error})
    else:
        args = {}
        for item in request.form:
            args[item] = request.form[item]

        error, result = fnmodule.run(function, **args)
        if error is None:
            return jsonify({
                "ok": True,
                "result": result
            }) 
        else:
            return jsonify({"ok": False, "error": error})
    
    return jsonify({"ok": True})

@app.route('/api/v1/_modules/list', methods = ['GET'])
def get_module_list():
    return_data = {}

    for module_name in current_app.mm.list_modules():
        return_data[module_name] = current_app.mm[module_name].__FUNCS__

    return jsonify({
        "ok": True,
        "result": return_data
    })

@app.route('/api/v1/_servers/list_all', methods = ['GET'])
def list_servers():

    error, server_list = current_app.mm.list_all_servers()
    if error is not None:
        return jsonify({
            "ok": False,
            "error": error
        })
    return jsonify({
        "ok": True,
        "result": server_list
    })

@app.route('/api/v1/_servers/save_state/<state_name>', methods = ['GET'])
def save_state(state_name):

    error, status = current_app.mm.save_state(save_name=state_name)
    if error is not None:
        return jsonify({
            "ok": False,
            "error": error
        })
    return jsonify({
        "ok": True,
        "result": status
    })

@app.route('/api/v1/_servers/restore_state/<state_name>', methods = ['GET'])
def restore_state(state_name):

    current_app.mm.restore_state(save_name=state_name)
    return jsonify({
        "ok": True,
        "result": True
    })


if __name__== '__main__':
    app.run()