#!/bin/ash

cp /etc/certs/fakernet-ca.crt /usr/local/share/ca-certificates/fakernet.crt;
update-ca-certificates;
cp /mail/postfix-files /etc/postfix/postfix-files;
