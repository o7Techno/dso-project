"""
Тесты валидации входных данных (контроль 1).
Негативные тесты для проверки защиты от инъекций и некорректных данных.
"""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_item_xss_attempt_rejected():
    """Негативный тест: попытка XSS инъекции должна быть отклонена."""
    payload = {"name": "<script>alert('XSS')</script>"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")
    assert "dangerous characters" in str(body.get("errors", {})).lower() or "validation" in body.get("detail", "").lower()


def test_item_sql_injection_attempt_rejected():
    """Негативный тест: попытка SQL инъекции должна быть отклонена."""
    payload = {"name": "test'; DROP TABLE items; --"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_sql_union_attempt_rejected():
    """Негативный тест: попытка SQL UNION инъекции должна быть отклонена."""
    payload = {"name": "test UNION SELECT * FROM users"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_javascript_protocol_rejected():
    """Негативный тест: javascript: протокол должен быть отклонен."""
    payload = {"name": "javascript:alert(1)"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_onclick_handler_rejected():
    """Негативный тест: обработчики событий (onclick) должны быть отклонены."""
    payload = {"name": "test onclick=alert(1)"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_too_long_rejected():
    """Негативный тест: слишком длинное имя должно быть отклонено."""
    payload = {"name": "a" * 101}  # Максимум 100 символов
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_empty_rejected():
    """Негативный тест: пустое имя должно быть отклонено."""
    payload = {"name": ""}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_control_characters_rejected():
    """Негативный тест: управляющие символы должны быть отклонены."""
    payload = {"name": "test\x00\x01\x02"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_extra_fields_rejected():
    """Негативный тест: дополнительные поля должны быть отклонены (extra='forbid')."""
    payload = {"name": "test", "malicious_field": "hack"}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_item_valid_accepted():
    """Позитивный тест: валидное имя должно быть принято."""
    payload = {"name": "Valid Item Name 123"}
    r = client.post("/items", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Valid Item Name 123"
    assert "id" in body


def test_event_past_date_rejected():
    """Негативный тест: событие в прошлом должно быть отклонено (NFR-4)."""
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    payload = {
        "title": "Past Event",
        "event_date": past_date,
        "location": "Somewhere",
    }
    r = client.post("/events", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")
    assert "past" in body.get("detail", "").lower() or "past" in str(body.get("errors", {})).lower()


def test_event_float_price_precision_issue():
    """Негативный тест: использование float вместо Decimal может привести к погрешности."""
    # Валидная дата в будущем
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Event with Float Price",
        "event_date": future_date,
        "location": "Somewhere",
        "price": 19.99,  # Будет преобразовано в Decimal через Pydantic
    }
    r = client.post("/events", json=payload)
    # Должно быть принято, так как Pydantic автоматически конвертирует в Decimal
    assert r.status_code == 200
    body = r.json()
    # Проверяем, что price сохранен как строка (Decimal сериализуется в строку)
    assert body["price"] is not None


def test_event_negative_price_rejected():
    """Негативный тест: отрицательная цена должна быть отклонена."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Event",
        "event_date": future_date,
        "location": "Somewhere",
        "price": -10.50,
    }
    r = client.post("/events", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_event_zero_price_rejected():
    """Негативный тест: нулевая цена должна быть отклонена (gt=0)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Event",
        "event_date": future_date,
        "location": "Somewhere",
        "price": 0,
    }
    r = client.post("/events", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_event_price_too_many_decimal_places_rejected():
    """Негативный тест: слишком много знаков после запятой должно быть отклонено."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    # Парсим как строку, чтобы избежать float погрешности
    payload_json = json.dumps({
        "title": "Event",
        "event_date": future_date,
        "location": "Somewhere",
        "price": "10.999",  # 3 знака после запятой, максимум 2
    })
    r = client.post("/events", data=payload_json, headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_event_duplicate_rejected():
    """Негативный тест: дубликат события должен быть отклонен (NFR-5)."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Duplicate Event",
        "event_date": future_date,
        "location": "Same Location",
    }
    # Создаем первое событие
    r1 = client.post("/events", json=payload)
    assert r1.status_code == 200
    
    # Пытаемся создать дубликат
    r2 = client.post("/events", json=payload)
    assert r2.status_code == 409
    body = r2.json()
    assert body["type"].endswith("#duplicate_event")


def test_event_too_long_title_rejected():
    """Негативный тест: слишком длинный заголовок должен быть отклонен."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "a" * 201,  # Максимум 200 символов
        "event_date": future_date,
        "location": "Somewhere",
    }
    r = client.post("/events", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["type"].endswith("#validation_error")


def test_event_valid_accepted():
    """Позитивный тест: валидное событие должно быть принято."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Valid Event",
        "description": "A valid event description",
        "event_date": future_date,
        "location": "Valid Location",
        "price": "29.99",  # Используем строку для точности
    }
    r = client.post("/events", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Valid Event"
    assert body["price"] == "29.99"


def test_http_client_timeout_handling():
    """Негативный тест: HTTP клиент должен обрабатывать таймауты."""
    import httpx
    from unittest.mock import patch, MagicMock
    
    # Мокаем таймаут
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.request.side_effect = httpx.TimeoutException("Request timed out")
        
        from app.main import safe_http_request
        # Должен сделать несколько попыток с backoff
        try:
            safe_http_request("GET", "http://example.com")
        except httpx.TimeoutException:
            pass
        # Проверяем, что было несколько попыток (HTTP_MAX_RETRIES + 1 = 3)
        assert mock_client.request.call_count == 3


def test_http_client_retry_on_5xx():
    """Негативный тест: HTTP клиент должен ретраить на 5xx ошибки."""
    import httpx
    from unittest.mock import patch, MagicMock
    
    # Мокаем httpx для симуляции 5xx ошибок
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_response
    )
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.request.return_value = mock_response
        
        from app.main import safe_http_request
        # Должен сделать несколько попыток
        try:
            safe_http_request("GET", "http://example.com")
        except httpx.HTTPStatusError:
            pass
        # Проверяем, что было несколько попыток (HTTP_MAX_RETRIES + 1 = 3)
        assert mock_client.request.call_count == 3


def test_http_client_no_retry_on_4xx():
    """Негативный тест: HTTP клиент НЕ должен ретраить на 4xx ошибки."""
    import httpx
    from unittest.mock import patch, MagicMock
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=mock_response
    )
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.request.return_value = mock_response
        
        from app.main import safe_http_request
        try:
            safe_http_request("GET", "http://example.com")
        except httpx.HTTPStatusError:
            pass
        # Должна быть только одна попытка для 4xx
        assert mock_client.request.call_count == 1

