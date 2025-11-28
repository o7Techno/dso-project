# Event Planner

#### Планирование локальных событий без приглашений

---

##  Установка и запуск

### Вариант 1: Docker (рекомендуется)

#### Быстрый старт:
```bash
# Создать .env файл (опционально)
cp .env.example .env

# Собрать и запустить
docker compose up -d

# Или используя Makefile
make build && make up
```

Приложение будет доступно по адресу http://localhost:8000

Подробная документация по Docker: [DOCKER.md](DOCKER.md)

### Вариант 2: Локальная установка

#### 1. Клонирование репозитория
```bash
git clone https://github.com/hse-secdev-2025-fall/course-project-o7Techno/
cd course-project-o7Techno
```

#### 2. Создание виртуального окружения
##### Windows (PowerShell):
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```
##### Linux / macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

#### 3. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt || true
pip install ruff black isort pytest pre-commit
```

#### 4. Запуск приложения
```bash
python run.py
```

## Тесты

### Локально:
```bash
pytest -q
```

### В Docker контейнере:
```bash
make test
# или
docker compose run --rm app python -m pytest -q
```

## Security automation (P09)

- Workflow `Security - SBOM & SCA` в `.github/workflows/ci-sbom-sca.yml` автоматически генерирует SBOM (Syft → CycloneDX JSON + Syft JSON через `-o <format> --file <path>`) и запускает SCA (Grype) при `push`/`pull_request` по Python-зависимостям и вручную через `workflow_dispatch`.
- Все артефакты проверки складываются в `EVIDENCE/P09/`: `sbom.json`, `sbom.syft.json`, `sca_report.json`, `sca_summary.md` и доступны в GitHub Actions как артефакт `P09_EVIDENCE`.
- Для исключений по уязвимостям используйте `policy/waivers.yml` (структура совместима с описанием из `project/69_sbom-vuln-mgmt.md`); записи согласовываются через issue/PR.
