.. _network-design:

Network Design
==============

When using FakerNet, you will need to consider how hosts will integrate and utilize FakerNet services, as well as if and how FakerNet users will get further real internet access.

Integration Methods
^^^^^^^^^^^^^^^^^^^^^

There are two main ways you can integrate FakerNet into your network infrastructure, as a Gateway or side-loaded into the network.

Gateway 
----------

The easiest method, and the recommended one, is to make the system the default gateway for the networks you want to connect to the fake internet. All hosts will sit behind the FakerNet host and route everything through it, including any access to the real internet. This strategy gives you the most control over access to the FakerNet systems and allows to you to redirect traffic to the FakerNet hosts. (This is especially useful to redirect DNS traffic.) Essentially, FakerNet works like your ISP.

Side-loaded
------------

Another method is utilize routing protocols to add the FakerNet networks to your existing routing infrastructure. You can use the Quagga that is installed for FakerNet or another method to add FakerNet's routes so that systems can access FakerNet systems. Setting up these routes goes beyond the realm of this documentation.


DNS Requirements 
^^^^^^^^^^^^^^^^^

To take full advantage of FakerNet, hosts should point to, directly or indirectly, to the FakerNet main DNS server (the one created during setup). Either hosts should have it configured as its only primary DNS server (don't use other DNS servers, which might cause inconsistent DNS responses), or point to a DNS that utilizes the FakerNet DNS server. If you have the FakerNet host as the default gateway, you can also use the ``redirect`` module to force all DNS queries to the FakerNet primary DNS server.

Real Internet Access
^^^^^^^^^^^^^^^^^^^^^

Depending on your setup, you may or may not want access to real Internet resources in your environment.

No Internet
--------------

This can be simply done by using the Gateway method without connecting the FakerNet host to any further networks. The networking will end with the FakerNet host and all hosts in your environment will only have access to the FakerNet "internet." With this setup, you are free to use any IP ranges (including real public ranges) as you want, as well as any root DNS names you want. For example, you could configure FakerNet systems in the ``8.8.8.0/24``, which would normally contain Google's public DNS, and use ``.com`` domains.

If the FakerNet host is connected to an external network for maintenance and access purposes, without any NAT rules, hosts will not be able to reach outside the FakerNet box. Some packets will reach out, since routing is enabled on the FakerNet host, but not be able to return due to a lack of NAT. For added safety and to stop these outbound packets, you can utilize ``iptables`` to block outbound traffic from the internal networks. 

"Extended" Internet
---------------------

If you are using the "side-load" method, this is practically the access already available. When using the gateway method, this can be achieved by adding NAT rules for the external interface, which can be done with the :ref:`module-iptables` module. For example, if the external interface is ``ens18``, and you want to allow all ranges:

..  code-block::

    local> run iptables set_external_iface
    local(iptables.set_external_iface)> set iface ens18
    local(iptables.set_external_iface)> execute
    OK
    local(iptables.set_external_iface)> run iptables add_nat_allow
    local(iptables.add_nat_allow)> set range *
    local(iptables.add_nat_allow)> execute
    OK

If you want only certain networks to be restricted from internet access, you could limit certain ranges. For example, the following will allow all other ranges except the ``10.88.50.0/24`` network (perhaps that is your internal network connected to lab devices):

..  code-block::

    > run iptables add_nat_allow
    local(iptables.add_nat_allow)> set range !10.88.50.0/24
    local(iptables.add_nat_allow)> execute
    OK

A few other things should be kept in mind:

* The primary FakerNet DNS should be configured with forwarders so it can resolve external addresses. Note that misspelled or misconfigured DNS names may be sent to these forwarders.
* You will only be able to use private IP ranges in FakerNet, otherwise you risk making parts of the real internet unaccessible.
* You will only be able to use unused/test root DNS names, such as ``fake`` or ``test``. Using root names like ``com`` risk making large swathes of the internet unaccessible.


Proxied Internet
--------------------

This method, only possible when using FakerNet as a gateway, limits internet access to select hosts. This is done by restricting the NAT rules to certain hosts, such as an instance of the ``tinyproxy`` FakerNet module. 

For example, if the ``tinyproxy`` instance is at ``10.10.10.2``, configure it alone be to allowed through NAT (given you haven't used the rules above):

..  code-block::

    > run iptables add_nat_allow
    local(iptables.add_nat_allow)> set range 10.10.10.2
    local(iptables.add_nat_allow)> execute
    OK

You can utilize the :ref:`module-iptables` module to create a wide-range of configurations using the ``add_raw`` and ``add_raw_to_table``.
