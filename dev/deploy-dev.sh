#!/bin/bash

# Install microk8s
sudo snap install microk8s --classic
usermod -a -G microk8s $USER
usermod -aG docker $USER
newgrp microk8s
newgrp docker
alias kubectl="microk8s kubectl"

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
##  Lieutenant
kubectl create secret generic lieutenant-secrets \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
  --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  --from-literal=PPLX_API_KEY="${PPLX_API_KEY}" \
  --from-literal=SENTRY_DSN="${SENTRY_DSN}" \
  --from-literal=GOOGLE_PSE_API_KEY="${GOOGLE_PSE_API_KEY}" \
  --from-literal=GOOGLE_PSE_ENGINE_ID="${GOOGLE_PSE_ENGINE_ID}" \
  --from-literal=MICROSOFT_CLIENT_ID="${MICROSOFT_CLIENT_ID}" \
  --from-literal=MICROSOFT_CLIENT_SECRET="${MICROSOFT_CLIENT_SECRET}" \
  --from-literal=MICROSOFT_CLIENT_TENANT_ID="${MICROSOFT_CLIENT_TENANT_ID}"
kubectl apply -f dev/lieutenant.yml

##  Gateway
kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}"
kubectl apply -f dev/gateway.yml