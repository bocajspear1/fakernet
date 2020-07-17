#!/bin/bash

CURRENT_USER=$(id -u -n)
CURRENT_UID=$(id -u)

echo "WARNING: This does only a non-Python dependency install, made for CI!"

if [[ "$CURRENT_UID" -eq "0" ]]; then
    echo "Do not start the script as root. sudo will be called when necessary."
    echo "This is so the user for FakerNet can be set to the running user."
    exit 1
fi

echo "User ${CURRENT_USER} (${CURRENT_UID}) will be the user configured to run FakerNet CI..."
echo "They will be able to run lxd commands, Docker commands, iptables, ovs-vsctl, and ovs-docker without a password!"
echo "Be sure you want them to have essentially root access when on a shell!"
echo "(Keep the user secure!)"
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
sudo apt-get install -y openvswitch-switch lxd python3-venv python3-pip quagga traceroute

echo "Adding current user to 'quaggavty' group..."
sudo usermod -a -G quaggavty $CURRENT_USER

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

sudo systemctl restart lxd

echo "Doing sudo configuration..."
echo "${CURRENT_USER} ALL=(ALL) NOPASSWD: /sbin/iptables" >> /tmp/.fn_sudo
echo "${CURRENT_USER} ALL=(ALL) NOPASSWD: /usr/bin/ovs-vsctl" >> /tmp/.fn_sudo
echo "${CURRENT_USER} ALL=(ALL) NOPASSWD: /usr/bin/ovs-docker" >> /tmp/.fn_sudo
echo "${CURRENT_USER} ALL=(ALL) NOPASSWD: /sbin/ip" >> /tmp/.fn_sudo
sudo mv /tmp/.fn_sudo /etc/sudoers.d/FakerNet
sudo chmod 440 /etc/sudoers.d/FakerNet
sudo chown root:root /etc/sudoers.d/FakerNet

echo "Setting up Quagga..."
sudo touch /etc/quagga/zebra.conf
sudo touch /etc/quagga/vtysh.conf
sudo touch /etc/quagga/ripd.conf
sudo chown quagga:quagga /etc/quagga/*.conf
sudo systemctl enable zebra
sudo systemctl enable ripd
sudo systemctl start zebra 
sudo systemctl start ripd 

echo "Running 'lxd init'..."
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
sudo systemctl start docker  

echo "Installation is complete!"

echo ""
echo "=============================================================="
echo "WARNING: YOU MUST RE-LOGIN!"
echo "OTHERWISE GROUP PERMISSIONS WILL NOT COME INTO EFFECT!"
echo "AND YOU WILL GET PERMISSION DENIED ERRORS FOR DOCKER!"
echo "=============================================================="