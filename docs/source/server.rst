.. _server:

Server
=========

FakerNet has a web server that is run with the ``./fnserver`` command. This server can also be run as a service, which allows FakerNet services to started on boot.

Adding the service 
^^^^^^^^^^^^^^^^^^^^^

If you used the install script, the service should be installed for you already. If not, for systemd-based distros, you can use the ``.service`` file template in the ``scripts`` directory.

Configuring On Boot 
^^^^^^^^^^^^^^^^^^^^^

To restore services on-boot, you will need to create a default restore point. This can be done with the ``save`` command on the console. Once this is created, FakerNet will restore the running service to the configuration when the ``save`` command was run.

Web API 
^^^^^^^^^^^^^^^^^^^^^

FakerNet provides a web API for your integration needs. This API is also used by the console when not in local mode, and the Web UI. For any remote access, 

