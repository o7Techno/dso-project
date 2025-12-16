# P11 - DAST (OWASP ZAP Baseline)

## Итоги после фикса
- Target: `http://localhost:8000/`
- Alerts: High = 0, Medium = 0, Low = 0
- Исправление: добавлен middleware с анти-кэш заголовками (`Cache-Control: no-store, no-cache, must-revalidate`, `Pragma: no-cache`, `Expires: 0`), исключающий кэшируемость ответов и снимающий алерт 10049.

## Артефакты
- Отчёты: `EVIDENCE/P11/zap_baseline.html`, `EVIDENCE/P11/zap_baseline.json`
- Логи: `EVIDENCE/P11/zap_baseline.log`, `EVIDENCE/P11/app.log`

## План действий
- Поддерживать анти-кэш заголовки для всех эндпоинтов.
- При дальнейших изменениях в API — повторять ZAP baseline (workflow `Security - DAST (ZAP Baseline)`) и обновлять отчёты в `EVIDENCE/P11`.
