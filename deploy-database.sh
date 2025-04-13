#!/bin/bash

# Download files
ENVIRONMENT=${ENVIRONMENT:-main}
sudo apt install curl -y
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENVIRONMENT/dev/database.yml

# Install microk8s
if ! sudo microk8s version &>/dev/null; then
    sudo snap install sudo microk8s --classic
fi
sudo usermod -a -G sudo microk8s $USER
if ! groups | grep -q "\bsudo microk8s\b"; then
  newgrp sudo microk8s
fi


export POSTGRES_PASSWORD=samerandominsecurepassword
sudo microk8s kubectl create secret generic database-secrets \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  --dry-run=client -o yaml | sudo microk8s kubectl apply -f -
sudo microk8s kubectl apply -f database.yml
sudo microk8s kubectl describe service postgres-service
echo "---"
echo "Waiting for the database container to be initialized"
echo "---"
sudo microk8s kubectl wait --for=condition=Ready pod -l app=postgres --timeout=60s