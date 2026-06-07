## Запуск проекта

### 1. Клонирование репозитория

```bash
git clone https://github.com/A-R-M-O-R/Secret-manage-service.git
cd secret-manage-service
```
---

### 2. Подготовка `.env`

Создай `.env` из шаблона:

```bash
cp .env.example .env
```

В `.env` обязательно должны быть заданы:

```env
POSTGRES_PASSWORD=<your_generated_password>
JWT_SECRET_KEY=<your_generated_secret>
API_KEY_PEPPER=<your_generated_secret>
```

---

### 3. Генерация master key

Master key используется для шифрования секретов и передается в контейнер как Docker secret.

```bash
python scripts/generate_master_key.py
```

Проверь, что файл создан:

```bash
ls -la secrets/sms_master_key
```
---

### 4. Генерация TLS-сертификата для Nginx

Linux/macOS:

```bash
bash scripts/generate-nginx-local-cert.sh
```

Windows PowerShell:

```powershell
.\scripts\generate-nginx-local-cert.ps1
```

После генерации должны появиться:

```text
nginx/certs/nginx.crt
nginx/certs/nginx.key
```

---

### 5. Сборка и запуск базы данных

```bash
docker compose build
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current
```

---

### 6. Запуск всего приложения

```bash
docker compose up -d --build
docker compose ps
```

Ожидаемые сервисы:

```text
postgres
api
nginx
```

---

### 7. Проверка health endpoints

```bash
curl -k https://127.0.0.1:8443/health
curl -k https://127.0.0.1:8443/api/v1/health
curl -k https://127.0.0.1:8443/api/v1/health/db
```

Флаг `-k` нужен из-за self-signed сертификата.

---

### 8. Создание admin-пользователя

```bash
docker compose run --rm -e PYTHONPATH=/app api python -m scripts.create_admin --username admin
```

Скрипт попросит пароль и подтверждение пароля.

---

### 9. Проверка логина

```bash
curl -k -X POST https://127.0.0.1:8443/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'
```

В ответе должен прийти JWT-токен.
