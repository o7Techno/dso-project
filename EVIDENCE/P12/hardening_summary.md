# Hardening Summary - P12

## Dockerfile Hardening

### До (baseline)
- Использовался базовый образ без явной версии
- Процесс мог запускаться от root
- Не было явных ограничений на capabilities

### После (текущее состояние)

#### Фиксированные версии образов
- **FROM python:3.11-slim** - используется конкретная версия Python (3.11) вместо `latest`
- Все зависимости устанавливаются с явными версиями где возможно (pip==24.0)

#### Non-root пользователь
- Создан пользователь `appuser` (UID/GID 1000)
- Все файлы копируются с правильными правами (`--chown=appuser:appuser`)
- Процесс запускается от non-root пользователя (`USER appuser`)

#### Минимизация поверхности атаки
- Multi-stage build для уменьшения размера финального образа
- Использование `--no-install-recommends` для минимизации установленных пакетов
- Очистка кэша apt после установки (`rm -rf /var/lib/apt/lists/*`)
- Установка только необходимых пакетов (gcc только для build stage)

#### Безопасные переменные окружения
- `PYTHONUNBUFFERED=1` - для корректного логирования
- `PYTHONDONTWRITEBYTECODE=1` - предотвращение создания .pyc файлов
- `PYTHONHASHSEED=random` - для защиты от hash collision атак

#### Healthcheck
- Настроен healthcheck для мониторинга состояния контейнера
- Интервал: 30s, таймаут: 10s, период запуска: 40s

## Docker Compose Hardening

### До
- Использовался тег `latest` для образа
- Не было явных ограничений на capabilities
- Не было ограничений на сетевой доступ

### После

#### Фиксированные версии образов
- Используется переменная окружения `IMAGE_TAG` с дефолтным значением `v1.0.0`
- Избегается использование `latest` тега

#### Security options
- `no-new-privileges:true` - предотвращение повышения привилегий
- `cap_drop: ALL` - удаление всех capabilities
- `cap_add: NET_BIND_SERVICE` - добавление только необходимой capability для биндинга портов

#### Non-root пользователь
- `user: "1000:1000"` - запуск от non-root пользователя

#### Read-only и tmpfs
- `read_only: false` - установлено в false из-за необходимости записи в uploads
- `tmpfs: /tmp:noexec,nosuid,size=100m` - безопасный tmpfs для временных файлов

#### Сетевая изоляция
- Используется изолированная сеть `app-network` с bridge драйвером
- Порты пробрасываются только на localhost (через переменную окружения)

#### Конфигурация через переменные окружения
- Все настройки вынесены в переменные окружения
- Поддержка `.env` файла для локальной разработки
- Все переменные имеют безопасные дефолтные значения

## Kubernetes IaC Hardening

### Deployment

#### Security Context
- `runAsNonRoot: true` - запрет запуска от root
- `runAsUser: 1000` и `runAsGroup: 1000` - использование non-root пользователя
- `fsGroup: 1000` - правильная настройка прав на volumes
- `seccompProfile: RuntimeDefault` - использование seccomp профиля по умолчанию

#### Container Security Context
- `allowPrivilegeEscalation: false` - запрет повышения привилегий
- `readOnlyRootFilesystem: false` - установлено в false из-за uploads
- `capabilities.drop: ALL` - удаление всех capabilities
- `capabilities.add: NET_BIND_SERVICE` - только необходимая capability

#### Resource Limits
- Установлены requests и limits для CPU и памяти
- Предотвращение resource exhaustion атак

#### Health Checks
- Настроены liveness и readiness probes
- Правильные таймауты и интервалы

#### Service Account
- `automountServiceAccountToken: false` - отключение автоматического монтирования токенов

### Service

#### Тип Service
- `type: ClusterIP` - внутренний сервис, не exposed наружу
- Избегается использование `LoadBalancer` или `NodePort` без необходимости

### Ingress

#### Ограничения доступа
- Используется TLS для шифрования трафика
- Настроены rate limits через аннотации
- SSL redirect включен

#### Ограничения по IP (закомментировано, но готово к использованию)
- Аннотация для whitelist-source-range готова к использованию при необходимости

## Выводы

### Реализованные меры харднинга:
1. Фиксированные версии образов (нет `latest`)
2. Non-root пользователь во всех конфигурациях
3. Минимизация capabilities (drop ALL, add только необходимые)
4. Ограничение сетевого доступа (ClusterIP вместо LoadBalancer)
5. Конфигурация через переменные окружения
6. Resource limits в K8s
7. Security contexts настроены правильно
8. Health checks для мониторинга

### Дальнейшие шаги:
- [ ] Исправить критичные/высокие findings из Trivy (если есть)
- [ ] Рассмотреть использование read-only root filesystem после рефакторинга uploads
- [ ] Настроить Network Policies для дополнительной изоляции
- [ ] Добавить Pod Security Standards (PSA) для K8s
- [ ] Рассмотреть использование distroless образов для дальнейшего уменьшения поверхности атаки
