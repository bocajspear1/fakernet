.. _web-api:

Web API
=======

FakerNet can run as a server, which exposes a REST API. By default, the API uses SSL and runs on port 5051.

You will need to generate a certificate before you can use it. You can use the following to create a self-signed certificate:

..  code-block::

    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes