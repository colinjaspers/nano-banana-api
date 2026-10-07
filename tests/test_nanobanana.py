"""Offline tests: urlopen is replaced, so no key, network or credit is needed."""
import base64
import io
import json
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import nanobanana  # noqa: E402

JPEG = b"\xff\xd8\xff\xe0fake-jpeg"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def urlopen(request, timeout=None):
        seen.append(request)
        count = 1
        if request.get_header("Content-type") == "application/json":
            count = json.loads(request.data).get("n", 1)
        item = {"b64_json": base64.b64encode(JPEG).decode()}
        return FakeResponse(json.dumps({"created": 0, "data": [item] * count}).encode())

    monkeypatch.setattr(nanobanana.urllib.request, "urlopen", urlopen)
    return seen


def test_generate_posts_json_and_decodes_every_image(calls):
    images = nanobanana.NanoBanana(api_key="k").generate(
        "a teapot", model="nano-banana-pro", aspect_ratio="16:9", resolution="4k", n=2)
    request = calls[0]
    assert request.full_url == "https://argolink.io/v1/images/generations"
    assert request.get_header("Authorization") == "Bearer k"
    assert json.loads(request.data) == {
        "model": "nano-banana-pro", "prompt": "a teapot", "n": 2, "aspect_ratio": "16:9", "resolution": "4k"}
    assert images == [JPEG, JPEG]


def test_edit_with_urls_sends_image_url_objects(calls):
    nanobanana.NanoBanana(api_key="k").edit("keep the bottle", ["https://example.com/a.png", "https://example.com/b.png"])
    body = json.loads(calls[0].data)
    assert calls[0].full_url.endswith("/images/edits")
    assert body["images"] == [{"image_url": "https://example.com/a.png"}, {"image_url": "https://example.com/b.png"}]


def test_edit_with_local_files_sends_repeated_multipart_fields(calls, tmp_path):
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    first.write_bytes(b"PNG-A")
    second.write_bytes(b"PNG-B")
    nanobanana.NanoBanana(api_key="k").edit("merge", [str(first), str(second)], aspect_ratio="4:3")
    request = calls[0]
    assert request.get_header("Content-type").startswith("multipart/form-data; boundary=")
    assert request.data.count(b'name="image[]"') == 2
    assert b"PNG-A" in request.data and b"PNG-B" in request.data
    assert b'name="aspect_ratio"\r\n\r\n4:3' in request.data


def test_mixed_references_become_data_urls(calls, tmp_path):
    local = tmp_path / "c.png"
    local.write_bytes(b"PNG-C")
    nanobanana.NanoBanana(api_key="k").edit("merge", ["https://example.com/a.png", str(local)])
    images = json.loads(calls[0].data)["images"]
    assert images[1]["image_url"] == "data:image/png;base64," + base64.b64encode(b"PNG-C").decode()


@pytest.mark.parametrize("kwargs", [
    {"model": "nano-banana-2-lite", "resolution": "2k"},
    {"model": "nano-banana-pro", "aspect_ratio": "1:8"},
    {"model": "nano-banana-2", "n": 5},
    {"model": "nano-banana-3"},
])
def test_requests_the_api_would_refuse_fail_locally(calls, kwargs):
    with pytest.raises(nanobanana.NanoBananaError):
        nanobanana.NanoBanana(api_key="k").generate("x", **kwargs)
    assert calls == []


def test_more_than_fourteen_references_fail_locally(calls):
    with pytest.raises(nanobanana.NanoBananaError):
        nanobanana.NanoBanana(api_key="k").edit("x", [f"https://example.com/{i}.png" for i in range(15)])


def test_price_follows_the_tiers():
    assert nanobanana.price("nano-banana-pro", "4k") == 0.03
    assert nanobanana.price("nano-banana-2", "4k", 4) == 0.1
    assert nanobanana.price("nano-banana-2-lite") == 0.01


def test_http_errors_keep_status_and_body(monkeypatch):
    def urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b'{"error":{"message":"url is not supported"}}'))

    monkeypatch.setattr(nanobanana.urllib.request, "urlopen", urlopen)
    with pytest.raises(nanobanana.NanoBananaError) as raised:
        nanobanana.NanoBanana(api_key="k").generate("x")
    assert raised.value.status == 400
    assert raised.value.body["error"]["message"] == "url is not supported"


def test_dry_run_prints_cost_without_a_key(capsys, monkeypatch):
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    assert nanobanana.main(["poster", "--model", "nano-banana-2", "--resolution", "4k", "-n", "3", "--dry-run"]) == 0
    assert "$0.075" in capsys.readouterr().out
