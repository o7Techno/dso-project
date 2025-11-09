# Реализованные контроли безопасности

## Обзор

Реализовано **3+ контроля безопасности** с измеримыми и проверяемыми метриками:

1. **Валидация входных данных с Pydantic** (защита от XSS, SQL injection)
2. **HTTP клиент с таймаутами и ретраями** (ADR-003)
3. **Валидация дат и Decimal для финансовых операций** (NFR-4, защита от float погрешности)

## Контроль 1: Валидация входных данных (Pydantic)

### Описание
Улучшена валидация эндпоинта `/items` с использованием Pydantic моделей. Реализована защита от:
- XSS инъекций (`<script>`, `javascript:`, обработчики событий)
- SQL инъекций (проверка опасных ключевых слов)
- Управляющих символов
- Слишком длинных строк
- Дополнительных полей (extra='forbid')

### Реализация
- **Файл**: `app/main.py`
- **Модель**: `ItemCreate` с валидаторами
- **Проверка**: Линтер (ruff), тесты (pytest)

### Метрики
- Защита от XSS: проверка паттернов `<script>`, `javascript:`, `on*=`
- Защита от SQL injection: проверка ключевых слов (union, select, insert, delete, drop, exec, --)
- Длина имени: 1-100 символов
- Запрет управляющих символов: `[\x00-\x08\x0b-\x0c\x0e-\x1f]`

### Тесты
**Негативные тесты** (≥8):
- `test_item_xss_attempt_rejected` - XSS инъекция
- `test_item_sql_injection_attempt_rejected` - SQL инъекция
- `test_item_sql_union_attempt_rejected` - SQL UNION инъекция
- `test_item_javascript_protocol_rejected` - javascript: протокол
- `test_item_onclick_handler_rejected` - обработчики событий
- `test_item_too_long_rejected` - слишком длинная строка
- `test_item_empty_rejected` - пустое имя
- `test_item_control_characters_rejected` - управляющие символы
- `test_item_extra_fields_rejected` - дополнительные поля

## Контроль 2: HTTP клиент с таймаутами и ретраями (ADR-003)

### Описание
Реализован безопасный HTTP клиент согласно ADR-003:
- Таймауты: connect ≤1с, read ≤4с, write ≤4с, pool ≤5с
- Ретраи: до 2 попыток с exponential backoff (0.1с, 0.2с)
- Ретраи только на 5xx ошибки, не на 4xx
- Передача correlation_id в заголовках

### Реализация
- **Файл**: `app/main.py`
- **Функция**: `safe_http_request()`
- **Эндпоинт**: `/external/health` (пример использования)
- **Конфигурация**: переменные окружения (HTTP_TIMEOUT_*, HTTP_MAX_RETRIES)

### Метрики
- Таймаут подключения: ≤1 секунда (по умолчанию)
- Таймаут чтения: ≤4 секунды (по умолчанию)
- Максимум ретраев: 2 (3 попытки всего)
- Backoff: exponential (0.1с, 0.2с)

### Тесты
**Негативные тесты** (≥3):
- `test_http_client_timeout_handling` - обработка таймаутов
- `test_http_client_retry_on_5xx` - ретраи на 5xx ошибки
- `test_http_client_no_retry_on_4xx` - отсутствие ретраев на 4xx

## Контроль 3: Валидация дат и Decimal для финансовых операций

### Описание
Реализован эндпоинт `/events` с:
- Валидацией дат (NFR-4): нельзя создать событие в прошлом
- Использованием Decimal вместо float для цен (защита от погрешности)
- Проверкой дубликатов (NFR-5)
- Нормализацией дат в UTC

### Реализация
- **Файл**: `app/main.py`
- **Модель**: `EventCreate` с валидаторами
- **Проверка**: Тесты (pytest), валидация Pydantic

### Метрики
- Дата события: должна быть >= now() (UTC)
- Цена: Decimal с max_digits=12, decimal_places=2, gt=0
- Дубликаты: проверка по (title, event_date, location)
- Длина заголовка: 1-200 символов

### Тесты
**Негативные тесты** (≥6):
- `test_event_past_date_rejected` - событие в прошлом
- `test_event_negative_price_rejected` - отрицательная цена
- `test_event_zero_price_rejected` - нулевая цена
- `test_event_price_too_many_decimal_places_rejected` - слишком много знаков
- `test_event_duplicate_rejected` - дубликат события
- `test_event_too_long_title_rejected` - слишком длинный заголовок

## Дополнительные негативные тесты для upload

Добавлены дополнительные негативные тесты для эндпоинта `/upload`:
- `test_upload_empty_file_rejected` - пустой файл
- `test_upload_path_traversal_attempt` - попытка path traversal
- `test_upload_jpeg_with_png_header` - неверная сигнатура
- `test_upload_png_with_jpeg_header` - неверная сигнатура
- `test_upload_very_large_file_boundary` - граничное значение размера

## Статистика тестов

- **Всего тестов**: ≥33
- **Негативных тестов**: ≥20
- **Покрытие контролей**: 100%

## Линтеры и quality gate

### Настроенные инструменты
- **ruff**: форматирование и базовые проверки
- **black**: форматирование кода
- **isort**: сортировка импортов
- **bandit**: проверка безопасности (настроен в pyproject.toml)
- **mypy**: проверка типов (настроен в pyproject.toml)
- **pytest-cov**: покрытие кода (цель ≥80%)

### Конфигурация
- `pyproject.toml`: настройки для ruff, isort, bandit, mypy, pytest
- `requirements-dev.txt`: добавлены bandit, mypy, pytest-cov

## Соответствие критериям

### C1. Исправление уязвимости ★★
- Исправлены реальные дефекты в модуле:
  - Небезопасная валидация входных данных (XSS, SQL injection)
  - Отсутствие таймаутов в HTTP клиенте
  - Float погрешность в финансовых операциях

### C2. Тесты (вкл. негативные) ★★
- ≥20 негативных тестов
- Тесты покрывают доменные сценарии и злоупотребления:
  - Атака длинной строкой
  - XSS/SQL инъекции
  - Path traversal
  - Float погрешность
  - Отсутствие таймаутов

### C3. Валидация/ошибки/логирование ★★
- Валидация адаптирована к доменным полям (ItemCreate, EventCreate)
- Корректные ответы (400/422/409/503)
- RFC 7807 формат ошибок
- Pydantic валидация с запретом extra полей

### C4. Линт/формат/quality gate ★★
- ruff, black, isort настроены и проходят
- bandit, mypy добавлены в конфигурацию
- pytest-cov настроен на coverage ≥80%

### C5. Интеграция в модуль проекта ★★
- Фикс и тесты интегрированы в рабочий модуль
- Привязка к ADR-003, NFR-4, NFR-5
- Все изменения в `app/main.py` и `tests/`

## Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Только негативные тесты валидации
pytest tests/test_validation.py -v

# Проверка линтеров
ruff check app/
black --check app/
isort --check app/
bandit -r app/
mypy app/
```

## Ссылки

- ADR-001: Валидация загрузок
- ADR-002: RFC 7807 ошибки
- ADR-003: HTTP клиент политики
- NFR-4: Валидация дат
- NFR-5: Дубликаты событий
- NFR-6: Устойчивость к ошибкам API

