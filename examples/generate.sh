#!/usr/bin/env bash
set -euo pipefail
: "${ARGOLINK_API_KEY:?set ARGOLINK_API_KEY first}"
curl -fsS https://api.argolink.io/v1/images/generations \
  -H "Authorization: Bearer $ARGOLINK_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"nano-banana-2","prompt":"A paper lantern on a quiet desk","aspect_ratio":"1:1","resolution":"1k"}' | jq .
