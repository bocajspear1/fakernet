.. _module-minica:

minica
======

    
MiniCA is a small, Go-based CA web application used to generate certificates for FakerNet services. It has a single password as its authentication, so don't use this in any production system or untrusted network.

The password for creating certs is located in ``work/minica/<SERVER_ID>/ca.pass`` externally or ``/etc/minica/certs/ca.pass`` in the container.

The web interface is available as HTTPS (signed by itself) at the container's IP address. You'll need to upload a CSR and enter the CA password.

Source for the CA server is available on `GitHub <https://github.com/bocajspear1/minica>`_.

See :ref:`param-types` for parameter types.

list
^^^^

View all CA servers

remove_server
^^^^^^^^^^^^^

Delete a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_server
^^^^^^^^^^

Add a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

get_server
^^^^^^^^^^

Get info on a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

generate_host_cert
^^^^^^^^^^^^^^^^^^

Generate a key and signed certificate

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "fqdn","TEXT"

get_ca_cert
^^^^^^^^^^^

Get a server's CA cert

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "type","TEXT"

start_server
^^^^^^^^^^^^

Start a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Stop a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

