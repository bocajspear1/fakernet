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

if [ ! -e "/etc/nginx/sites-enabled/nginx-bepasty.conf" ]; then
    echo "Setting up Nginx"
    mv /etc/nginx/sites-enabled/nginx-bepasty.conf.init /etc/nginx/sites-enabled/nginx-bepasty.conf
    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /etc/nginx/sites-enabled/nginx-bepasty.conf
fi

if [ ! -e "/opt/bepasty/conf/bepasty.conf" ]; then
    echo "Setting up Nginx"
    mv /opt/bepasty/bepasty.conf.init /opt/bepasty/conf/bepasty.conf
    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /opt/bepasty/conf/bepasty.conf
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    sed -i "s|INSERT_SECRET_KEY|${SECRET_KEY}|" /opt/bepasty/conf/bepasty.conf
    ADMIN_PASS=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
    sed -i "s|INSERT_ADMIN_PASS|${ADMIN_PASS}|" /opt/bepasty/conf/bepasty.conf
fi

chmod 777 /opt/bepasty/storage/
