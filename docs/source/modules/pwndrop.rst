.. _module-pwndrop:

pwndrop
=======

    
A file-hosting application oriented to delivering attack payloads.

Made by Kuba Gretzky and on `GitHub <https://github.com/kgretzky/pwndrop>`_.

See :ref:`param-types` for parameter types.

list
^^^^

View all pwndrop servers

remove_server
^^^^^^^^^^^^^

Delete a pwndrop server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_server
^^^^^^^^^^

Add a pwndrop server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

start_server
^^^^^^^^^^^^

Start a pwndrop server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Stop a pwndrop server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

