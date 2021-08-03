#!/bin/bash

NO_MOVE=0
FORCE=0
CREATE_SERVICE=0
INSTALL_USER=$(id -u -n)
INSTALL_UID=$(id -u)
INSTALL_DIR=/opt/fakernet
DOCKER_PROXY=""

COLOR_RED="\e[1;31m"
COLOR_BLUE="\e[1;34m"
COLOR_GREEN="\e[1;32m"
COLOR_ORANGE="\e[1;33m"
COLOR_RESET="\e[0m"

ShowHelp() {
  echo "install_ubuntu.sh [-u <USER>] [-n] [-d <DOCKER_PROXY>] [-f] [-s]"
}

while getopts ":nfhu:d:" option; do
    case $option in
        h) # display Help
            ShowHelp
            exit;;
        u) # Username for installation
            INSTALL_USER=$(id -u -n $OPTARG)
            INSTALL_UID=$(id -u $OPTARG)
            ;;
        n)
            NO_MOVE=1
            ;;
        s)
            CREATE_SERVICE=1
            ;;
        d)
            DOCKER_PROXY=$OPTARG
            ;;
        f)
            FORCE=1
            ;;
        \?) # Invalid option
            echo "Error: Invalid option"
            ShowHelp
            exit;;
    esac
done

# Make sure the time synced
sudo timedatectl set-ntp off
sudo timedatectl set-ntp on
sleep 10

if [[ "$INSTALL_UID" -eq "0" ]]; then
    echo -e "${COLOR_RED}Do not set the install user as root. sudo will be called when necessary."
    echo -e "This is so the user for FakerNet runs a less-privileged user.${COLOR_RESET}"
    exit 1
fi

if [ ! -f ./fnconsole ]; then
    echo "${COLOR_RED}Only run this script from the main FakerNet directory!${COLOR_RESET}"
    exit 1
fi

if [[ "$FORCE" -ne "1" ]]; then
    echo -e "${COLOR_BLUE}User ${COLOR_ORANGE}${INSTALL_USER} (${INSTALL_UID}) ${COLOR_BLUE}will be the user configured to run FakerNet..."
    echo -e "They will be able to run lxd commands, Docker commands, iptables, ovs-vsctl, and ovs-docker without a password!"
    echo -e "Be sure you want them to have essentially ${COLOR_RED}root${COLOR_BLUE} access when on a shell!"
    echo -e "${COLOR_ORANGE}(Keep the user secure!)${COLOR_RESET}"
    read -p "Type 'yes' to continue> " ok

    if [[ "$ok" != "yes" ]]; then
        echo "${COLOR_ORANGE}Not running...${COLOR_RESET}"
        exit 1
    fi
fi

echo -e "${COLOR_BLUE}Getting Docker pre-reqs...${COLOR_RESET}"
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg software-properties-common lsb-release

echo -e "${COLOR_BLUE}Installing Docker key...${COLOR_RESET}"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo -e "${COLOR_BLUE}Adding Docker repo...${COLOR_RESET}"
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list

echo -e "${COLOR_BLUE}Installing Docker...${COLOR_RESET}"
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

echo -e "${COLOR_BLUE}Installing other dependencies...${COLOR_RESET}"
sudo apt-get install -y openvswitch-switch lxd python3-venv python3-pip quagga traceroute rustc libssl-dev

echo -e "${COLOR_BLUE}Adding current user to 'quaggavty' group...${COLOR_RESET}"
sudo usermod -a -G quaggavty $INSTALL_USER

echo -e "${COLOR_BLUE}Adding current user to 'docker' group...${COLOR_RESET}"
sudo usermod -a -G docker $INSTALL_USER

echo -e "${COLOR_BLUE}Adding current user to 'lxd' group...${COLOR_RESET}"
sudo usermod -a -G lxd $INSTALL_USER

echo -e "${COLOR_BLUE}Configuring Docker to not be privileged...${COLOR_RESET}"
if [ -z "$DOCKER_PROXY" ]; then 
    echo -e "{\n    \"userns-remap\": \"default\"\n}" | sudo tee /etc/docker/daemon.json
else
    echo -e "${COLOR_BLUE}Configuring with Docker proxy at ${DOCKER_PROXY}...${COLOR_RESET}"
    echo -e "{\n    \"userns-remap\": \"default\",\n    \"registry-mirrors\": [\"${DOCKER_PROXY}\"]\n}" | sudo tee /etc/docker/daemon.json
fi

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


if [[ "$NO_MOVE" -eq "1" ]]; then
    INSTALL_DIR=`pwd`
    echo -e "${COLOR_BLUE}Keeping FakerNet in ${INSTALL_DIR}...${COLOR_RESET}"
else
    echo -e "${COLOR_BLUE}Installing FakerNet to ${INSTALL_DIR}...${COLOR_RESET}"
    sudo cp -p -r `pwd` ${INSTALL_DIR}
    sudo chown -R ${INSTALL_USER} ${INSTALL_DIR} 
    sudo chmod -R 775 ${INSTALL_DIR}
fi


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

if [[ "$CREATE_SERVICE" -eq "1" ]]; then
    echo -e "${COLOR_BLUE}Creating FakerNet service...${COLOR_RESET}"
    sudo cp scripts/fakernet.service.template /etc/systemd/system/fakernet.service
    sudo sed -i "s_CURRENTUSER_${INSTALL_USER}_g" /etc/systemd/system/fakernet.service
    sudo sed -i "s_PWD_${INSTALL_DIR}_g" /etc/systemd/system/fakernet.service
    sudo systemctl daemon-reload 
fi

echo -e "${COLOR_GREEN}Installation is complete!${COLOR_RESET}"

CURRENT_UID=$(id -u)

if [[ "$CURRENT_UID" -eq "$INSTALL_UID" ]]; then
    echo ""
    echo -e "${COLOR_ORANGE}=============================================================="
    echo "WARNING: YOU MUST RE-LOGIN!"
    echo "OTHERWISE GROUP PERMISSIONS WILL NOT COME INTO EFFECT!"
    echo "AND YOU WILL GET PERMISSION DENIED ERRORS FOR DOCKER!"
    echo -e "==============================================================${COLOR_RESET}"
else
    echo -e "${COLOR_GREEN}Logon as user ${INSTALL_USER} to run FakerNet!${COLOR_RESET}"
fi