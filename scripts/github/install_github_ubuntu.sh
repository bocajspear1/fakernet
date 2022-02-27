#!/bin/bash

USERNAME="fakernet"

sudo useradd -m ${USERNAME}

NO_MOVE=0
CREATE_SERVICE=0
INSTALL_USER=${USERNAME}
INSTALL_UID=$(id -u ${USERNAME})
INSTALL_DIR=/opt/fakernet

id 
echo ${INSTALL_UID}

COLOR_RED="\e[1;31m"
COLOR_BLUE="\e[1;34m"
COLOR_GREEN="\e[1;32m"
COLOR_ORANGE="\e[1;33m"
COLOR_RESET="\e[0m"

# Make sure the time synced
sudo timedatectl set-ntp off
sudo timedatectl set-ntp on
sleep 10


if [ ! -f ./fnconsole ]; then
    echo "${COLOR_RED}Only run this script from the main FakerNet directory!${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_BLUE}Installing other dependencies...${COLOR_RESET}"
sudo apt-get install -y openvswitch-switch python3-venv python3-pip quagga traceroute rustc libssl-dev

echo -e "${COLOR_BLUE}Installing LXD 4.0 LTS snap (package is old)...${COLOR_RESET}"
sudo apt-get remove lxd 2>/dev/null || true
sudo snap remove lxd 2>/dev/null || true
sudo snap install lxd --channel=4.0/stable

echo -e "${COLOR_BLUE}Adding install user to 'quaggavty' group...${COLOR_RESET}"
sudo usermod -a -G quaggavty $INSTALL_USER

echo -e "${COLOR_BLUE}Adding install user to 'docker' group...${COLOR_RESET}"
sudo usermod -a -G docker $INSTALL_USER

echo -e "${COLOR_BLUE}Adding install user to 'lxd' group...${COLOR_RESET}"
sudo usermod -a -G lxd $INSTALL_USER

echo -e "${COLOR_BLUE}Configuring Docker to not be privileged...${COLOR_RESET}"
echo -e "{\n    \"userns-remap\": \"default\"\n}" | sudo tee /etc/docker/daemon.json

sudo systemctl restart docker

# Wait until dockremap has been populated.
# Duplicate entries can cause an issue
while [ -z "$(grep dockremap /etc/subuid)" ]; do 
    sleep 20; 
done;

echo -e "${COLOR_BLUE}Configuring subuid/subgid...${COLOR_RESET}"
# Allow dockremap to map container root to host UID
echo "dockremap:${INSTALL_UID}:1" > /tmp/.temp_subuid
echo "dockremap:${INSTALL_UID}:1" > /tmp/.temp_subgid
cat /etc/subuid >> /tmp/.temp_subuid
cat /etc/subgid >> /tmp/.temp_subgid
sudo mv /tmp/.temp_subuid /etc/subuid
sudo mv /tmp/.temp_subgid /etc/subgid

sudo systemctl restart lxd

echo -e "${COLOR_BLUE}Doing sudo configuration...${COLOR_RESET}"
echo "${INSTALL_USER} ALL=(ALL) NOPASSWD: /sbin/iptables" >> /tmp/.fn_sudo
echo "${INSTALL_USER} ALL=(ALL) NOPASSWD: /usr/bin/ovs-vsctl" >> /tmp/.fn_sudo
echo "${INSTALL_USER} ALL=(ALL) NOPASSWD: /usr/bin/ovs-docker" >> /tmp/.fn_sudo
echo "${INSTALL_USER} ALL=(ALL) NOPASSWD: /sbin/ip" >> /tmp/.fn_sudo
sudo mv /tmp/.fn_sudo /etc/sudoers.d/fakernet
sudo chmod 440 /etc/sudoers.d/fakernet
sudo chown root:root /etc/sudoers.d/fakernet

echo -e "${COLOR_BLUE}Setting up Quagga...${COLOR_RESET}"
sudo touch /etc/quagga/zebra.conf
sudo touch /etc/quagga/vtysh.conf
sudo touch /etc/quagga/ripd.conf
sudo chown quagga:quagga /etc/quagga/*.conf
sudo systemctl enable zebra
sudo systemctl enable ripd
sudo systemctl start zebra 
sudo systemctl start ripd 


echo -e "${COLOR_BLUE}Installing FakerNet to ${INSTALL_DIR}...${COLOR_RESET}"
sudo cp -p -r `pwd` ${INSTALL_DIR}
sudo chown -R ${INSTALL_USER} ${INSTALL_DIR} 
sudo chmod 775 ${INSTALL_DIR}

echo -e "${COLOR_BLUE}Install Python components...${COLOR_RESET}"
sudo --user ${INSTALL_USER} python3 -m venv ${INSTALL_DIR}/venv
# Python cryptography library needs setuptools_rust to be installed first
sudo --user ${INSTALL_USER} --login -- bash -c "source ${INSTALL_DIR}/venv/bin/activate && pip3 install setuptools_rust"
sudo --user ${INSTALL_USER} --login -- bash -c "source ${INSTALL_DIR}/venv/bin/activate && pip3 install -r ${INSTALL_DIR}/requirements.txt"



echo -e "${COLOR_BLUE}Running 'lxd init'...${COLOR_RESET}"
cat <<EOF | sudo lxd init --preseed
config: {}
networks: []
storage_pools:
- config: {}
  description: ""
  name: default
  driver: dir
profiles:
- config: {}
  description: ""
  devices:
    root:
      path: /
      pool: default
      type: disk
  name: default
cluster: null
EOF


sudo systemctl stop docker  
sleep 10
sudo systemctl start docker  

echo ""
lxc version
echo ""

echo -e "${COLOR_GREEN}Installation is complete!${COLOR_RESET}"
