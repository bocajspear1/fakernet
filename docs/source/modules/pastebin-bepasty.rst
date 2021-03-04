.. _module-pastebin-bepasty:

pastebin-bepasty
================

    
list
^^^^

View all Bepasty servers

add_server
^^^^^^^^^^

Delete a pastebin server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

remove_server
^^^^^^^^^^^^^

Remove a Pastebin server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

start_server
^^^^^^^^^^^^

Start a pastebin server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Stop a pastebin server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

