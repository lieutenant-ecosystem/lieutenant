#!/bin/bash

# Install microk8s
if ! microk8s version &>/dev/null; then
    sudo snap install microk8s --classic
fi
sudo usermod -a -G microk8s $USER
if ! groups | grep -q "\bmicrok8s\b"; then
  newgrp microk8s
fi

# Resetting the environment
microk8s kubectl delete deployments --all
docker rmi $(docker images -q)
docker images --format "{{.Repository}} {{.ID}}" | awk '$1=="sergeant-service" || $1=="vector_embedding_service" {print $2}' | xargs -r docker rmi -f

# Enable the registry
sudo microk8s enable registry

# Build the images
docker build -t localhost:32000/sergeant_service:local sergeant_service
docker build -t localhost:32000/vector_embedding_service:local vector_embedding_service
docker build -t localhost:32000/open_webui:local open_webui
docker build -t localhost:32000/gateway:local gateway

# Push the images to the registry
docker push localhost:32000/sergeant_service:local
docker push localhost:32000/vector_embedding_service:local
docker push localhost:32000/open_webui:local
docker push localhost:32000/gateway:local

# Deploy

## Postgres SQL database
if [ "$ENVIRONMENT" = "dev" ]; then
  POSTGRES_PASSWORD=samerandominsecurepassword
  DATABASE_URL=postgresql://lieutenant:$POSTGRES_PASSWORD@postgres-service:5432/lieutenant-open_webui
  microk8s kubectl create secret generic database-secrets \
    --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
    --dry-run=client -o yaml | microk8s kubectl apply -f -
  microk8s kubectl apply -f dev/database.yml
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
  --from-literal=MICROSOFT_CLIENT_TENANT_ID="${MICROSOFT_CLIENT_TENANT_ID}" \
  --from-literal=VECTOR_EMBEDDING_BASE_URL="${VECTOR_EMBEDDING_BASE_URL}" \
  --from-literal=VECTOR_EMBEDDING_API_KEY="${VECTOR_EMBEDDING_API_KEY}" \
  --from-literal=VECTOR_EMBEDDING_SERVICE_DATABASE_URL="${VECTOR_EMBEDDING_SERVICE_DATABASE_URL}" \
  --dry-run=client -o yaml | microk8s kubectl apply -f -
microk8s kubectl apply -f dev/lieutenant.yml

##  Gateway
microk8s kubectl create secret generic gateway-secrets \
  --from-literal=CLOUDFLARE_TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN}" \
  --from-literal=SSH_USERNAME="${SSH_USERNAME}" \
  --from-literal=SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY}" \
  --dry-run=client -o yaml | microk8s kubectl apply -f -
microk8s kubectl apply -f dev/gateway.yml

# Port forward the database port
kubectl port-forward svc/postgres-service 5432:5432

# Tail the logs
microk8s kubectl describe pod -l app=lieutenant
microk8s kubectl wait --for=condition=Ready pod -l app=lieutenant --timeout=60s
microk8s kubectl logs -f -l app=lieutenant --all-containers=true