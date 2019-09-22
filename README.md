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

For the sake of security, set Docker to run containers unprivileged. In `/etc/docker/daemon.json`:
```
{
  "userns-remap": "default"
}
```

You will then need to allow remapping in the container so that we can edit files and have them accessible to services inside the container (both `/etc/subuid` and `/etc/subgid`):
```
dockremap:1000:1
```

Be sure to restart Docker to enable these changes.

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
5. Git the FakerNet repo and enter it:
```
git clone https://github.com/bocajspear1/fakernet.git
cd fakernet
```
6. Create a virtualenv and activate it:
```
python3 -m venv ./venv
. ./venv/bin/activate
```
7. Install Python dependencies:
```
pip3 install -r requirements.txt
```
8. Build the FakerNet Docker images and pull in LXD images:
```
python3 build.py
```