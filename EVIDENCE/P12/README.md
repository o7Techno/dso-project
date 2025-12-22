# P12 - IaC & Container Security Evidence

Этот каталог содержит артефакты проверки безопасности инфраструктуры и контейнеров.

## Структура

- `hadolint_report.json` - отчёт Hadolint по Dockerfile
- `checkov_report.json` - отчёт Checkov по K8s манифестам в `iac/`
- `checkov_compose_report.json` - отчёт Checkov по docker-compose.yaml
- `trivy_report.json` - отчёт Trivy по собранному Docker образу
- `trivy_fs_report.json` - отчёт Trivy по файловой системе проекта
- `scan_summary.md` - автоматически генерируемая сводка сканирований
- `hardening_summary.md` - описание мер харднинга

## Генерация отчётов

Отчёты генерируются автоматически при запуске workflow `.github/workflows/ci-p12-iac-container.yml`.

Workflow запускается:
- Вручную через `workflow_dispatch`
- При push в ветки с изменениями в:
  - `Dockerfile`
  - `iac/**`
  - `k8s/**`
  - `deploy/**`
  - `compose.yaml`
  - `docker-compose.yml`
  - `security/**`
- При создании Pull Request с изменениями в указанных путях

## Инструменты

### Hadolint
- Проверяет Dockerfile на соответствие best practices
- Конфигурация: `security/hadolint.yaml`

### Checkov
- Проверяет IaC манифесты (Kubernetes, Docker Compose) на уязвимости
- Конфигурация: `security/checkov.yaml`
- Сканирует: `iac/` и `compose.yaml`

### Trivy
- Сканирует Docker образ на уязвимости в зависимостях
- Конфигурация: `security/trivy.yaml`
- Проверяет собранный образ и файловую систему

## Артефакты

После успешного выполнения workflow все отчёты доступны:
1. В артефакте `P12_EVIDENCE` в GitHub Actions
2. В этом каталоге (если закоммичены в репозиторий)
