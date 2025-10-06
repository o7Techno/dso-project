# Связь NFR со Stories/Tasks

| Story/Task ID | Краткое описание задачи                        | Связанные NFR                  | Приоритет | Релиз |
|---------------|-------------------------------------------------|-------------------------------:|----------:|:-----:|
| AUTH-01       | Регистрация и вход пользователя                 | NFR-01, NFR-02                 | High      | R1    |
| AUTH-02       | Смена/восстановление пароля                     | NFR-01                         | Medium    | R1    |
| AUTH-03       | Session/token handling & auth middleware        | NFR-02, NFR-03                 | High      | R1    |
| EVENT-01      | CRUD для событий (create/read/update/delete)    | NFR-03, NFR-04, NFR-07         | High      | R1    |
| EVENT-02      | Список событий, фильтры (from/to)               | NFR-03, NFR-07                 | Medium    | R1    |
| EVENT-03      | Защита от дубликатов + DB unique constraint     | NFR-05, NFR-03                 | Medium    | R1    |
| EVENT-04      | Входные проверки/валидация полей (date, place) | NFR-04                         | High      | R1    |
| CAL-01        | Интеграция с внешним календарём (adapter)       | NFR-06                         | Medium    | R2    |
| INFRA-01      | Настройка логирования и аудита                   | NFR-07                         | Medium    | R1    |
| SEC-01        | CI: pip-audit/safety integration                | NFR-08                         | Medium    | R1    |
| SEC-02        | Secrets handling & policy (env, vault)          | NFR-01, NFR-08                 | High      | R1    |
| OPS-01        | Monitoring/alerts (ошибки, p95 latencies)       | NFR-06, NFR-07                 | Medium    | R2    |
