#!/bin/bash

# Download the necessary files
if [ -z "$ENVIRONMENT" ] || [ "$ENVIRONMENT" = "production" ]; then
  export BRANCH="main"
  export TAG="latest"
fi
if ! command -v curl &>/dev/null; then
    sudo apt update && sudo apt install -y curl
fi
curl -O "https://raw.githubusercontent.com/lieutenant-ecosystem/lieutenant/refs/heads/$BRANCH/infrastructure/docker/docker-compose.yml"

# Install docker
if ! sudo docker --version &>/dev/null; then
    sudo snap install docker
    sudo usermod -aG docker $USER
    newgrp docker
fi

# Prepare the symlinks for data persistence
APP_DATA_DIR="$HOME/app_data"
export SERGEANT_SERVICE_DATA_DIR="$APP_DATA_DIR/sergeant_service/data/"
export VECTOR_EMBEDDING_SERVICE_DATA_DIR="$APP_DATA_DIR/vector_embedding_service/data/"
export INTELLIGENCE_SERVICE_DATA_DIR="$APP_DATA_DIR/intelligence_service/data/"

mkdir -p "$SERGEANT_SERVICE_DATA_DIR"
mkdir -p "$VECTOR_EMBEDDING_SERVICE_DATA_DIR"
mkdir -p "$INTELLIGENCE_SERVICE_DATA_DIR"

# Lieutenant
if [ -z "$VECTOR_EMBEDDING_SERVICE_DATABASE_URL" ]; then
  export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:=samerandominsecurepassword}
  export DATABASE_URL=postgresql://lieutenant:samerandominsecurepassword@postgres-service:5432/lieutenant-open_webui
  export VECTOR_EMBEDDING_SERVICE_DATABASE_URL=$DATABASE_URL
  docker compose up
else
  docker-compose up --scale postgres-service=0   # Skips deploying the database if the environment is not a development one (remember to remove the health checks from the YAML file)
fi