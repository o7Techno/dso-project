# Инструкция по запуску и тестированию

## Быстрый запуск

### 1. Установка зависимостей (если еще не установлены)

```bash
pip install -r requirements.txt
```

### 2. Запуск приложения

**Вариант A: Через uvicorn (рекомендуется)**
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Вариант B: Через Python скрипт**
Создайте файл `run.py` в корне проекта:
```python
import uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
```

Затем запустите:
```bash
python run.py
```

### 3. Проверка работы

Откройте в браузере:
- **API документация (Swagger)**: http://127.0.0.1:8000/docs
- **Альтернативная документация (ReDoc)**: http://127.0.0.1:8000/redoc
- **Health check**: http://127.0.0.1:8000/health

## Тестирование

### Автоматические тесты

```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# Только тесты валидации
pytest tests/test_validation.py -v

# С покрытием кода
pytest --cov=app --cov-report=html
```

### Ручное тестирование через скрипт

1. Запустите приложение (см. выше)
2. В другом терминале запустите:
```bash
python test_api.py
```

Этот скрипт проверит:
- Health check
- Создание валидного item
- Защиту от XSS атак
- Защиту от SQL инъекций
- Создание валидного события
- Защиту от создания событий в прошлом
- Защиту от отрицательных цен
- HTTP клиент с таймаутами

### Тестирование через браузер (Swagger UI)

1. Откройте http://127.0.0.1:8000/docs
2. Попробуйте эндпоинты:
   - `POST /items` - создание item (попробуйте с XSS: `<script>alert(1)</script>`)
   - `POST /events` - создание события (попробуйте с прошлой датой)
   - `GET /external/health` - проверка HTTP клиента

### Тестирование через curl/Postman

**Создание валидного item:**
```bash
curl -X POST "http://127.0.0.1:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item"}'
```

**Попытка XSS атаки (должна быть отклонена):**
```bash
curl -X POST "http://127.0.0.1:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert(1)</script>"}'
```

**Создание валидного события:**
```bash
curl -X POST "http://127.0.0.1:8000/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "event_date": "2025-12-31T12:00:00Z",
    "location": "Test Location",
    "price": "29.99"
  }'
```

**Попытка создать событие в прошлом (должна быть отклонена):**
```bash
curl -X POST "http://127.0.0.1:8000/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Past Event",
    "event_date": "2020-01-01T12:00:00Z",
    "location": "Somewhere"
  }'
```

## Проверка линтеров

```bash
# Ruff
ruff check app/

# Black (проверка форматирования)
black --check app/

# isort (проверка сортировки импортов)
isort --check app/

# Bandit (проверка безопасности)
bandit -r app/

# MyPy (проверка типов)
mypy app/
```

## Структура эндпоинтов

- `GET /health` - проверка здоровья приложения
- `POST /items` - создание item (с валидацией от XSS/SQL injection)
- `GET /items/{item_id}` - получение item по ID
- `POST /events` - создание события (с валидацией дат и Decimal)
- `GET /events/{event_id}` - получение события по ID
- `POST /upload` - загрузка файлов (с проверкой magic bytes)
- `GET /external/health` - проверка внешнего сервиса (использует безопасный HTTP клиент)

## Примеры ответов

### Успешное создание item:
```json
{
  "id": 1,
  "name": "Test Item"
}
```

### Ошибка валидации (XSS):
```json
{
  "type": "about:blank#validation_error",
  "title": "Request validation error",
  "status": 422,
  "detail": "Input validation failed",
  "errors": {
    "name": "name contains dangerous characters"
  },
  "correlation_id": "uuid-here"
}
```

### Ошибка валидации (событие в прошлом):
```json
{
  "type": "about:blank#validation_error",
  "title": "Request validation error",
  "status": 422,
  "detail": "Input validation failed",
  "errors": {
    "event_date": "event_date cannot be in the past"
  },
  "correlation_id": "uuid-here"
}
```

