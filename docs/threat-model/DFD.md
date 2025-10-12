## Data Flow Diagram — Event Planner

```mermaid
flowchart LR
  %% === Trust Boundaries ===
  subgraph B0["Client boundary"]
    U["Пользователь (Web/Mobile)"]
    C["Клиентское приложение (UI)"]
  end

  subgraph B1["Edge boundary"]
    G["API Gateway / Rate Limiter"]
    CDN["CDN / Static Content"]
  end

  subgraph B2["Core boundary"]
    AUTH["Auth Service (JWT/Refresh Tokens)"]
    API["Backend API (Events/Users/Notifications)"]
    WORKER["Async Worker (Email/SMS jobs)"]
    OBS["Observability (Logs / Metrics / Traces)"]
  end

  subgraph B3["Data boundary"]
    DB["Main Database (PostgreSQL)"]
    MQ["Message Queue (RabbitMQ)"]
    OBJ["Object Storage (Images/Attachments)"]
    KMS["Secrets / Config / Credentials"]
  end

  %% === External parties ===
  EXT_MAIL["Email/SMS Provider"]
  EXT_IDP["External IdP (OAuth/OIDC)"]

  %% === Flows (нумерация обязательна) ===
  U -->|"F1: UX-действия / формы / навигация"| C
  C -->|"F2: HTTPS REST/JSON API calls"| G
  G -->|"F3: mTLS REST/gRPC → Core Services"| API
  G -->|"F4: mTLS REST/gRPC → Auth Service"| AUTH
  AUTH -->|"F5: JWT (TTL 60 мин) + Refresh 30 дней"| C
  API -->|"F6: mTLS + SQL/ORM → основная БД"| DB
  API -->|"F7: enqueue task → очередь сообщений"| MQ
  MQ -->|"F8: dequeue job → отправка уведомлений"| WORKER
  WORKER -->|"F9: SMTP/SMS API over TLS"| EXT_MAIL
  API -->|"F10: OTLP/Logs/Metrics → Observability"| OBS
  API -->|"F11: S3 API / HTTPS → Object Storage"| OBJ
  AUTH -->|"F12: OAuth/OIDC → External IdP"| EXT_IDP

  %% === Async flows ===
  API -->|"enqueue async tasks"| MQ
  MQ -->|"consume jobs"| WORKER
  WORKER -->|"update job status"| DB
