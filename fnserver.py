# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys 
import sqlite3
import sys
import logging

from flask import Flask, g, jsonify, current_app, request
from flask_httpauth import HTTPBasicAuth

from lib.module_manager import ModuleManager

from flask.logging import default_handler

def create_app():
    app = Flask(__name__)
    app.secret_key = 'aasdfasfd'

    with app.app_context():
        current_app.db = sqlite3.connect('fakernet.db')
        current_app.mm = ModuleManager(db=current_app.db)
        current_app.mm.load()

        fileLog = logging.FileHandler("./logs/fakernet-server.log")
        formatter = logging.Formatter('%(asctime)s %(levelname)s SERVER : %(message)s')
        fileLog.setFormatter(formatter)


        app.logger.addHandler(fileLog)
        app.logger.setLevel(logging.INFO)
        

        current_app.mm['init'].check()
        if current_app.mm['init'].init_needed:
            error_message = "FakerNet is not yet configured. Please run `fnconsole` first to configure your setup."
            print(error_message)
            app.logger.error(error_message)
            sys.exit()


        app.logger.info("Restoring services")
        error, _ = current_app.mm.restore_state(save_name="default")
        if error is not None:
            print(error)
            app.logger.error(error)
            sys.exit(1)
        
        app.logger.info("Server started")

    return app

app = create_app()
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if request.remote_addr == "127.0.0.1":
        app.logger.warning("Accessed from localhost, bypassing authentication!")
        return "ok"
    error, _ = current_app.mm.check_user(username, password)
    if not error:
        app.logger.warning("User %s logged in successfully", username)
        return username


@app.route('/')
@auth.login_required
def authenticate():
    return {
        "ok": True,
        "result": 'g.csrf_token'
    }

@app.route('/api/v1/<module_name>/run/<function>', methods = ['POST'])
@auth.login_required
def run_command(module_name, function):
    
    if not module_name in current_app.mm.list_modules():
        return jsonify({"ok": False, "error": "Invalid module"})
    
    fnmodule = current_app.mm[module_name]

    if function not in fnmodule.__FUNCS__:
        return jsonify({"ok": False, "error": "Invalid function"})

    

    # Check if a no-parameter function
    if len(fnmodule.__FUNCS__[function]) == 0 or len(fnmodule.__FUNCS__[function]) == 1 and "_desc" in fnmodule.__FUNCS__[function]:
        app.logger.info("%s called %s.%s, args=", request.remote_addr, module_name, function)
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

        app.logger.info("%s called %s.%s, args=%s", request.remote_addr, module_name, function, str(args))

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
@auth.login_required
def get_module_list():
    return_data = {}

    for module_name in current_app.mm.list_modules():
        return_data[module_name] = current_app.mm[module_name].__FUNCS__

    return jsonify({
        "ok": True,
        "result": return_data
    })

@app.route('/api/v1/_servers/list_all', methods = ['GET'])
@auth.login_required
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
@auth.login_required
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
@auth.login_required
def restore_state(state_name):

    current_app.mm.restore_state(save_name=state_name)
    return jsonify({
        "ok": True,
        "result": True
    })

@app.route('/api/v1/_users/list', methods = ['GET'])
@auth.login_required
def list_users():

    error, user_list = current_app.mm.list_users()
    if error is not None:
        return jsonify({
            "ok": False,
            "error": error
        })
    return jsonify({
        "ok": True,
        "result": user_list
    })

@app.route('/api/v1/_users/add', methods = ['POST'])
@auth.login_required
def add_user():

    if not "username" in request.form or not "password" in request.form:
        return jsonify({
            "ok": False,
            "error": "'username' and 'password' are required"
        })

    if request.remote_addr != "127.0.0.1":
        app.logger.error("Remote system attempted to add user: %s", request.remote_addr)
        return jsonify({
            "ok": False,
            "error": "Users can only be added locally"
        })

    error, result = current_app.mm.add_user(request.form['username'], request.form['password'])
    if error is not None:
        return jsonify({
            "ok": False,
            "error": error
        })
    return jsonify({
        "ok": True,
        "result": result
    })

if __name__== '__main__':
    app.run()