# FakerNet

FakerNet is a framework to quickly build internet-like services rapidly for home labs, testing, and research. Instead of wasting time setting up DNS, web servers, certificate authorities, and email, FakerNet uses Docker and LXC to quickly spin up these services and servers without all the hassle.

## Requirements

* Python 3.5+
* Docker
* LXD
* Open vSwitch

## Supported Services

* DNS
* Certificate Authority
  * [minica](https://github.com/bocajspear1/minica)
* Email Server/Webmail
* Pastebin clone
  * [Bepasty](https://github.com/bepasty/bepasty-server)
* WebDAV
* [Mattermost](https://mattermost.com/) (Slack alternative)

## Not-yet-supported Services

* Serverless Code
* Web Servers
* Domain Registrar
* Status website (isitdownrightnow clone)
* Reddit Clone
* Search Engine
* IRC Server
* GitHub clone
* Twitter clone
* Social Media
* Wiki
* File services

## Permissions


### Docker

Be sure your user is the `docker` group so they can execute Docker commands

### Open vSwitch

Fakernet uses Open vSwitch to allow for a more flexible networking structure, using the `ovs-docker` command, which is packaged in repo at least in Ubuntu. It's a script and can be easily installed if not. 

To allow Fakernet to create switches and manage ports, you will need to allow the user running Fakernet to run `ovs-vsctl` and `ovs-docker` as root with sudo.
> Note: You are giving a user root privilege for a command, so be careful who it is!
```
jacob ALL=(ALL) NOPASSWD: /usr/bin/ovs-vsctl
jacob ALL=(ALL) NOPASSWD: /usr/bin/ovs-docker
```

### LXD

Be sure your user is in the `lxd` group to allow the execution of LXD commands.

### iptables

Also add sudo rules for `iptables`
```
jacob ALL=(ALL) NOPASSWD: /sbin/iptables
```

# Installation

## Ubuntu 18.04

1. Install dependencies:
```
apt-get install git python3-venv python3-pip openvswitch-switch lxd 
```
2. Install Docker as indicated on their [website](https://docs.docker.com/install/linux/docker-ce/ubuntu/). Configure as dictated in the **Permissions** section.
3. Add your user to the `docker` group.
4. Be sure to re-login so that group permissions come into effect.
5. Edit Docker's configuration to do uid remapping. This is for both security and to allow mapping of configuration files in Docker containers. In `/etc/docker/daemon.json`:
```
{
  "userns-remap": "default"
}
```
6. Restart the Docker service, Docker will create the `dockremap` user and setup subuids properly. 
7. Setup the `/etc/[ug]id` to remap the root uid in containers to our uid. In both `/etc/subuid` and `/etc/subgid`. Restart Docker afterwards:
```
dockremap:1000:1
```
8. Git the FakerNet repo and enter it:
```
git clone https://github.com/bocajspear1/fakernet.git
cd fakernet
```
9. Create a virtualenv and activate it:
```
python3 -m venv ./venv
. ./venv/bin/activate
```
10. Install Python dependencies:
```
pip3 install -r requirements.txt
```
11. Build the FakerNet Docker images and pull in LXD images:
```
python3 build.py
```
12. Run `fnconsole` to run the setup and start FakerNet services.
```
./fnconsole
```
13. (Recommended) Install `iptables-persistent` to manage your iptables rules.
14. Allow Forwarding between your internal and external interfaces:
```
sudo iptables -I FORWARD -i <INTERNAL_INTERFACE> -j ACCEPT
sudo iptables -I FORWARD -i <EXTERNAL_INTERFACE> -j ACCEPT
```
15. Enable masqerading for external access:
```
sudo iptables -t nat -I POSTROUTING 1 -o <EXTERNAL_INTERFACE> -j MASQUERADE
```
16. (Recommended) Setup forwarders for the main DNS server:
```
./fnconsole
run dns add_forwarder
set id 1
set ip_addr <FORWARDER IP>
execute
```

# Usage

Run
```
./fnconsole
```
to start the FakerNet console.

The main command to do stuff is `run`. The console supports autocomplete, so you can see a list of available modules.