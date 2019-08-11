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

if [ ! -e "/opt/bepasty/bepasty.conf" ]; then
    echo "Setting up Nginx"
    mv /opt/bepasty/bepasty.conf.init /opt/bepasty/bepasty.conf
    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /opt/bepasty/bepasty.conf
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    sed -i "s_INSERT_SECRET_KEY_${SECRET_KEY}_" /opt/bepasty/bepasty.conf
    ADMIN_PASS=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
    sed -i "s_INSERT_ADMIN_PASS_${ADMIN_PASS}_" /opt/bepasty/bepasty.conf
fi