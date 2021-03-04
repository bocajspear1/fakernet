.. _module-lxd:

lxd
===

    
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



