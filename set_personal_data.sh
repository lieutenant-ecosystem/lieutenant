#!/bin/bash
set -euo pipefail

POD_NAME=$(microk8s kubectl get pods -l app=lieutenant -o jsonpath="{.items[0].metadata.name}")
CONTAINER_NAME="intelligence-service"

send_request() {
  local description="$1"
  local source="$2"

  payload=$(jq -n --arg id "optional-id" \
                 --arg description "$description" \
                 --arg source "$source" \
                 '{id: $id, description: $description, source: $source}')
  escaped_payload=$(printf "%s" "$payload" | sed "s/'/'\\''/g")
  remote_cmd="curl -X POST \"http://0.0.0.0:8002/http_blob\" \
    -H \"Content-Type: application/json\" \
    -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" \
    -d '$escaped_payload' | tee /tmp/curl_output.log"

  microk8s kubectl exec -it "$POD_NAME" -c "$CONTAINER_NAME" -- sh -c "$remote_cmd"
}

send_request "'$YOUR_DESCRIPTION'" "'$YOUR_SOURCE_URL'"