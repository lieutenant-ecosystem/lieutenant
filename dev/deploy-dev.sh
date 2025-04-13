#!/bin/bash

# Install docker & microk8s
if ! docker version &>/dev/null; then
    sudo snap install docker
fi
if ! microk8s version &>/dev/null; then
    sudo snap install microk8s --classic
fi
sudo usermod -a -G microk8s $USER
if ! groups | grep -q "\bmicrok8s\b"; then
  newgrp microk8s
fi

# Set the environment variables
set -a; source .env_local; set +a

# Resetting the environment
sudo microk8s kubectl delete deployments --all

# Enable the registry
sudo microk8s enable registry

# Build the images
#docker build -t localhost:32000/sergeant_service:local sergeant_service
#docker build -t localhost:32000/vector_embedding_service:local vector_embedding_service
#docker build -t localhost:32000/intelligence_service:local intelligence_service
docker build -t localhost:32000/open_webui:local open_webui
docker build -t localhost:32000/gateway:local gateway

# Push the images to the registry
#docker push localhost:32000/sergeant_service:local
#docker push localhost:32000/vector_embedding_service:local
#docker push localhost:32000/intelligence_service:local
docker push localhost:32000/open_webui:local
docker push localhost:32000/gateway:local

# Prepare the symlinks for data persistence
sudo ln -sfn "$HOME/Documents/Codebase/lieutenant/sergeant_service/data/" "/var/snap/microk8s/common/sergeant_service"
sudo ln -sfn "$HOME/Documents/Codebase/lieutenant/vector_embedding_service/data/" "/var/snap/microk8s/common/vector_embedding_service"
sudo ln -sfn "$HOME/Documents/Codebase/lieutenant/intelligence_service/data/" "/var/snap/microk8s/common/intelligence_service"


# Deploy

## Postgres SQL database
if [ "$ENVIRONMENT" = "dev" ]; then
  sudo microk8s kubectl create secret generic database-secrets \
    --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
    --dry-run=client -o yaml | sudo microk8s kubectl apply -f -
  sudo microk8s kubectl delete -f dev/database.yml --ignore-not-found=true
  sudo microk8s kubectl apply -f dev/database.yml

  counter=0
  while ! nc -z localhost 5432; do
    echo "Waiting for database to load for $counter seconds..."
    sleep 1
    ((counter++))
  done
  echo "Database port opened successfully in $counter seconds"
fi

##  Lieutenant
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
  --from-literal=VECTOR_EMBEDDING_SERVICE_DEFAULT_MODEL="${VECTOR_EMBEDDING_SERVICE_DEFAULT_MODEL}" \
  --from-literal=VECTOR_EMBEDDING_SERVICE_DATABASE_URL="${VECTOR_EMBEDDING_SERVICE_DATABASE_URL}" \
  --dry-run=client -o yaml | sudo microk8s kubectl apply -f -
sudo microk8s kubectl delete -f dev/lieutenant.yml --ignore-not-found=true
sudo microk8s kubectl apply -f dev/lieutenant.yml

##  Gateway
sudo microk8s kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}" \
  --dry-run=client -o yaml | sudo microk8s kubectl apply -f -
sudo microk8s kubectl delete -f dev/gateway.yml --ignore-not-found=true
sudo microk8s kubectl apply -f dev/gateway.yml

# Tail the logs
sudo microk8s kubectl describe pod -l app=lieutenant
sudo microk8s kubectl wait --for=condition=Ready pod -l app=lieutenant --timeout=600s
sudo microk8s kubectl logs -f -l app=lieutenant --all-containers=true