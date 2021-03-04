.. _services-tutorials:

Services Tutorials
==================

These tutorials will help you get started building services with FakerNet.

.. contents:: Contents
   :depth: 2


External DNS Resolution
-----------------------

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