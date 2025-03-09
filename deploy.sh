#!/bin/bash

# Download files
ENVIRONMENT=${ENVIRONMENT:-main}
sudo apt install curl -y
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENVIRONMENT/lieutenant.yml
curl -O https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$ENVIRONMENT/gateway.yml

# Install microk8s
if ! microk8s version &>/dev/null; then
    sudo snap install microk8s --classic
fi
sudo usermod -a -G microk8s $USER
if ! groups | grep -q "\bmicrok8s\b"; then
  newgrp microk8s
fi

# Lieutenant
microk8s kubectl create secret generic lieutenant-secrets \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
  --from-literal=DATABASE_URL="${DATABASE_URL}" \
  --from-literal=SENTRY_DSN="${SENTRY_DSN}" \
  --from-literal=GOOGLE_PSE_API_KEY="${GOOGLE_PSE_API_KEY}" \
  --from-literal=GOOGLE_PSE_ENGINE_ID="${GOOGLE_PSE_ENGINE_ID}" \
  --from-literal=MICROSOFT_CLIENT_ID="${MICROSOFT_CLIENT_ID}" \
  --from-literal=MICROSOFT_CLIENT_SECRET="${MICROSOFT_CLIENT_SECRET}" \
  --from-literal=MICROSOFT_CLIENT_TENANT_ID="${MICROSOFT_CLIENT_TENANT_ID}" \
  --from-literal=VECTOR_EMBEDDING_SERVICE_DATABASE_URL="${VECTOR_EMBEDDING_SERVICE_DATABASE_URL}" \
  --dry-run=client -o yaml | microk8s kubectl apply -f -
microk8s kubectl apply -f lieutenant.yml

# Gateway
microk8s kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}" \
  --dry-run=client -o yaml | microk8s kubectl apply -f -
microk8s kubectl apply -f gateway.yml


# Monitor the deployment
microk8s kubectl describe pod -l app=lieutenant
echo "---"
echo "Waiting for Lieutenant's containers to be initialized"
echo "---"
microk8s kubectl wait --for=condition=Ready pod -l app=lieutenant --timeout=600s
microk8s kubectl logs -f -l app=lieutenant --all-containers=true