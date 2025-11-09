from fastapi.testclient import TestClient

from app.main import MAX_UPLOAD_SIZE_BYTES, app

client = TestClient(app)


def _make_png(bytes_len: int = 16):
    header = b"\x89PNG\r\n\x1a\n"
    return header + b"0" * (bytes_len - len(header))


def test_upload_png_ok():
    data = _make_png(64)
    files = {"file": ("test.png", data, "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["size"] == len(data)
    assert body["content_type"] == "image/png"
    assert body["filename"].endswith(".bin")


def test_upload_wrong_mime_signature_rejected():
    data = b"BADHEADER" + b"0" * 32
    files = {"file": ("bad.png", data, "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#invalid_signature")
    assert body["title"] == "Request validation error"


def test_upload_unsupported_media_type():
    data = b"SOMETHING" * 4
    files = {"file": ("a.txt", data, "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 415
    body = r.json()
    assert body["type"].endswith("#unsupported_media_type")
    assert body["status"] == 415


def test_upload_too_large():
    too_big = MAX_UPLOAD_SIZE_BYTES + 1
    data = _make_png(too_big)
    files = {"file": ("big.png", data, "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 413
    body = r.json()
    assert body["type"].endswith("#payload_too_large")
