#!/bin/bash
set -euo pipefail

POD_NAME=$(microk8s kubectl get pods -l app=lieutenant -o jsonpath="{.items[0].metadata.name}")
CONTAINER_NAME="intelligence-service"

send_request() {
  local index="$1"
  local description="$2"
  local source="$3"

  payload=$(jq -n --arg id "optional-id" \
                 --arg description "$description" \
                 --arg source "$source" \
                 --arg index "$index" \
                 '{id: $id, description: $description, source: $source, index: $index}')
  escaped_payload=$(printf "%s" "$payload" | sed "s/'/'\\''/g")
  remote_cmd="curl -X POST \"http://0.0.0.0:8002/http_blob\" \
    -H \"Content-Type: application/json\" \
    -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" \
    -d '$escaped_payload' | tee /tmp/curl_output.log"

  microk8s kubectl exec -it "$POD_NAME" -c "$CONTAINER_NAME" -- sh -c "$remote_cmd"
}

INDEX='Notes'
DESCRIPTION='Details about the user'
SOURCE='URL'
send_request "$INDEX" "$DESCRIPTION" "$SOURCE"