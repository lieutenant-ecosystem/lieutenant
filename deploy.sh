#!/bin/bash

# Download files
ENV=${1:-main}
sudo apt install curl -y
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENV/lieutenant.yml
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENV/gateway.yml

# Install microk8s
sudo snap install microk8s --classic
sudo usermod -a -G microk8s $USER
sudo usermod -aG docker $USER
newgrp microk8s
newgrp docker
alias microk8s kubectl="microk8s microk8s kubectl"

# Lieutenant
microk8s kubectl create secret generic lieutenant-secrets \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
  --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  --from-literal=PPLX_API_KEY="${PPLX_API_KEY}" \
  --from-literal=SENTRY_DSN="${SENTRY_DSN}" \
  --from-literal=GOOGLE_PSE_API_KEY="${GOOGLE_PSE_API_KEY}" \
  --from-literal=GOOGLE_PSE_ENGINE_ID="${GOOGLE_PSE_ENGINE_ID}" \
  --from-literal=MICROSOFT_CLIENT_ID="${MICROSOFT_CLIENT_ID}" \
  --from-literal=MICROSOFT_CLIENT_SECRET="${MICROSOFT_CLIENT_SECRET}" \
  --from-literal=MICROSOFT_CLIENT_TENANT_ID="${MICROSOFT_CLIENT_TENANT_ID}"
microk8s kubectl apply -f lieutenant.yml

# Gateway
microk8s kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}"
microk8s kubectl apply -f gateway.yml