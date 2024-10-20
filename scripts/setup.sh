#!/bin/bash

sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo snap install docker

# Set up Docker prerequisites
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update

# Install Docker
sudo apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose
sudo groupadd docker
sudo usermod -aG docker $USER

# Setup the docker-compose.yml file
ENV_FILE=$HOME/.env
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/production/docker-compose.yml
sudo chown $USER:$USER $ENV_FILE
sudo chown :docker $ENV_FILE
sudo chmod 640 $ENV_FILE
sudo chmod 644 $ENV_FILE
sudo chmod 755 $HOME

# Start the Lieutenant
sudo docker-compose --env-file $HOME/.env up -d