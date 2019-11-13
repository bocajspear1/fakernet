#!/bin/bash

sudo cp scripts/fakernet.service.template /etc/systemd/system/fakernet.service
sudo sed -i "s_CURRENTUSER_${USER}_g" /etc/systemd/system/fakernet.service
PWD=`pwd`
sudo sed -i "s_PWD_${PWD}_g" /etc/systemd/system/fakernet.service
sudo systemctl daemon-reload 