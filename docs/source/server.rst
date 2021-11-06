.. _server:

Server
=========

FakerNet has a web server that is run with the ``./fnserver`` command. This server can also be run as a service, which allows FakerNet services to started on boot.

Adding the Service 
^^^^^^^^^^^^^^^^^^^^^

If you used the install script, the service should be installed for you already. If not, for systemd-based distros, you can use the ``.service`` file template in the ``scripts`` directory.

Starting Servers On Boot 
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To restore services on-boot, you will need to create a default restore point. This can be done with the ``save`` command on the console. Once this is created, FakerNet will restore the running services to the up/down status when the ``save`` command was run.

Web Server 
^^^^^^^^^^^^^^^

The web server can be accessed on port ``5051`` using TLS from your browser. It provides both a simple web-based UI to interact with FakerNet, as well as a REST API. You will need to create users to access the web interface from anywhere but the local host. Authentication is currently done with HTTP basic authentication.

Users
----------

To add a user, you will need to open the console:

..  code-block::

    ./fnconsole 

Then, use the ``useradd`` command without any options, it will prompt for username and password for the new user. The password is hidden while typing it.

..  code-block::

    127.0.0.1> useradd
    username> testuser
    password> 
    password (again)>
    User Added

The user will be immediately available for use. You can add uses regardless of the server currently running or not. If the server is on, the console automatically communciates with it.

Web UI
--------

The web UI is fairly simple and minimalistic. It has three main pages:

* **Status**: This provides the current CPU, memory, and disk usage, as well as list of currently running servers.
* **Run**: This page allows you to call module functions. Select the module and function from the dropdowns, fill in the textboxes with the necessary options, then press ``Submit`` to run. The results will appear below the form.
* **API Docs**: This provides a `Swagger <https://swagger.io/docs/>`_ web interface to show the endpoints for the REST API. This page is fully interactive, allowing calls to the API to be performed right there.

Web API 
---------

FakerNet provides a REST API for your integration needs. This API is also used by the console when not in local mode and the Web UI. Reference the Swagger page on the web server for API documentation. 

