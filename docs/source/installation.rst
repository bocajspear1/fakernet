.. _installation:

Installation 
============

.. warning:: 
   During installation, the current user (the one running FakerNet) will be given access to commands that can used to gain root privileges if given unfettered access on a shell.

.. contents:: Contents
   :depth: 3


Script Installation
-------------------

Ubuntu
^^^^^^
An installation script for Ubuntu (tested on Ubuntu 18.04) is available in `scripts/install_ubuntu.sh`


Now go to :ref:`firewall-rules` and :ref:`build-images`.

Manual Installation
-------------------


1. Install Dependencies
^^^^^^^^^^^^^^^^^^^^^^^ 

These are:

* LXD
* Open vSwitch
* Python 3.5 or higher, with pip and venv support
* git
* quagga routing services
* traceroute
* Python Development files (e.g. `python3-dev` on Ubuntu)

For Ubuntu, (which FakerNet has been tested on), this is the command: 


.. code-block:: 

   apt-get install git python3-venv python3-pip openvswitch-switch lxd quagga traceroute

2. Install Docker 
^^^^^^^^^^^^^^^^^

 Install Docker as indicated on their `website <https://docs.docker.com/install/linux/docker-ce/ubuntu/>`_.

3. Setup Groups
^^^^^^^^^^^^^^^


Ensure your user is in the following groups:

* ``lxd``
* ``docker``
* ``quaggavty``


.. note::
   Be sure to re-login so that group permissions come into effect.

4. Configure Docker
^^^^^^^^^^^^^^^^^^^^^^^^^

Edit Docker's configuration to do uid remapping and user namespaces. This is for both security and to allow mapping of configuration files in Docker containers. 

In `/etc/docker/daemon.json` add the following (the file usually needs to be made):

.. code-block::

  {
    "userns-remap": "default"
  }

Restart the Docker service, Docker will create the `dockremap` user and setup subuids properly.

5. Configure ID Mappings
^^^^^^^^^^^^^^^^^^^^^^^^

To ensure the root user in the containers maps to our current user that will run FakerNet, modify `/etc/[ug]id`. In both `/etc/subuid` and `/etc/subgid` set the following.afterwards:


.. code-block::

   dockremap:1000:1

Restart Docker

6. Configure ``sudo``
^^^^^^^^^^^^^^^^^^^^^

FakerNet needs to run certain commands as root to manage networking for the containers. To do this without running the entire framework as root, we can use `sudo` rules to give the current user access to the specific commands. These commands are:

  * ``ovs-vsctl``: For controlling Open vSwitch
  * ``ovs-docker``: For connecting Docker images to Open vSwitch switches
  * ``iptables``: For making automatic redirects
  * ``ip``: For controlling interfaces

..  code-block:: 

    # Example sudoers entries. Paths may differ in your case.
    user ALL=(ALL) NOPASSWD: /usr/bin/ovs-vsctl
    user ALL=(ALL) NOPASSWD: /usr/bin/ovs-docker
    user ALL=(ALL) NOPASSWD: /sbin/iptables
    user ALL=(ALL) NOPASSWD: /sbin/ip


.. warning:: 
   Note these commands can give the user root privileges (apart from the possibility for root privileges from Docker and LXD), so be aware of the user you are giving these controls to and restrict access to the account.


7. Get FakerNet 
^^^^^^^^^^^^^^^

..  note:: 
    If you haven't re-logged in to activated the new groups on the current user, do that now.

..  note::
    If you haven't configured LXD, run ``lxd init`` now as root. The defaults will usually suffice, but don't create a managed switch during LXD setup.

Git clone the FakerNet repo and enter the root directory:

..  code-block:: bash

    git clone https://github.com/bocajspear1/fakernet.git
    cd fakernet

8. Install Python Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a virtualenv and activate it, then install dependencies:

..  code-block:: bash

    python3 -m venv ./venv
    . ./venv/bin/activate
    pip3 install -r requirements.txt

.. _firewall-rules:

Firewall Rules
-----------------

Docker sets the default iptables forward rule to drop. To ensure external access to FakerNet services, add the following rules. Use something like ``iptables-persistent`` to manage your iptables and have them start on boot.

..  code-block:: bash

    sudo iptables -I FORWARD -i <INTERNAL_INTERFACE> -j ACCEPT
    sudo iptables -I FORWARD -o <INTERNAL_INTERFACE> -j ACCEPT
    sudo iptables -I FORWARD -i <EXTERNAL_INTERFACE> -j ACCEPT
    sudo iptables -I FORWARD -o <EXTERNAL_INTERFACE> -j ACCEPT
    # If you want NAT for services to have external Internet access
    sudo iptables -t nat -I POSTROUTING 1 -o <EXTERNAL_INTERFACE> -j MASQUERADE

.. _build-images:

Build Docker and LXD Images
---------------------------

Once everything is installed, you'll need to tell FakerNet to build the necessary Docker and LXD images. By pre-building the base images, this allows FakerNet to be portable into internet-restricted environments after the installation process is complete.

Run the build process using the following commands:

..  code-block::

    . ./venv/bin/activate
    python3 build.py

Finished
--------

Congratulations, FakerNet is now set up and configured! For how to use FakerNet now, go to :ref:`using-fakernet`