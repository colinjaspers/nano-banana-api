#!/usr/bin/env bash
# Text to image with Nano Banana 2 at 2K, 16:9. The response carries the JPEG as base64.
set -euo pipefail
: "${NANO_BANANA_API_KEY:?export NANO_BANANA_API_KEY first}"
BASE="${NANO_BANANA_BASE_URL:-https://argolink.io/v1}"

curl -fsS --max-time 600 "$BASE/images/generations" \
  -H "Authorization: Bearer $NANO_BANANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano-banana-2",
    "prompt": "Isometric cutaway of a tiny ramen shop at night, warm lantern light, rain on the street",
    "aspect_ratio": "16:9",
    "resolution": "2k",
    "n": 1
  }' -o response.json

jq -r '.data[0].b64_json' response.json | base64 --decode > ramen-shop.jpg   # older macOS: base64 -D
echo "saved ramen-shop.jpg (billed: 1 image at 2K = \$0.02)"
