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
* IRC Server [inspircd](https://www.inspircd.org/)

## Not-yet-supported Services

* Serverless Code
* Web Servers
* Domain Registrar
* Status website (isitdownrightnow clone)
* Reddit Clone
* Search Engine
* GitHub clone
* Twitter clone
* Social Media
* Wiki
* File services

## Setup

> Security Note: During installation, the current user (the one running FakerNet) will be given access to commands that can used to gain root privileges if given unfettered access on a shell. FakerNet limits access to these commands during operation. Be aware of the user you are giving these controls to and restrict access to the account that runs FakerNet.

### Install Script

An installation script for Ubuntu (tested on Ubuntu 18.04) is available in `scripts/install_ubuntu.sh`

### Manual Install

1. Install dependencies. These are:
* LXD
* Open vSwitch
* Python 3.5 or higher, with pip and venv support
* git
* quagga routing services
* traceroute

For Ubuntu, (which FakerNet has been tested on), this is the command:
```
apt-get install git python3-venv python3-pip openvswitch-switch lxd quagga traceroute
```
3. If not already, add your user to the `lxd` group. (Be sure to re-login at some point so that group permissions come into effect.)
2. Install Docker as indicated on their [website](https://docs.docker.com/install/linux/docker-ce/ubuntu/). 
3. Add your user to the `docker` group so your user can run Docker commands. (Be sure to re-login at some point so that group permissions come into effect.)
4. Edit Docker's configuration to do uid remapping and user namespaces. This is for both security and to allow mapping of configuration files in Docker containers. In `/etc/docker/daemon.json` add the following (the file usually needs to be made):
```
{
  "userns-remap": "default"
}
```
6. Restart the Docker service, Docker will create the `dockremap` user and setup subuids properly. 
7. To ensure the root user in the containers maps to our current user that will run FakerNet, modify `/etc/[ug]id`. In both `/etc/subuid` and `/etc/subgid` set the following.afterwards:
```
dockremap:1000:1
```
8. Restart Docker
9. FakerNet needs to run certain commands as root. To do this without running the entire framework as root, we can use `sudo` rules to give the current user access to the specific commands. These commands are:
  * `ovs-vsctl`: For controlling Open vSwitch
  * `ovs-docker`: For connecting Docker images to Open vSwitch switches
  * `iptables`: For making automatic redirects
  * `ip`: For controlling interfaces

```
# Example sudoers entries. Paths may differ in your case.
user ALL=(ALL) NOPASSWD: /usr/bin/ovs-vsctl
user ALL=(ALL) NOPASSWD: /usr/bin/ovs-docker
user ALL=(ALL) NOPASSWD: /sbin/iptables
user ALL=(ALL) NOPASSWD: /sbin/ip
```
> Note these commands can give the user root privileges (apart from the possibility for root privileges from Docker and LXD), so be ware of the user you are giving these controls to and restrict access to the account.
9. For access to the Quagga routing services, add the current user to the `quaggavty` group.
10. If you haven't re-logged in to activated the new groups on the current user, do that now.
11. If you haven't configured LXD, run `lxd init` now as root. The defaults will usually suffice, but don't create a managed switch during LXD setup.
12. Git clone the FakerNet repo and enter the root directory:
```
git clone https://github.com/bocajspear1/fakernet.git
cd fakernet
```
13. Create a virtualenv and activate it:
```
python3 -m venv ./venv
. ./venv/bin/activate
```
14. Install Python dependencies:
```
pip3 install -r requirements.txt
```


# Usage

Run
```
./fnconsole
```
to start the FakerNet console.

The main command to do stuff is `run`. The console supports autocomplete, so you can see a list of available modules.