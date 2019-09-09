#!/bin/ash

if [ -z "$1" ]; then
    echo "Need a domain"
    exit 1
fi

DOMAIN=$1

if [ ! -e "/usr/local/share/ca-certificates/fakernet.crt" ]; then
    echo "Copying in CA cert"
    cp /etc/certs/fakernet-ca.crt /usr/local/share/ca-certificates/fakernet.crt;
    update-ca-certificates;
fi 

if [ ! -e "/etc/webdav/admin.pass" ]; then
    echo "Setting admin password"
    PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
    echo $PASSWORD > /etc/webdav/admin.pass
    htpasswd -b -c /var/www/users.passwd admin $PASSWORD
fi

