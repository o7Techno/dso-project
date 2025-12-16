# P11 - DAST (OWASP ZAP Baseline)

## Итоги (ожидается после последнего прогона)
- Target: `http://localhost:8000/`
- Alerts: High = 0, Medium = 0, Low = 0 (правило 10049 игнорируется явно)
- Исправление в приложении: middleware с анти-кэш заголовками (`Cache-Control: no-store, no-cache, must-revalidate`, `Pragma: no-cache`, `Expires: 0`).
- Исключение в ZAP baseline: правило `10049` добавлено в `security/zap-baseline.conf` как `IGNORE`, т.к. оно стало информационным после фикса (Non-Storable Content) и нерелевантно для цели скана.

## Артефакты
- Отчёты: `EVIDENCE/P11/zap_baseline.html`, `EVIDENCE/P11/zap_baseline.json`
- Логи: `EVIDENCE/P11/zap_baseline.log`, `EVIDENCE/P11/app.log`

## План действий
- Поддерживать анти-кэш заголовки для всех эндпоинтов.
- При дальнейших изменениях в API — повторять ZAP baseline (workflow `Security - DAST (ZAP Baseline)`) и обновлять отчёты в `EVIDENCE/P11`.
- Если потребуется видеть правило 10049 снова — удалить/закомментировать его в `security/zap-baseline.conf` и перепрогнать.
