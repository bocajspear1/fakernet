#!/bin/bash

CURRENT_USER=$(id -u -n)
CURRENT_UID=$(id -u)

if [ ! -f ./fnconsole ]; then
    echo "Only run this script from the main FakerNet directory!"
    exit 1
fi

echo -e "User ${CURRENT_USER} (${CURRENT_UID}) will be the user configured to run FakerNet..."
read -p "Type 'yes' to continue> " ok

if [[ "$ok" != "yes" ]]; then
    echo "Not running..."
    exit 1
fi

echo "Getting Docker pre-reqs..."
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common

echo "Installing Docker key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

echo "Installing Docker repo..."
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

echo "Installing Docker..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

echo "Installing other dependencies..."
sudo apt-get install -y openvswitch-switch lxd python3-venv python3-pip quagga 

echo "Adding current user to 'docker' group..."

sudo usermod -a -G docker $CURRENT_USER

echo "Configuring Docker to not be privileged..."
echo -e "{\n    \"userns-remap\": \"default\"\n}" | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

echo "Configuring subuid/subgid..."
echo "dockremap:${CURRENT_UID}:1" > /tmp/.temp_subuid
echo "dockremap:${CURRENT_UID}:1" > /tmp/.temp_subgid
cat /etc/subuid >> /tmp/.temp_subuid
cat /etc/subgid >> /tmp/.temp_subgid
sudo mv /tmp/.temp_subuid /etc/subuid
sudo mv /tmp/.temp_subgid /etc/subgid

echo "Install Python components..."
python3 -m venv ./venv
. ./venv/bin/activate
pip3 install -r requirements.txt

echo "Running 'lxd init'... (Defaults will usually for for FakerNet)"
lxd init

echo "Installation is complete!"

echo ""
echo "=============================================================="
echo "WARNING: YOU MUST RE-LOGIN!"
echo "OTHERWISE GROUP PERMISSIONS WILL NOT COME INTO EFFECT!"
echo "AND YOU WILL GET PERMISSION DENIED ERRORS FOR DOCKER!"
echo "=============================================================="