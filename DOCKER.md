# Docker Setup and Usage

Этот документ описывает использование Docker для контейнеризации приложения Event Planner.

## Требования

- Docker Engine 20.10+
- Docker Compose 2.0+

## Быстрый старт

### 1. Создание .env файла

Скопируйте `.env.example` в `.env` и при необходимости настройте переменные окружения:

```bash
cp .env.example .env
```

### 2. Сборка и запуск

Используя Makefile:
```bash
make build
make up
```

Или используя docker compose напрямую:
```bash
docker compose build
docker compose up -d
```

Или используя скрипт:
```bash
./scripts/run.sh
```

### 3. Проверка работы

Приложение будет доступно по адресу:
- API: http://localhost:8000
- Документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Структура Docker файлов

- `Dockerfile` - Multi-stage build с оптимизацией размера и безопасности
- `compose.yaml` - Конфигурация Docker Compose с security hardening
- `.dockerignore` - Исключения для контекста сборки
- `docker/seccomp-profile.json` - Seccomp профиль для ограничения системных вызовов

## Безопасность

Контейнер настроен с максимальным уровнем безопасности:

- Запуск под non-root пользователем (UID 1000)
- Ограничение capabilities (DROP ALL, ADD NET_BIND_SERVICE)
- Seccomp профиль для ограничения системных вызовов
- No new privileges
- Read-only файловая система (кроме /app/uploads)
- tmpfs для /tmp с noexec, nosuid
- HEALTHCHECK для мониторинга состояния

## Проверки и тестирование

### Локальные проверки

```bash
# Проверка non-root пользователя
make check-user

# Проверка healthcheck
make check-health

# Полный набор тестов контейнера
./scripts/test_container.sh

# Линтинг Dockerfile
make lint

# Сканирование безопасности (Trivy)
make scan
```

### CI/CD

GitHub Actions workflow (`.github/workflows/docker-security.yml`) автоматически выполняет:

1. **Hadolint** - линтинг Dockerfile
2. **Trivy** - сканирование уязвимостей образа
3. **Container tests** - проверка non-root пользователя, healthcheck, API endpoints

Отчёты сохраняются как артефакты и загружаются в GitHub Security.

## Makefile команды

```bash
make help          # Показать все доступные команды
make build         # Собрать Docker образ
make up            # Запустить сервисы
make down          # Остановить сервисы
make logs          # Показать логи
make test          # Запустить тесты в контейнере
make lint          # Линтинг Dockerfile (Hadolint)
make scan          # Сканирование безопасности (Trivy)
make check-user    # Проверка non-root пользователя
make check-health  # Проверка healthcheck
make clean         # Очистка контейнеров и образов
```

## Оптимизация образа

Dockerfile использует multi-stage build:

1. **Build stage**: Установка зависимостей и запуск тестов
2. **Runtime stage**: Минимальный образ только с runtime зависимостями

Размер финального образа оптимизирован:
- Использование `python:3.11-slim` базового образа
- Удаление build зависимостей из runtime stage
- Минимальное количество слоёв
- Кэширование зависимостей

## Переменные окружения

Основные переменные (см. `.env.example`):

- `APP_PORT` - Порт приложения (по умолчанию: 8000)
- `HTTP_TIMEOUT_*` - Таймауты HTTP клиента
- `EXTERNAL_HEALTH_URL` - URL для проверки внешнего сервиса

## Troubleshooting

### Контейнер не запускается

```bash
# Проверить логи
docker compose logs app

# Проверить статус
docker compose ps
```

### Проблемы с правами доступа

Убедитесь, что директория `app/uploads` имеет правильные права:
```bash
chmod 755 app/uploads
```

### Healthcheck не проходит

Проверьте, что приложение запущено:
```bash
docker compose exec app curl http://localhost:8000/health
```

## Дополнительная информация

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Hadolint Documentation](https://github.com/hadolint/hadolint)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
