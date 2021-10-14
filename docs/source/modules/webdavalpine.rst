.. _module-webdavalpine:

webdavalpine
============

    
This module creates a Apache-based WebDAV server on an Alpine Linux instance. Public files are accessed at ``<SERVER>/files/public`` while other paths require credentials. A ``admin`` user is created on build and their password is located in the ``webdav`` subdirectory in the server's working directory. For example, with server with an ID of 1: ``work/webdavalpine/1/webdav/admin.pass``

References
""""""""""

* `Apache WebDAV Configuration <https://www.codeotaku.com/journal/2009-04/apache-webdav-configuration/index>`_
* `configure apache/webdav readonly for user x, read/write for user y <https://serverfault.com/questions/294386/configure-apache-webdav-readonly-for-user-x-read-write-for-user-y>`_

See :ref:`param-types` for parameter types.

list
^^^^

View all WebDAV servers

add_server
^^^^^^^^^^

Delete a WebDAV server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

remove_server
^^^^^^^^^^^^^

Remove a WebDAV server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

start_server
^^^^^^^^^^^^

Start a WebDAV server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Start a WebDAV server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

