.. _module-mattermost:

mattermost
==========

    
list
^^^^

View all Mattermost servers

remove_server
^^^^^^^^^^^^^

Delete a Mattermost server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_server
^^^^^^^^^^

Add a Mattermost server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

start_server
^^^^^^^^^^^^

Start a Mattermost server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Stop a Mattermost server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

