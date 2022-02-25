#!/bin/ash


if [ -z "${DOMAIN}" ]; then
    echo "Need a domain"
    exit 1
fi

# MySQL Setup
start_mysql () {
  mysqld --socket=/run/mysqld/mysqld.sock --user=mysql --datadir=/var/lib/mysql &
  sleep 2
}

mkdir -p /var/lib/mysql/
chown mysql:mysql /var/lib/mysql/
mkdir -p /run/mysqld/
chown mysql:mysql /run/mysqld/

chmod 777 /mattermost/plugins
chmod 777 /mattermost/client/plugins
chmod 777 /mattermost/data
mkdir -p /mattermost/logs
# echo "Setting permissions..."
# chown mattermost:mattermost -R /mattermost

if [ ! -e "/mattermost/config/config.json " ]; then
    echo "Setting up MariaDB"
    mysql_install_db --user=mysql --datadir=/var/lib/mysql
    start_mysql

    DB_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    mysql -u root -e "create user 'mmuser'@'localhost' identified by '${DB_PASSWORD}'; create database mattermost;"
    mysql -u root -e " grant all privileges on mattermost.* to 'mmuser'@'localhost'; flush privileges;"
    
    echo "Setting up Mattermost config"
    mv /config.json.init  /mattermost/config/config.json 
    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /mattermost/config/config.json 
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    sed -i "s|INSERT_SECRET_KEY|${SECRET_KEY}|" /mattermost/config/config.json 
    sed -i "s|INSERT_DB_PASSWORD|${DB_PASSWORD}|" /mattermost/config/config.json 
    chown mattermost:mattermost /mattermost/config/config.json
    chmod 775 /mattermost/config/config.json
else
  start_mysql
fi

su mattermost -c '/mattermost/bin/mattermost'