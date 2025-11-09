"""
Простой скрипт для тестирования API вручную.
Запустите приложение (uvicorn app.main:app) и затем этот скрипт.
"""
import json
from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = "http://127.0.0.1:8000"

client = httpx.Client(timeout=10.0)


def test_health():
    """Проверка health endpoint"""
    print("\n=== Тест 1: Health Check ===")
    r = client.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_create_item_valid():
    """Создание валидного item"""
    print("\n=== Тест 2: Создание валидного item ===")
    payload = {"name": "Test Item 123"}
    r = client.post(f"{BASE_URL}/items", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_create_item_xss_attack():
    """Попытка XSS атаки (должна быть отклонена)"""
    print("\n=== Тест 3: Попытка XSS атаки (должна быть отклонена) ===")
    payload = {"name": "<script>alert('XSS')</script>"}
    r = client.post(f"{BASE_URL}/items", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_create_item_sql_injection():
    """Попытка SQL инъекции (должна быть отклонена)"""
    print("\n=== Тест 4: Попытка SQL инъекции (должна быть отклонена) ===")
    payload = {"name": "test'; DROP TABLE items; --"}
    r = client.post(f"{BASE_URL}/items", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_create_event_valid():
    """Создание валидного события"""
    print("\n=== Тест 5: Создание валидного события ===")
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Test Event",
        "description": "A test event",
        "event_date": future_date,
        "location": "Test Location",
        "price": "29.99",
    }
    r = client.post(f"{BASE_URL}/events", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_create_event_past_date():
    """Попытка создать событие в прошлом (должна быть отклонена)"""
    print("\n=== Тест 6: Попытка создать событие в прошлом (должна быть отклонена) ===")
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    payload = {
        "title": "Past Event",
        "event_date": past_date,
        "location": "Somewhere",
    }
    r = client.post(f"{BASE_URL}/events", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_create_event_negative_price():
    """Попытка создать событие с отрицательной ценой (должна быть отклонена)"""
    print("\n=== Тест 7: Попытка создать событие с отрицательной ценой (должна быть отклонена) ===")
    future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "title": "Event",
        "event_date": future_date,
        "location": "Somewhere",
        "price": -10.50,
    }
    r = client.post(f"{BASE_URL}/events", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


def test_external_health():
    """Проверка внешнего health endpoint (использует безопасный HTTP клиент)"""
    print("\n=== Тест 8: Проверка внешнего health endpoint ===")
    r = client.get(f"{BASE_URL}/external/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")


if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование API безопасности")
    print("=" * 60)
    
    try:
        test_health()
        test_create_item_valid()
        test_create_item_xss_attack()
        test_create_item_sql_injection()
        test_create_event_valid()
        test_create_event_past_date()
        test_create_event_negative_price()
        test_external_health()
        
        print("\n" + "=" * 60)
        print("Все тесты выполнены!")
        print("=" * 60)
    except Exception as e:
        print(f"\nОшибка: {e}")
        print("Убедитесь, что приложение запущено на http://127.0.0.1:8000")
    finally:
        client.close()

