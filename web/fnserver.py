# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys 
import sqlite3
import sys
import logging
import platform
import os

from flask import Flask, g, jsonify, current_app, request, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth

import psutil

from lib.module_manager import ModuleManager
from lib.version import FAKERNET_VERSION

from flask.logging import default_handler

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ['FLASK_KEY']

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
        
        app.logger.info("Server %s started", FAKERNET_VERSION)

    return app

app = create_app()
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if request.remote_addr == "127.0.0.1":
        # app.logger.warning("Accessed from localhost, bypassing authentication!")
        return "ok"
    error, _ = current_app.mm.check_user(username, password)
    if not error:
        # app.logger.warning("User %s logged in successfully", username)
        return username

@app.route('/apidoc/<path>')
def download_file(path):
    return send_from_directory('swagger', path)

@app.route('/')
@auth.login_required
def authenticate():
    return render_template('index.html', version=FAKERNET_VERSION)

@app.route('/status')
@auth.login_required
def status():
    return render_template('status.html', version=FAKERNET_VERSION)

@app.route('/run')
@auth.login_required
def run_module():
    return render_template('run.html', version=FAKERNET_VERSION)

@app.route('/api/v1/_system_data')
@auth.login_required
def status_data():
    system_info = "{} - {} {}".format(platform.node(), platform.system(), platform.release())
    memory = psutil.virtual_memory() 
    main_disk = psutil.disk_usage('/')
    return {
        "ok": True,
        "result": {
            "system": system_info,
            "memory_used": memory.used,
            "memory_total": memory.total,
            "cpu_percent": psutil.cpu_percent(interval=.5),
            "disk_used": main_disk.used,
            "disk_total": main_disk.total
        }
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
                "result": {
                    "output": result
                }
            }) 
        else:
            return jsonify({"ok": False, "error": error})
    else:
        args = {}
        json_data = request.get_json()
        if json_data is not None:
            for item in json_data:
                args[item] = json_data[item]
        else:
            for item in request.form:
                args[item] = request.form[item]

        app.logger.info("%s called %s.%s, args=%s", request.remote_addr, module_name, function, str(args))

        error, result = fnmodule.run(function, **args)
        if error is None:
            return jsonify({
                "ok": True,
                "result": {
                    "output": result
                }
            }) 
        else:
            return jsonify({"ok": False, "error": error})
    
    return jsonify({"ok": True})

@app.route('/api/v1/_version')
@auth.login_required
def version():
    return jsonify({
        "ok": True,
        "result": {
            "version": FAKERNET_VERSION
        }
    })

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
        "result": {
            "servers": server_list
        }
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
        "result": {
            "status": status
        } 
    })

@app.route('/api/v1/_servers/restore_state/<state_name>', methods = ['GET'])
@auth.login_required
def restore_state(state_name):

    current_app.mm.restore_state(save_name=state_name)
    return jsonify({
        "ok": True,
        "result": {
            "status": True
        } 
    })


@app.route('/api/v1/_users', methods = ['PUT', 'GET', 'DELETE'])
@auth.login_required
def user_manage():

    if request.remote_addr != "127.0.0.1" and request.method != 'GET':
        app.logger.error("Remote system attempted to modify user: %s", request.remote_addr)
        return jsonify({
            "ok": False,
            "error": "Users can only be modified locally"
        })

    if request.method == 'GET':
        error, user_list = current_app.mm.list_users()
        if error is not None:
            return jsonify({
                "ok": False,
                "error": error
            })
        return jsonify({
            "ok": True,
            "result": {
                "users": user_list
            }
        })
    elif request.method == 'PUT':
        if not "username" in request.form or not "password" in request.form:
            return jsonify({
                "ok": False,
                "error": "'username' and 'password' are required"
            })
        error, result = current_app.mm.add_user(request.form['username'], request.form['password'])
        if error is not None:
            return jsonify({
                "ok": False,
                "error": error
            })
        return jsonify({
            "ok": True,
            "result": {
                "status": result
            }
        })
    elif request.method == 'DELETE':
        if not "username" in request.form:
            return jsonify({
                "ok": False,
                "error": "'username' are required"
            })
        error, result = current_app.mm.remove_user(request.form['username'])
        if error is not None:
            return jsonify({
                "ok": False,
                "error": error
            })
        return jsonify({
            "ok": True,
            "result": {
                "status": result
            }
        })
    

if __name__== '__main__':
    app.run()