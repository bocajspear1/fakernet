#!/bin/ash

cp /etc/certs/fakernet-ca.crt /usr/local/share/ca-certificates/fakernet.crt;
update-ca-certificates;
cp /mail/postfix-files /etc/postfix/postfix-files;

PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
echo $PASSWORD > /etc/dovecot/admin.pass
HASHED_PASS=$(doveadm pw -s SSHA512 -p $PASSWORD)
sed -i "s_HASHEDPASSWORD_${HASHED_PASS}_" /etc/dovecot/db.sql
cat /etc/dovecot/db.sql | sqlite3 /etc/postfix/vmail.sqlite

mkdir -p /var/spool/mailvirtual/
chown postfix:postfix /var/spool/mailvirtual/
