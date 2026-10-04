# Nano Banana API

A focused Argolink guide for Nano Banana image generation and reference editing. The public examples use only Argolink hosts and environment-based credentials.

[Open the Argolink API docs →](https://argolink.io/gh-nano-banana-api)

## What is covered

- model selection and capability discovery;
- text-to-image and image-to-image requests;
- aspect ratio, resolution, reference input, and output handling;
- credential hygiene and failure diagnosis.

See [`docs/nano-banana-api.md`](./docs/nano-banana-api.md) for JSON and multipart examples.

## Public contract boundary

This repository is an integration aid, not an authority for prices or availability. Read the linked Argolink model or API page immediately before deployment. Runtime access uses `ARGOLINK_API_KEY`; do not copy a key into source, issues, screenshots, or generated artifacts.

## Repository map

- [`ARGOLINK.md`](./ARGOLINK.md): scope and public boundary.
- [`docs/`](./docs): durable request and validation notes.
- [`examples/`](./examples): runnable, credential-free examples.
- [`argolink/`](./argolink): Argolink-specific mapping and review checklist.
- [`ARGOLINK_LINKS.md`](./ARGOLINK_LINKS.md): tracked landing link.
