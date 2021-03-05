# FakerNet

![FakerNet Logo](fakernet.png)

FakerNet is a framework to quickly build internet-like services rapidly for home labs, testing, and research. Instead of wasting time setting up DNS, web servers, certificate authorities, and email, FakerNet uses Docker and LXC to quickly spin up these services and servers without all the hassle.

## Requirements

* Python 3.5+
* Docker
* LXD
* Open vSwitch
* Quagga

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
* Proxy
  * [Tinyproxy](http://tinyproxy.github.io/)
* Payload File Server
  * [pwndrop](https://github.com/kgretzky/pwndrop)

For more details, look at the [modules page](https://fakernet.readthedocs.io/en/latest/modules.html) in the documentation.

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

# Installation

See the [installation documentation](https://fakernet.readthedocs.io/en/latest/installation.html)

# User Guide

 Check out the [Getting Started Guide](https://fakernet.readthedocs.io/en/latest/getting-started.html)

# Contribute

Feel free to open an issue or merge request.

* Issue Tracker: https://github.com/bocajspear1/fakernet/issues
* Source Code: https://github.com/bocajspear1/fakernet

# License

The project is licensed under the Mozilla Public License Version 2.0.