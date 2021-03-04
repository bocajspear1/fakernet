Getting Started 
================

This guide will help you through the steps of getting started with FakerNet. By the time you've completed the tasks here, you should have a working instance of FakerNet.

Network Design
--------------

The goal of FakerNet is to make it easy to create internet-like services, meaning we want whole networks to be able to use the services and servers FakerNet builds. While testing, you can just access the services from the host system but for other systems, the easiest way to use FakerNet-build services is to set the FakerNet host as the default gateway for the network. This makes it very simple for hosts to access what FakerNet builds. 

For more details and information on more complex FakerNet setups, refer to :ref:`network-design` for more details. 

Installing
-----------

Once you've determined the FakerNet host's place in the network, you can move onto :ref:`installation`.

..  note::
    Be sure you have built the Docker and LXD images before you continue!

First Run
----------

The first thing you need to do after installing FakerNet is perform a first-run configuration. This consists of getting the basic services built:

* A DNS server (the central server that all other FakerNet systems by default will forward to and yours should too)
* A MiniCA instance to generate certificates for other services.

Starting this process is as sample as running the console:

..  code-block::

    ./fnconsole 

This starts the console, which recognizes that its the first run. It will prompt you for a few things:

* A network address for the services to run on. Enter in the format ``X.X.X.X/PREFIX``.
* The root-level domain for you fake internet services. This could be ``fake`` or ``test``. This will be the root-level domain for all your services, so for example, if you put ``test``, the certificate authority server will have the domain ``ca.test`` assigned to it automatically.
* The network address for the main DNS server
* The network address for the main certificate authority server

Once this is done, these services will be automatically built and configured and you will be put on the FakerNet console. Type ``exit`` if you want to exit. Other services you build will utilize these two initial services for DNS and certificates.

Configuring Other Hosts
-----------------------

If you have the FakerNet host as the default gateway, all hosts that use the gateway should be able to access FakerNet servers automatically. If not, you need to make sure that your network can route requests to the FakerNet host.

Regardless, you'll need to configure your hosts to use the main DNS server (the one built during First Run) for their domain server. This allows them to resolve FakerNet domains.

Starting Using FakerNet
-----------------------

Now that you've gotten FakerNet installed and configured, you can begin to use it to build services and servers and have your network access them. 

* If you're looking for quick tutorials on how to build services, check out the :ref:`services-tutorials`.
* For a overview of how you interact with FakerNet, check out :ref:`using-fakernet` then the :ref:`cli-usage`.
