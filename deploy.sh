#!/bin/bash

# Download files
ENVIRONMENT=${ENVIRONMENT:-main}
sudo apt install curl -y
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENVIRONMENT/lieutenant.yml
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENVIRONMENT/gateway.yml

# Install microk8s
if ! sudo microk8s version &>/dev/null; then
    sudo snap install sudo microk8s --classic
fi
sudo usermod -a -G sudo microk8s $USER
if ! groups | grep -q "\bsudo microk8s\b"; then
  newgrp sudo microk8s
fi

# Prepare the symlinks for data persistence
APP_DATA_DIR="$HOME/app_data"
SERGEANT_SERVICE_DATA_DIR="$APP_DATA_DIR/sergeant_service/data/"
VECTOR_EMBEDDING_SERVICE_DATA_DIR="$APP_DATA_DIR/vector_embedding_service/data/"
INTELLIGENCE_SERVICE_DATA_DIR="$APP_DATA_DIR/intelligence_service/data/"

mkdir -p "$SERGEANT_SERVICE_DATA_DIR"
mkdir -p "$VECTOR_EMBEDDING_SERVICE_DATA_DIR"
mkdir -p "$INTELLIGENCE_SERVICE_DATA_DIR"

sudo ln -sfn "$SERGEANT_SERVICE_DATA_DIR" "/var/snap/microk8s/common/sergeant_service"
sudo ln -sfn "$VECTOR_EMBEDDING_SERVICE_DATA_DIR" "/var/snap/microk8s/common/vector_embedding_service"
sudo ln -sfn "$INTELLIGENCE_SERVICE_DATA_DIR" "/var/snap/microk8s/common/intelligence_service"


# Lieutenant
sudo microk8s kubectl create secret generic lieutenant-secrets \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
  --from-literal=DATABASE_URL="${DATABASE_URL}" \
  --from-literal=SENTRY_DSN="${SENTRY_DSN}" \
  --from-literal=OPENAI_COMPATIBLE_API_BASE_URL="${OPENAI_COMPATIBLE_API_BASE_URL}" \
  --from-literal=OPENAI_COMPATIBLE_API_KEY="${OPENAI_COMPATIBLE_API_KEY}" \
  --from-literal=MICROSOFT_CLIENT_ID="${MICROSOFT_CLIENT_ID}" \
  --from-literal=MICROSOFT_CLIENT_SECRET="${MICROSOFT_CLIENT_SECRET}" \
  --from-literal=MICROSOFT_CLIENT_TENANT_ID="${MICROSOFT_CLIENT_TENANT_ID}" \
  --from-literal=VECTOR_EMBEDDING_BASE_URL="${VECTOR_EMBEDDING_BASE_URL}" \
  --from-literal=VECTOR_EMBEDDING_API_KEY="${VECTOR_EMBEDDING_API_KEY}" \
  --from-literal=VECTOR_EMBEDDING_SERVICE_DATABASE_URL="${VECTOR_EMBEDDING_SERVICE_DATABASE_URL}" \
  --dry-run=client -o yaml | sudo microk8s kubectl apply -f -
sudo microk8s kubectl apply -f lieutenant.yml

# Gateway
sudo microk8s kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}" \
  --dry-run=client -o yaml | sudo microk8s kubectl apply -f -
sudo microk8s kubectl apply -f gateway.yml


# Monitor the deployment
sudo microk8s kubectl describe pod -l app=lieutenant
echo "---"
echo "Waiting for Lieutenant's containers to be initialized"
echo "---"
sudo microk8s kubectl wait --for=condition=Ready pod -l app=lieutenant --timeout=600s
sudo microk8s kubectl logs -f -l app=lieutenant --all-containers=true