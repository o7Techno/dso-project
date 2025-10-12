# STRIDE анализ

Ниже отмечены ключевые потоки и компоненты системы (F1–F10 из DFD) и 1–2 угрозы на каждый.
Для каждой угрозы указан контроль/митигирование, связь с соответствующим NFR и способ проверки.

| Поток/Элемент | Категория STRIDE | Угроза | Контроль / Митигирование | Связанный NFR | Проверка / Референс | Обоснование |
|---|---|---|---|---|---|---|
| F1 (Client → API Gateway) | Spoofing | Подмена пользователя или сессии | JWT-аутентификация; HTTPS; проверка подписи токена | NFR-02, NFR-06 | Интеграционные тесты auth-flow; проверка HTTPS | Исключаем доступ анонимных и поддельных клиентов |
| F1 (Client → API Gateway) | Tampering | Подмена параметров в запросах | HTTPS + валидация схемы (JSON Schema/OAS) | NFR-03, NFR-08 | OWASP ZAP; schema tests | Защита от инъекций и подмен на границе |
| F2 (API Gateway → EventService) | DoS | Флуд-запросы при создании событий | Rate limiting ≤100 RPS/IP; Circuit Breaker | NFR-03, NFR-05 | k6 нагрузочные тесты; метрики 429 | Снижение риска перегрузки API |
| F2 (API Gateway → EventService) | Elevation of Privilege | Байпас авторизации при редактировании событий | RBAC; JWT claims с ролями “организатор/участник” | NFR-06, NFR-08 | Интеграционные тесты 401/403 | Защита от несанкционированного доступа |
| F3 (EventService → DB) | Information Disclosure | Утечка данных о событиях и пользователях | AES-256 шифрование; маскирование логов | NFR-01, NFR-08 | Code review; проверка логов | Защита конфиденциальных данных |
| F3 (EventService → DB) | Tampering | SQL-инъекции и подмена данных | ORM; параметризованные запросы; валидация входных данных | NFR-08 | Semgrep/SAST в CI | Исключаем модификацию данных |
| F4 (NotificationService → API) | Repudiation | Отрицание факта отправки уведомлений | Аудит-логи уведомлений с trace-id | NFR-08 | Проверка логов и trace-id | Трассируемость действий в системе |
| F4 (NotificationService → API) | DoS | Массовая отправка уведомлений | Очереди сообщений (Kafka/SQS); лимиты на отправку | NFR-03 | Нагрузочные тесты очередей | Предотвращение перегрузок рассылки |
| F5 (UserService → AuthService) | Spoofing | Кража токенов или фальшивый вход | Короткий TTL токенов; refresh flow; HTTPS | NFR-02, NFR-06 | Тесты JWT rotation; проверка revoke | Минимизация окна компрометации |
| F5 (UserService → AuthService) | Repudiation | Отрицание факта логина | Неизменяемые аудит-логи входов | NFR-08 | Проверка логов login/refresh | Подтверждаем действия пользователя |
| F6 (API → Storage) | Information Disclosure | Утечка изображений и вложений событий | Приватные бакеты; короткие TTL pre-signed URLs | NFR-07 | Тесты доступа; ACL проверки | Минимизация рисков утечки файлов |
| F6 (API → Storage) | Tampering | Подмена или вредоносные файлы | Проверка content-type/size; антивирусное сканирование | NFR-07, NFR-08 | Интеграционные тесты upload/download | Гарантия целостности и безопасности загрузок |
| F7 (Client → NotificationService) | DoS | Флуд push/email-запросами | Rate limit + очередь отправки | NFR-05 | k6 bursts; метрики 5xx | Снижение нагрузки на сервис |
| F8 (Monitoring → Logs) | Information Disclosure | Секреты или PII в логах | Маскирование; secret-scanner; ограничение ретенции | NFR-08, NFR-07 | CI secret detection; ручная проверка | Безопасные журналы для дебага |
| F9 (AdminPanel → API) | Elevation of Privilege | Доступ неавторизованного администратора | MFA; RBAC; ограничение IP | NFR-06, NFR-08 | AuthFlow тесты; логи 403 | Исключаем привилегированные атаки |
| F10 (DB Backup → Storage) | Information Disclosure | Утечка резервных копий событий | Шифрование backup; ротация ключей ≤30 дней | NFR-01, NFR-07 | Проверка KMS/backup scripts | Контроль над безопасностью архивов |

---
