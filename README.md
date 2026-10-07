# Nano Banana API — from $0.01/image (1K, Nano Banana 2 Lite)

**Google Nano Banana Pro, Nano Banana 2 and Nano Banana 2 Lite are live on [ArgoLink](https://argolink.io/gh-nano-banana-api)**: Pro at $0.03/image for 1K, 2K or 4K, Nano Banana 2 at $0.02 (1K/2K) and $0.025 (4K), 2 Lite at $0.01, 70–88% below Google's Gemini API list price. Text-to-image and image-to-image with up to 14 reference images, 10 or 14 aspect ratios and 1–4 images per request, all on two OpenAI-style Images endpoints.

[Model pages →](https://argolink.io/en/models/nano-banana-pro) · [Prices](#price-per-image) · [Quick start](#quick-start) · [Parameters](#parameters) · [Which model](#which-model) · [FAQ](#faq)

This repo has a dependency-free client for [Python](./nanobanana.py) and [Node.js](./nanobanana.mjs), three [examples](./examples) and offline [tests](./tests). Point `NANO_BANANA_BASE_URL` at any endpoint that speaks the same Images protocol.

<sub>Last checked: 2026-10-07, against the pages linked in each table.</sub>

## At a glance

| | Nano Banana Pro | Nano Banana 2 | Nano Banana 2 Lite |
|---|---|---|---|
| Model ID | `nano-banana-pro` | `nano-banana-2` | `nano-banana-2-lite` |
| Google's name for it | Gemini 3 Pro Image | Gemini 3.1 Flash Image | Gemini 3.1 Flash Lite Image |
| `resolution` | `1k` · `2k` · `4k` | `1k` · `2k` · `4k` | `1k` |
| `aspect_ratio` | 1:1 16:9 9:16 4:3 3:4 3:2 2:3 5:4 4:5 21:9 | the same ten plus 1:4 4:1 1:8 8:1 | the same ten as Pro |
| Reference images (edits) | up to 14 | up to 14 | up to 14 |
| Images per request (`n`) | 1–4 | 1–4 | 1–4 |
| Output | JPEG, base64 in `data[].b64_json` | same | same |
| Price per returned image | $0.03 at every tier | $0.02 at 1K/2K, $0.025 at 4K | $0.01 |

Endpoints: `POST /v1/images/generations` (JSON) for text to image, `POST /v1/images/edits` (JSON links or multipart files) for image to image. Both answer once every image is ready, so give your HTTP client a timeout of at least 600 seconds.

## Price per image

One returned image, standard (non-batch) rates, each provider's own figure.

| Model · tier | ArgoLink | Google Gemini API | fal.ai | Replicate |
|---|---:|---:|---:|---:|
| Nano Banana Pro · 1K | **$0.03** | $0.134 | $0.15 | $0.15 |
| Nano Banana Pro · 2K | **$0.03** | $0.134 | $0.15 | $0.15 |
| Nano Banana Pro · 4K | **$0.03** | $0.24 | $0.30 | $0.30 |
| Nano Banana 2 · 1K | **$0.02** | $0.067 | $0.08 | $0.067 |
| Nano Banana 2 · 2K | **$0.02** | $0.101 | $0.12 | $0.101 |
| Nano Banana 2 · 4K | **$0.025** | $0.151 | $0.16 | $0.151 |
| Nano Banana 2 Lite · 1K | **$0.01** | $0.0336 | — | $0.034 |

<sub>Sources, all checked 2026-10-07: [ArgoLink model pages](https://argolink.io/en/models/nano-banana-2); [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) (Google states image output as tokens, $120/M for Pro and $60/M for Nano Banana 2, and gives these per-image equivalents; prompt and input-image tokens are extra); fal [nano-banana-pro](https://fal.ai/models/fal-ai/nano-banana-pro) ($0.15, 4K at double) and [nano-banana-2](https://fal.ai/models/fal-ai/nano-banana-2) ($0.08, 2K ×1.5, 4K ×2), both plus $0.015 when web search is used; Replicate [google/nano-banana-pro](https://replicate.com/google/nano-banana-pro), [google/nano-banana-2](https://replicate.com/google/nano-banana-2), [google/nano-banana-2-lite](https://replicate.com/google/nano-banana-2-lite). The pages win if they change.</sub>

What a batch costs: 100 product shots at 2K are $3.00 on Pro or $2.00 on Nano Banana 2 here, against $13.40 / $10.10 at Google's list price.

## Quick start

```bash
git clone https://github.com/colinjaspers/nano-banana-api
cd nano-banana-api
export NANO_BANANA_API_KEY=your-key        # create one at argolink.io

python nanobanana.py "A green glass bottle on wet black stone, studio rim light" \
  --model nano-banana-pro --aspect-ratio 16:9 --resolution 4k
python nanobanana.py "Same bottle on a beach at sunset" --ref nano-banana-1.jpg --aspect-ratio 16:9 --out beach
node nanobanana.mjs "A paper lantern on a quiet desk" nano-banana-2 2k
```

Each run writes `nano-banana-1.jpg` (and `-2`, `-3`, … when `-n` is above 1) and prints what it cost. `--dry-run` checks the request against the limits above and prints the price without sending anything.

### cURL

```bash
BASE=https://argolink.io/v1

# Text to image
curl -sS --max-time 600 $BASE/images/generations \
  -H "Authorization: Bearer $NANO_BANANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nano-banana-2", "prompt": "Isometric ramen shop at night, rain", "aspect_ratio": "16:9", "resolution": "2k"}' \
  | jq -r '.data[0].b64_json' | base64 --decode > ramen.jpg

# Image to image with links (public HTTPS URLs or data URLs)
curl -sS --max-time 600 $BASE/images/edits \
  -H "Authorization: Bearer $NANO_BANANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano-banana-pro",
    "prompt": "Keep the bottle exactly, move it onto a beach at sunset",
    "images": [{"image_url": "https://example.com/bottle.png"}],
    "aspect_ratio": "4:3",
    "resolution": "4k"
  }' -o edit.json

# Image to image with local files: repeat image[] once per file
curl -sS --max-time 600 $BASE/images/edits \
  -H "Authorization: Bearer $NANO_BANANA_API_KEY" \
  -F model=nano-banana-2 -F "prompt=Combine both products into one flat lay" \
  -F "image[]=@./mug.png" -F "image[]=@./notebook.png" \
  -F aspect_ratio=1:1 -F resolution=2k -o edit.json
```

### Python

```python
from nanobanana import NanoBanana, save

client = NanoBanana()  # NANO_BANANA_API_KEY, optional NANO_BANANA_BASE_URL
images = client.generate("Watercolor map of Kyoto, labelled districts", model="nano-banana-pro",
                         aspect_ratio="3:4", resolution="2k", n=2)
save(images, "kyoto")                       # kyoto-1.jpg, kyoto-2.jpg: two images, $0.06
edited = client.edit("Make it autumn", ["kyoto-1.jpg"], model="nano-banana-2", aspect_ratio="3:4")
```

### Node.js

```js
import { NanoBanana, save } from "./nanobanana.mjs";

const client = new NanoBanana();
const images = await client.edit("Put the sneaker on a concrete plinth, hard noon light",
  ["https://example.com/sneaker.png"], { model: "nano-banana-pro", aspectRatio: "4:3", resolution: "4k" });
await save(images, "sneaker");
```

More: [text_to_image.sh](./examples/text_to_image.sh), [edit_local_files.py](./examples/edit_local_files.py), and [draft_then_final.mjs](./examples/draft_then_final.mjs), which drafts four 1K options on 2 Lite and finishes the chosen one on Pro at 4K for $0.07 in total.

## Parameters

| Field | Endpoint | Values |
|---|---|---|
| `model` | both | `nano-banana-pro`, `nano-banana-2`, `nano-banana-2-lite` |
| `prompt` | both | required; for an edit, say what to keep and what to change |
| `aspect_ratio` | both | see the table above; **1:1 when left out, for edits too**: the frame never follows the references |
| `resolution` | both | `1k` (default), `2k`, `4k`; 2 Lite takes `1k` only |
| `n` | both | 1–4, default 1; every returned image is billed |
| `response_format` | both | `b64_json` only, so you can leave it out; `url` is rejected |
| `images` | edits, JSON | `[{"image_url": "https://…"}, …]`, public HTTPS or data URLs, up to 14 |
| `image[]` | edits, multipart | one field per local file, up to 14 |

One edit request is either JSON or multipart. The clients in this repo pick for you: links go as JSON, local files as multipart, and a mix as JSON with the files turned into data URLs.

## Which model

| You need | Use | Why |
|---|---|---|
| Many cheap drafts, thumbnails, A/B variants | `nano-banana-2-lite` | $0.01 at 1K; 1K is its only tier |
| Production images, banners, extreme formats | `nano-banana-2` | 2K at $0.02, 4K at $0.025, and the only one with 1:4, 4:1, 1:8 and 8:1 |
| Final assets where quality matters most | `nano-banana-pro` | one price for 1K, 2K and 4K, so render finals at 4K |

## Migrating from fal

| fal | Here |
|---|---|
| `fal-ai/nano-banana-pro` and `fal-ai/nano-banana-pro/edit` | one model ID, two endpoints: `/v1/images/generations` and `/v1/images/edits` |
| `num_images` | `n` (1–4) |
| `resolution: "1K"` / `"2K"` / `"4K"` | `resolution: "1k"` / `"2k"` / `"4k"`, lowercase |
| `image_urls: ["https://…"]` | `images: [{"image_url": "https://…"}]` |
| `aspect_ratio: "auto"` | not in the list; leave the field out for 1:1 or name a ratio |
| `output_format: "png"` | JPEG only; convert after download if you need PNG |

## FAQ

**Is Nano Banana Pro the same model as Gemini 3 Pro Image?**
Google's pricing page lists "Gemini 3 Pro Image (Nano Banana Pro)", model ID `gemini-3-pro-image`, and "Gemini 3.1 Flash Image (Nano Banana 2)". On ArgoLink the publisher is Google and the IDs are `nano-banana-pro` and `nano-banana-2`.

**Why is 4K the same price as 1K on Nano Banana Pro?**
ArgoLink bills Pro at $0.03 per returned image whatever the tier. Google's own rate rises from $0.134 at 1K/2K to $0.24 at 4K, and fal's and Replicate's double at 4K. If you use Pro, render at 4K.

**Can I get a PNG or an image URL back?**
No. All three models return JPEG as base64 in `data[].b64_json`; `response_format: "url"` is rejected. Decode it (`base64 --decode`) and convert locally if you need another format.

**How many reference images can an edit take, and how do I send them?**
Up to 14. Public HTTPS URLs or data URLs go in a JSON `images` array as `{"image_url": …}` objects; local files go as multipart, one `image[]` field per file. Don't join several paths into one field.

**Why did my edit come back square?**
`aspect_ratio` defaults to 1:1 for edits as well as for generation. Send the ratio you want with every edit.

**Why does a request take minutes, and what timeout should I use?**
The endpoint replies only when every image is finished, and 2K/4K renders take longer. Use a timeout of 600 seconds or more; the clients here default to 600.

## Run the tests

```bash
pip install pytest
pytest tests/
```

The tests replace the HTTP layer, so they need no key and spend nothing.

## License

MIT. Not affiliated with Google; Nano Banana and Gemini are Google's names for its models.
