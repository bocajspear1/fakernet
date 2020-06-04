# Getting Started

## Network Design

For designing your network to work with FakerNet please reference the [Network Design](network-design.html) page.

## Installing

Currently, Fakernet has been tested with Ubuntu 18.04. An installation script is available to speed things up. Run the script in ```scripts/install_ubuntu.sh``` for a quick install.

If you want to do a manual install, please reference the project's README.

## Post Installation

### Build Images

After everything is install, you'll need to build the FakerNet Docker images and pull in LXD images (This will take awhile):
```
python3 build.py
```

### iptables

Currently, a few additions need to be done manually through ```iptables``` to ensure proper access and networking. It is recommended to use something like ```iptables-persistent``` to save and manage your rules to be activated on start. (You will probably need to prune off default Docker and LXD rules in the saved rules file.)

* You'll need to allow forwarding between your internal and external interfaces. Docker closes off forwarding by default:
```
sudo iptables -I FORWARD -i <INTERNAL_INTERFACE> -j ACCEPT
sudo iptables -I FORWARD -i <EXTERNAL_INTERFACE> -j ACCEPT
```
* If you want your FakerNet systems to have access to the external network, enable masqerading on the external interface:
```
sudo iptables -t nat -I POSTROUTING 1 -o <EXTERNAL_INTERFACE> -j MASQUERADE
```

## Using FakerNet

FakerNet is primarily accessed via a command line interface, ```fnconsole```. (A web based interface may be created at some point.) This command line can either use modules locally or connect to a REST API server, either remote or locally. The FakerNet server (```fnserver```) is required for automatic startup of your network setup, otherwise you have to manually start your services and reapply certain configurations every time your FakerNet system reboots.

### First Run

Before you install the service, you need to perform the first-run setup. This is as easy as running the FakerNet console, which will set you though creating the minimum required services:

* A DNS server (the central server that all other FakerNet systems by default will forward to and yours should too)
* A MiniCA instance to generate certificates for other services.

After that, you will be dropped into the FakerNet console. Type ```exit``` to close the console.

### Forwarders
* If you want your primary DNS to be able to resolve internet queries, setup forwarders for the main DNS server:
```
./fnconsole
run dns add_forwarder
set id 1
set ip_addr <FORWARDER IP>
execute
```

### Installing the FakerNet Service

The FakerNet service can be installed using the following instructions:

#### Systemd

Run in a system shell:
```
./scripts/create_systemd_service.sh
```

This should create the FakerNet service that will run as the current user.

## Installation Complete

FakerNet should now be setup. Head to the [Console User Manual](console-user-manual.html) to see how to use ```fnconsole```
