<h1 align="center">FakerNet</h1>

<p align="center">
<img src="https://raw.githubusercontent.com/bocajspear1/fakernet/master/fakernet.png"/>
</p>

<h2 align="center">Internet-in-a-box</h2>
<br/>

[![Documentation Status](https://readthedocs.org/projects/fakernet/badge/?version=latest)](https://fakernet.readthedocs.io/en/latest/?badge=latest)
![Last Commit](https://img.shields.io/github/last-commit/bocajspear1/fakernet/master)
![Open Issues](https://img.shields.io/github/issues-raw/bocajspear1/fakernet)
![License](https://img.shields.io/github/license/bocajspear1/fakernet)



FakerNet is a framework to quickly build internet-like services rapidly for home labs, testing, and research. Instead of wasting time setting up DNS, web servers, certificate authorities, and email, FakerNet uses Docker and LXC to quickly create and integrate these services and servers without all the hassle.

## Requirements

* Python 3.5+
* Docker
* LXD
* Open vSwitch
* Quagga

## Supported Services

FakerNet supports a number of services:

* DNS
* Certificate Authority - [minica](https://github.com/bocajspear1/minica)
* Email Server/Webmail
* Pastebin clone - [Bepasty](https://github.com/bepasty/bepasty-server)
* WebDAV
* Slack Alternative - [Mattermost](https://mattermost.com/)
* IRC Server - [inspircd](https://www.inspircd.org/)
* Proxy - [Tinyproxy](http://tinyproxy.github.io/)
* Payload File Server - [pwndrop](https://github.com/kgretzky/pwndrop)

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

Feel free to contribute one or more of these services! Check out the module-building tutorial [here](https://fakernet.readthedocs.io/en/latest/tutorials/building-modules.html).

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