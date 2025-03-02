#!/bin/bash

#CRON_JOBS=(
#    "*/5 * * * * /usr/bin/curl -X POST http://lieutenant-service:83/http_blob \
#    -H 'Content-Type: application/json' \
#    -H 'Authorization: Bearer YOUR_AUTH_TOKEN' \
#    -d '{\"source\": \"https://testlieutenant.blob.core.windows.net/test/Operation%20Prosperity%20Guardian.md?sp=r&st=2025-03-02T08:27:45Z&se=2025-12-31T16:27:45Z&spr=https&sv=2022-11-02&sr=b&sig=nhQlmbq6YGh3Y7RGIsxsMQv889vPIoCCcA1iRDx%2Fidc%3D\", \"description\": \"Funds are ready in the case of a parent's severe illness\"}'"
#
#    # Additional jobs can be added below this line
#    # "0 * * * * /usr/bin/curl -X POST http://your-domain.com/another-scheduled-task"
#)
#
#apt update && apt install -y cron
#(crontab -l 2>/dev/null; for job in "${CRON_JOBS[@]}"; do echo "$job"; done) | crontab -
#
#echo "✅ Cron jobs added successfully."

echo "startup.sh completed successfully"