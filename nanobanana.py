"""Nano Banana image API client: Nano Banana Pro, Nano Banana 2 and Nano Banana 2 Lite.

Standard library only (Python 3.8+). It speaks the OpenAI-style Images protocol
(POST /v1/images/generations and POST /v1/images/edits); the default base URL is ArgoLink's.

    export NANO_BANANA_API_KEY=...
    python nanobanana.py "A green glass bottle on wet stone, studio light" --model nano-banana-pro --resolution 4k
    python nanobanana.py "Put this bottle on a beach at sunset" --ref bottle.png --aspect-ratio 4:3
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE_URL = "https://argolink.io/v1"
DEFAULT_MODEL = "nano-banana-2"
# Some CDNs reject the default "Python-urllib" agent outright (HTTP 403), so name the client.
USER_AGENT = "nanobanana-python/1.0"

TEN_RATIOS = ("1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9")

# Per returned image, USD, from the model pages (checked 2026-10-07).
MODELS = {
    "nano-banana-pro": {"ratios": TEN_RATIOS, "price": {"1k": 0.03, "2k": 0.03, "4k": 0.03}},
    "nano-banana-2": {"ratios": TEN_RATIOS + ("1:4", "4:1", "1:8", "8:1"), "price": {"1k": 0.02, "2k": 0.02, "4k": 0.025}},
    "nano-banana-2-lite": {"ratios": TEN_RATIOS, "price": {"1k": 0.01}},
}
MAX_IMAGES_PER_REQUEST = 4
MAX_REFERENCES = 14


class NanoBananaError(RuntimeError):
    """A request was rejected locally or by the API."""

    def __init__(self, message: str, status: int | None = None, body: object = None):
        super().__init__(message)
        self.status = status
        self.body = body


def check(model: str, aspect_ratio: str | None = None, resolution: str | None = None,
          n: int = 1, references: int = 0) -> None:
    """Reject a request the API would refuse, before it costs anything."""
    spec = MODELS.get(model)
    if spec is None:
        raise NanoBananaError(f"unknown model {model!r}; expected one of {', '.join(MODELS)}")
    if aspect_ratio is not None and aspect_ratio not in spec["ratios"]:
        raise NanoBananaError(f"{model} does not take aspect_ratio {aspect_ratio}")
    if resolution is not None and resolution not in spec["price"]:
        raise NanoBananaError(f"{model} renders {', '.join(spec['price'])} only, not {resolution}")
    if not 1 <= n <= MAX_IMAGES_PER_REQUEST:
        raise NanoBananaError(f"n must be 1-{MAX_IMAGES_PER_REQUEST}")
    if references > MAX_REFERENCES:
        raise NanoBananaError(f"an edit takes at most {MAX_REFERENCES} reference images, got {references}")


def price(model: str, resolution: str | None = None, images: int = 1) -> float:
    """Cost of `images` returned images at one tier. Every returned image is billed."""
    return round(MODELS[model]["price"][resolution or "1k"] * images, 4)


def _is_url(reference: str) -> bool:
    return reference.startswith(("https://", "http://", "data:"))


def _data_url(path: str) -> str:
    content_type = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as handle:
        return f"data:{content_type};base64,{base64.b64encode(handle.read()).decode()}"


def _multipart(fields: list, files: list) -> tuple:
    boundary = uuid.uuid4().hex
    body = bytearray()
    for name, value in fields:
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()
    for name, path in files:
        filename = os.path.basename(path).replace('"', "_")
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as handle:
            data = handle.read()
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                 f"Content-Type: {content_type}\r\n\r\n").encode() + data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


class NanoBanana:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 600,
                 validate: bool = True):
        self.api_key = api_key or os.environ.get("NANO_BANANA_API_KEY")
        if not self.api_key:
            raise NanoBananaError("set NANO_BANANA_API_KEY or pass api_key")
        self.base_url = (base_url or os.environ.get("NANO_BANANA_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout  # the request returns only when every image is ready
        self.validate = validate

    def _send(self, path: str, data: bytes, content_type: str) -> list:
        request = urllib.request.Request(self.base_url + path, data=data, method="POST")
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("User-Agent", USER_AGENT)
        request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as error:
            text = error.read().decode(errors="replace")
            try:
                detail = json.loads(text)
            except ValueError:
                detail = text
            raise NanoBananaError(f"POST {path} returned {error.code}: {text[:300]}", error.code, detail) from None
        return [base64.b64decode(item["b64_json"]) for item in payload.get("data", [])]

    @staticmethod
    def _fields(model: str, prompt: str, aspect_ratio, resolution, n) -> dict:
        body = {"model": model, "prompt": prompt, "n": n}
        if aspect_ratio:
            body["aspect_ratio"] = aspect_ratio
        if resolution:
            body["resolution"] = resolution
        return body

    def generate(self, prompt: str, model: str = DEFAULT_MODEL, aspect_ratio: str | None = None,
                 resolution: str | None = None, n: int = 1) -> list:
        """Text to image. Returns the JPEG bytes of every image (aspect_ratio 1:1 and 1k when left out)."""
        if self.validate:
            check(model, aspect_ratio, resolution, n)
        body = self._fields(model, prompt, aspect_ratio, resolution, n)
        return self._send("/images/generations", json.dumps(body).encode(), "application/json")

    def edit(self, prompt: str, references: list, model: str = DEFAULT_MODEL, aspect_ratio: str | None = None,
             resolution: str | None = None, n: int = 1) -> list:
        """Image to image with 1-14 references: HTTPS URLs, data URLs or local file paths.

        URLs go as JSON images[].image_url; local files go as repeated multipart image[] fields.
        A mix is sent as JSON, with the local files turned into data URLs. The output frame is
        1:1 unless aspect_ratio is set: it does not follow the references.
        """
        if not references:
            raise NanoBananaError("an edit needs at least one reference image")
        if self.validate:
            check(model, aspect_ratio, resolution, n, len(references))
        fields = self._fields(model, prompt, aspect_ratio, resolution, n)
        if all(not _is_url(ref) for ref in references):
            data, content_type = _multipart(list(fields.items()), [("image[]", ref) for ref in references])
            return self._send("/images/edits", data, content_type)
        fields["images"] = [{"image_url": ref if _is_url(ref) else _data_url(ref)} for ref in references]
        return self._send("/images/edits", json.dumps(fields).encode(), "application/json")


def save(images: list, prefix: str = "nano-banana") -> list:
    """Write each image as <prefix>-<n>.jpg (the API returns JPEG) and return the paths."""
    paths = []
    for index, image in enumerate(images, 1):
        path = f"{prefix}-{index}.jpg"
        with open(path, "wb") as handle:
            handle.write(image)
        paths.append(path)
    return paths


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or edit images with Nano Banana Pro / 2 / 2 Lite.")
    parser.add_argument("prompt")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(MODELS))
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--resolution", choices=("1k", "2k", "4k"))
    parser.add_argument("-n", type=int, default=1, help="images per request, 1-4, each billed")
    parser.add_argument("--ref", action="append", default=[], help="reference image: path or URL (repeat up to 14)")
    parser.add_argument("--out", default="nano-banana", help="output file prefix")
    parser.add_argument("--dry-run", action="store_true", help="validate and print the cost, send nothing")
    args = parser.parse_args(argv)

    check(args.model, args.aspect_ratio, args.resolution, args.n, len(args.ref))
    estimate = price(args.model, args.resolution, args.n)
    if args.dry_run:
        print(f"{args.model} x{args.n} at {args.resolution or '1k'}: ${estimate:.3f}")
        return 0
    client = NanoBanana()
    if args.ref:
        images = client.edit(args.prompt, args.ref, args.model, args.aspect_ratio, args.resolution, args.n)
    else:
        images = client.generate(args.prompt, args.model, args.aspect_ratio, args.resolution, args.n)
    for path in save(images, args.out):
        print(path)
    print(f"billed images: {len(images)}, about ${price(args.model, args.resolution, len(images)):.3f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except NanoBananaError as error:
        sys.exit(f"error: {error}")
