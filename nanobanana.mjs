// Nano Banana image API client for Node.js 18+ (built-in fetch, FormData and Blob; no dependencies).
//
//   export NANO_BANANA_API_KEY=...
//   node nanobanana.mjs "A green glass bottle on wet stone, studio light" nano-banana-pro 4k

import { readFile, writeFile } from "node:fs/promises";
import { basename, extname } from "node:path";

const DEFAULT_BASE_URL = "https://argolink.io/v1";
const TEN_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"];

// USD per returned image (model pages, checked 2026-10-07).
export const MODELS = {
  "nano-banana-pro": { ratios: TEN_RATIOS, price: { "1k": 0.03, "2k": 0.03, "4k": 0.03 } },
  "nano-banana-2": { ratios: [...TEN_RATIOS, "1:4", "4:1", "1:8", "8:1"], price: { "1k": 0.02, "2k": 0.02, "4k": 0.025 } },
  "nano-banana-2-lite": { ratios: TEN_RATIOS, price: { "1k": 0.01 } },
};

const MIME = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };

export class NanoBananaError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export function check(model, { aspectRatio, resolution, n = 1, references = 0 } = {}) {
  const spec = MODELS[model];
  if (!spec) throw new NanoBananaError(`unknown model ${model}`);
  if (aspectRatio && !spec.ratios.includes(aspectRatio)) throw new NanoBananaError(`${model} does not take aspect_ratio ${aspectRatio}`);
  if (resolution && !(resolution in spec.price)) throw new NanoBananaError(`${model} does not render ${resolution}`);
  if (n < 1 || n > 4) throw new NanoBananaError("n must be 1-4");
  if (references > 14) throw new NanoBananaError("an edit takes at most 14 reference images");
}

export const price = (model, resolution = "1k", images = 1) =>
  Math.round(MODELS[model].price[resolution] * images * 10000) / 10000;

const isUrl = (ref) => /^(https?:|data:)/.test(ref);
const mimeOf = (path) => MIME[extname(path).toLowerCase()] ?? "application/octet-stream";
const dataUrl = async (path) => `data:${mimeOf(path)};base64,${(await readFile(path)).toString("base64")}`;

export class NanoBanana {
  constructor({
    apiKey = process.env.NANO_BANANA_API_KEY,
    baseUrl = process.env.NANO_BANANA_BASE_URL || DEFAULT_BASE_URL,
    timeoutMs = 600_000,
  } = {}) {
    if (!apiKey) throw new NanoBananaError("set NANO_BANANA_API_KEY or pass apiKey");
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.timeoutMs = timeoutMs; // the response arrives only when every image is ready
  }

  async #post(path, body) {
    const json = !(body instanceof FormData);
    const response = await fetch(this.baseUrl + path, {
      method: "POST",
      headers: { Authorization: `Bearer ${this.apiKey}`, ...(json ? { "Content-Type": "application/json" } : {}) },
      body: json ? JSON.stringify(body) : body,
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    const text = await response.text();
    if (!response.ok) throw new NanoBananaError(`POST ${path} returned ${response.status}: ${text.slice(0, 300)}`, response.status, text);
    return JSON.parse(text).data.map((item) => Buffer.from(item.b64_json, "base64"));
  }

  static #fields(model, prompt, { aspectRatio, resolution, n = 1 }) {
    return {
      model,
      prompt,
      n,
      ...(aspectRatio ? { aspect_ratio: aspectRatio } : {}),
      ...(resolution ? { resolution } : {}),
    };
  }

  /** Text to image; resolves to one JPEG Buffer per returned image. */
  async generate(prompt, { model = "nano-banana-2", ...options } = {}) {
    check(model, options);
    return this.#post("/images/generations", NanoBanana.#fields(model, prompt, options));
  }

  /**
   * Image to image with 1-14 references: URLs, data URLs or local paths. URLs go as JSON
   * images[].image_url, local files as repeated multipart image[] fields, and a mix as JSON with
   * the files turned into data URLs. Left out, the frame is 1:1 whatever the references are.
   */
  async edit(prompt, references, { model = "nano-banana-2", ...options } = {}) {
    if (!references?.length) throw new NanoBananaError("an edit needs at least one reference image");
    check(model, { ...options, references: references.length });
    const fields = NanoBanana.#fields(model, prompt, options);
    if (references.some(isUrl)) {
      const images = await Promise.all(references.map(async (ref) => ({ image_url: isUrl(ref) ? ref : await dataUrl(ref) })));
      return this.#post("/images/edits", { ...fields, images });
    }
    const form = new FormData();
    for (const [key, value] of Object.entries(fields)) form.append(key, String(value));
    for (const path of references) {
      form.append("image[]", new Blob([await readFile(path)], { type: mimeOf(path) }), basename(path));
    }
    return this.#post("/images/edits", form);
  }
}

export async function save(images, prefix = "nano-banana") {
  return Promise.all(images.map(async (image, i) => {
    const path = `${prefix}-${i + 1}.jpg`;
    await writeFile(path, image);
    return path;
  }));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [prompt, model = "nano-banana-2", resolution = "1k"] = process.argv.slice(2);
  if (!prompt) {
    console.error('usage: node nanobanana.mjs "prompt" [model] [1k|2k|4k]');
    process.exit(1);
  }
  const images = await new NanoBanana().generate(prompt, { model, resolution });
  console.log((await save(images)).join("\n"));
  console.error(`about $${price(model, resolution, images.length).toFixed(3)}`);
}
