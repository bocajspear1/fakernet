.. _services-tutorials:

Services Tutorials
==================

These tutorials will help you get started building services with FakerNet.

.. contents:: Table of Contents
   :local:
   :depth: 2

Adding a Subdomain Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding a subdomain server is simply one module function in the FakerNet console.

First, open the console:

..  code-block::

    ./fnconsole

Then use the ``smart_add_subdomain_server`` function in the ``dns`` module:

..  code-block::

    run dns smart_add_subdomain_server

Set the options with the ``set`` command, ensure that there is a parent domain when you set the FQDN. For example, if you used ``test`` for the root domain, you can create a subdomain like the example:

..  code-block::

    local> run dns smart_add_subdomain_server
    dns.smart_add_subdomain_server: Add subdomain server, automatically setting up root server to point to it
    local(dns.smart_add_subdomain_server)> set fqdn subdomain.test
    local(dns.smart_add_subdomain_server)> set ip_addr 172.16.3.30
    
Then run ``execute``:

..  code-block::

    execute

Now, if you exit out of the console, you can use ``dig`` to see our server is set up:

..  code-block::

    $ dig @172.16.3.30 ns1.subdomain.test

    ; <<>> DiG 9.16.1-Ubuntu <<>> @172.16.3.30 ns1.subdomain.test
    ; (1 server found)
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 36394
    ;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

    ;; OPT PSEUDOSECTION:
    ; EDNS: version: 0, flags:; udp: 1232
    ; COOKIE: 50319db6aad37a7501000000617b6c62114c6943afdcc411 (good)
    ;; QUESTION SECTION:
    ;ns1.subdomain.test.            IN      A

    ;; ANSWER SECTION:
    ns1.subdomain.test.     604800  IN      A       172.16.3.30

    ;; Query time: 4 msec
    ;; SERVER: 172.16.3.30#53(172.16.3.30)
    ;; WHEN: Thu Oct 28 23:37:06 EDT 2021
    ;; MSG SIZE  rcvd: 91

We can also query the root domain server (the one set up in setup), for example, if you set the ip to ``172.16.3.2``:

..  code-block::

    $ dig @172.16.3.2 ns1.subdomain.test

    ; <<>> DiG 9.16.1-Ubuntu <<>> @172.16.3.2 ns1.subdomain.test
    ; (1 server found)
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 37913
    ;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

    ;; OPT PSEUDOSECTION:
    ; EDNS: version: 0, flags:; udp: 1232
    ; COOKIE: 4c9842f214f44d1201000000617b6c6cfd0cf3a1dffa30d6 (good)
    ;; QUESTION SECTION:
    ;ns1.subdomain.test.            IN      A

    ;; ANSWER SECTION:
    ns1.subdomain.test.     604790  IN      A       172.16.3.30

    ;; Query time: 0 msec
    ;; SERVER: 172.16.3.2#53(172.16.3.2)
    ;; WHEN: Thu Oct 28 23:37:16 EDT 2021
    ;; MSG SIZE  rcvd: 91

External DNS Resolution
^^^^^^^^^^^^^^^^^^^^^^^^

If you want your main DNS server to resolve external addresses, you'll need to configure forwarders for it.

First, open the console:

..  code-block::

    ./fnconsole

Then use the ``add_forwarder`` function in the ``dns`` module:

..  code-block::

    run dns add_forwarder

With the ``set`` command, configure the parameters (the ID of the main DNS server is 1):

..  code-block::

    set id 1
    set ip_addr <FORWARDER IP>

Then call ``execute`` to run the function:

..  code-block::

    execute

Creating a Mail Server
^^^^^^^^^^^^^^^^^^^^^^^^^

Creating a mail server is easy with the ``simplemail`` module. It sets up the needed DNS entries and uses RoundCube to provide web-based email access.

First, open the console:

..  code-block::

    ./fnconsole

Then use the ``add_server`` function in the ``dns`` module:

..  code-block::

    local> run simplemail add_server

Then we can set the necessary options:

* ``fqdn``: The full domain name of the mail server (like ``mail.domain.test``)
* ``mail_domain``: The domain the server will send and recieve mail for. This is the domain at the end of an email address. (like user@**domain.test**). This can be the same as the ``fqdn``.
* ``ip_addr``: The IP address of the mail server

For example:
..  code-block::

    local(simplemail.add_server)> set fqdn mail.test
    local(simplemail.add_server)> set mail_domain mail.test
    local(simplemail.add_server)> set ip_addr 172.16.3.32

    
Then run ``execute``:

..  code-block::

    local(simplemail.add_server)>  execute

You should get the output of ``OK`` if everything setup correctly.
