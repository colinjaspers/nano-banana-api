# Nano Banana image contract

Argolink exposes Nano Banana image generation and editing through an Images-compatible JSON or multipart surface. Model IDs are `nano-banana-2`, `nano-banana-2-lite`, and `nano-banana-pro`.

## Endpoints

| Use | Route |
| --- | --- |
| Text-to-image | `POST /v1/images/generations` |
| Image-to-image edit | `POST /v1/images/edits` |
| Authentication | `Authorization: Bearer $ARGOLINK_API_KEY` |

## Generation

```bash
export ARGOLINK_API_KEY='replace-me'
curl -fsS https://api.argolink.io/v1/images/generations \
  -H "Authorization: Bearer $ARGOLINK_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{{
    "model": "nano-banana-2",
    "prompt": "A clean studio product photograph of a red ceramic cup",
    "aspect_ratio": "1:1",
    "resolution": "2k"
  }}' | jq .
```

## Editing

Use `/v1/images/edits` with a JSON HTTPS image reference or the documented multipart upload. `nano-banana-2` accepts the ten common ratios plus `1:4`, `4:1`, `1:8`, and `8:1`; the professional and lite variants use the common ten ratios. Professional and standard variants accept `1k`, `2k`, and `4k`; the lite variant is `1k`. Check the live page for any change.

## Output hygiene

Decode only the returned image field, write it to a controlled output directory, and never log base64 content or a customer image URL.
