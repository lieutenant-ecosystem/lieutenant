#!/bin/bash

# Download files
ENVIRONMENT=${ENVIRONMENT:-main}
sudo apt install curl -y
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENVIRONMENT/dev/database.yml

# Install microk8s
if ! microk8s version &>/dev/null; then
    sudo snap install microk8s --classic
fi
sudo usermod -a -G microk8s $USER
if ! groups | grep -q "\bmicrok8s\b"; then
  newgrp microk8s
fi


export POSTGRES_PASSWORD=samerandominsecurepassword
microk8s kubectl create secret generic database-secrets \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  --dry-run=client -o yaml | microk8s kubectl apply -f -
microk8s kubectl apply -f database.yml
microk8s kubectl describe service postgres-service
echo "---"
echo "Waiting for the database container to be initialized"
echo "---"
microk8s kubectl wait --for=condition=Ready pod -l app=postgres --timeout=60s