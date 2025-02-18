#!/bin/bash

# Install microk8s
set +e
sudo snap install microk8s --classic
sudo usermod -a -G microk8s $USER
newgrp microk8s

# Resetting the environment
microk8s kubectl delete pods -n container-registry --all && docker rm $(docker ps -aq)
docker system prune -a -f
set -e

# Enable the registry
sudo microk8s enable registry

# Build the images
docker build -t localhost:32000/sergeant_service:local sergeant_service
docker build -t localhost:32000/open_webui:local open_webui
docker build -t localhost:32000/gateway:local gateway

# Push the images to the registry
docker push localhost:32000/sergeant_service:local
docker push localhost:32000/open_webui:local
docker push localhost:32000/gateway:local

# Deploy

## Postgres SQL database
if [ "$ENVIRONMENT" = "dev" ]; then
  POSTGRES_PASSWORD=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 10)
  DATABASE_URL=postgresql://lieutenant:$POSTGRES_PASSWORD@postgres-service:5432/lieutenant-open_webui
  microk8s kubectl create secret generic database-secrets \
    --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
  microk8s kubectl delete -f dev/database.yml && microk8s kubectl apply -f dev/database.yml
fi

##  Lieutenant
microk8s kubectl create secret generic lieutenant-secrets \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
  --from-literal=DATABASE_URL="${DATABASE_URL}" \
  --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  --from-literal=PPLX_API_KEY="${PPLX_API_KEY}" \
  --from-literal=SENTRY_DSN="${SENTRY_DSN}" \
  --from-literal=GOOGLE_PSE_API_KEY="${GOOGLE_PSE_API_KEY}" \
  --from-literal=GOOGLE_PSE_ENGINE_ID="${GOOGLE_PSE_ENGINE_ID}" \
  --from-literal=MICROSOFT_CLIENT_ID="${MICROSOFT_CLIENT_ID}" \
  --from-literal=MICROSOFT_CLIENT_SECRET="${MICROSOFT_CLIENT_SECRET}" \
  --from-literal=MICROSOFT_CLIENT_TENANT_ID="${MICROSOFT_CLIENT_TENANT_ID}"
microk8s kubectl delete -f dev/lieutenant.yml && microk8s kubectl apply -f dev/lieutenant.yml

##  Gateway
microk8s kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}"
microk8s kubectl delete -f dev/gateway.yml && microk8s kubectl apply -f dev/gateway.yml