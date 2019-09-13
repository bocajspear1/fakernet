MiniCA is a small, Go-based CA web application. It has a single password as its authentication, so don't use this in any production system or untrusted network.

The password for creating certs is located in `work/minica/<SERVER_ID>/ca.pass` externally or `/etc/minica/certs/ca.pass` in the container.

The web interface is available as HTTPS (signed by itself) at the container's IP address. You'll need to upload a CSR and enter the CA password.