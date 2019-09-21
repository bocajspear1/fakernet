#!/bin/ash

if [ -z "$1" ]; then
    echo "Need a domain"
    exit 1
fi

DOMAIN=$1

mv /mail/postfix-files /etc/postfix/postfix-files;
mv /mail/dynamicmaps.cf.d /etc/postfix/dynamicmaps.cf.d;

if [ ! -e "/usr/local/share/ca-certificates/fakernet.crt" ]; then
    echo "Copying in CA cert"
    cp /etc/certs/fakernet-ca.crt /usr/local/share/ca-certificates/fakernet.crt;
    update-ca-certificates;
fi 

if [ ! -e "/etc/dovecot/admin.pass" ]; then
    echo "Setting up database"
    PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
    echo $PASSWORD > /etc/dovecot/admin.pass
    HASHED_PASS=$(doveadm pw -s SSHA512 -p $PASSWORD)
    sed -i "s_HASHEDPASSWORD_${HASHED_PASS}_" /etc/dovecot/db.sql
    cat /etc/dovecot/db.sql | sqlite3 /etc/postfix/vmail.sqlite
    chown :maildb /etc/postfix/vmail.sqlite
    chown :maildb /etc/postfix
    chmod 775 /etc/postfix
    chmod 664 /etc/postfix/vmail.sqlite
fi

mkdir -p /var/spool/mailvirtual/
chown postfix:postfix /var/spool/mailvirtual/
chown root:root /etc/postfix/dynamicmaps.cf
chmod 640 /etc/postfix/dynamicmaps.cf 
postalias /etc/postfix/aliases



if [ ! -e "/var/www/localhost/htdocs/roundcube/config/config.inc.php" ]; then
    echo "Setting up Roundcube"

    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /etc/apache2/conf.d/01-access.conf
    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /etc/apache2/conf.d/ssl.conf

    cp /var/www/localhost/htdocs/roundcube/config/config.inc.php.sample /var/www/localhost/htdocs/roundcube/config/config.inc.php
    IMAPKEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 24 | head -n 1)
    sed -i "s|config\['db_dsnw'\].*\$|config['db_dsnw'] = 'sqlite:////var/www/localhost/db/roundcube.db?mode=0646';|" /var/www/localhost/htdocs/roundcube/config/config.inc.php
    sed -i "s|config\['des_key'\].*\$|config['des_key'] = '${IMAPKEY}';|" /var/www/localhost/htdocs/roundcube/config/config.inc.php
    sed -i "s| 'localhost';\$| 'tls://${DOMAIN}';|" /var/www/localhost/htdocs/roundcube/config/config.inc.php
    sed -i "s|config\['smtp_port'\] = 25;\$|config\['smtp_port'\] = 587;|" /var/www/localhost/htdocs/roundcube/config/config.inc.php
fi