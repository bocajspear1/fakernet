.. _module-lxd:

lxd
===

    
This module manages LXD containers, which provide a more VM-like experience as compared to the Docker containers most services are in.

The hostname and container name is the ``fqdn`` with the dots replaced with dashes.

LXD addresses are set manually by FakerNet on start, so if you start the container outside FakerNet you will not get your address properly. (This is due to the built in LXD network management utilizing DHCP, which caused limitations). Configuring the container to have a static IP through its own startup scripts is currently left up to the user, as supporting all the different methods of setting a static IP in the container would be a real pain.


See :ref:`param-types` for parameter types.

list
^^^^

View containers

add_container
^^^^^^^^^^^^^

Add a new container

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP_ADDR"
    "password","PASSWORD"
    "template","TEXT"

remove_container
^^^^^^^^^^^^^^^^



..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

start_container
^^^^^^^^^^^^^^^



..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_container
^^^^^^^^^^^^^^



..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

list_templates
^^^^^^^^^^^^^^

List available LXD templates

add_template
^^^^^^^^^^^^

Add template by image name

..  csv-table:: Parameters
    :header: "Name", "Type"

    "image_name","TEXT"
    "template_name","TEXT"

remove_template
^^^^^^^^^^^^^^^

Remove template by ID

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

