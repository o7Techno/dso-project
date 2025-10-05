# Event Planner

Планирование локальных событий без приглашений

---

##  Быстрая установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/hse-secdev-2025-fall/course-project-o7Techno/
cd course-project-o7Techno
```

### 2. Создание виртуального окружения
#### Windows (PowerShell):
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```
#### Linux / macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt || true
pip install ruff black isort pytest pre-commit
```

### 4. Запуск приложения
```bash
python main.py
```

## Тесты
```bash
pytest -q
```
