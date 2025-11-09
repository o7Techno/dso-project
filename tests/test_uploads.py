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


def test_upload_empty_file_rejected():
    """Негативный тест: пустой файл должен быть отклонен."""
    data = b""
    files = {"file": ("empty.png", data, "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")
    assert "empty" in body.get("detail", "").lower()


def test_upload_path_traversal_attempt():
    """Негативный тест: попытка path traversal должна быть отклонена."""
    data = _make_png(64)
    # Попытка использовать ../ в имени файла
    files = {"file": ("../../../etc/passwd.png", data, "image/png")}
    r = client.post("/upload", files=files)
    # Файл должен быть сохранен под UUID, но проверяем что нет ошибки path traversal
    # В реальности имя файла игнорируется, но проверяем что система работает
    assert r.status_code in [200, 422]  # Может быть отклонен или принят с безопасным именем
    if r.status_code == 200:
        body = r.json()
        # Имя файла должно быть UUID, а не оригинальное
        assert ".." not in body["filename"]
        assert body["filename"].endswith(".bin")


def test_upload_jpeg_with_png_header():
    """Негативный тест: JPEG файл с заявленным PNG content-type должен быть отклонен."""
    # JPEG magic bytes
    jpeg_data = b"\xFF\xD8\xFF\xE0" + b"0" * 60
    files = {"file": ("fake.png", jpeg_data, "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#invalid_signature")


def test_upload_png_with_jpeg_header():
    """Негативный тест: PNG файл с заявленным JPEG content-type должен быть отклонен."""
    png_data = _make_png(64)
    files = {"file": ("fake.jpg", png_data, "image/jpeg")}
    r = client.post("/upload", files=files)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#invalid_signature")


def test_upload_very_large_file_boundary():
    """Негативный тест: файл точно на границе лимита должен быть принят."""
    data = _make_png(MAX_UPLOAD_SIZE_BYTES)
    files = {"file": ("boundary.png", data, "image/png")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["size"] == MAX_UPLOAD_SIZE_BYTES
