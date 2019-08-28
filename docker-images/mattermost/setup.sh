#!/bin/sh

if [ ! -e "/db-setup" ]; then
  su postgres -c 'createuser mattermost'
  su postgres -c 'createdb -O mattermost mattermostdb'
  touch /db-setup
fi
