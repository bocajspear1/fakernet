#!/bin/sh

if [ -z "$1" ]; then
    echo "Need a domain"
    exit 1
fi

DOMAIN=$1

if [ ! -e "/db-setup" ]; then
    su postgres -c 'createuser mattermost'
    su postgres -c 'createdb -O mattermost mattermostdb'
    touch /db-setup
fi

if [ ! -e "/mattermost/config/config.json " ]; then
    echo "Setting up Mattermost config"
    mv /config.json.init  /mattermost/config/config.json 
    sed -i "s|DOMAIN.ZONE|${DOMAIN}|" /mattermost/config/config.json 
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    sed -i "s|INSERT_SECRET_KEY|${SECRET_KEY}|" /mattermost/config/config.json 
    chown mattermost:mattermost /mattermost/config/config.json
    chmod 775 /mattermost/config/config.json
fi
