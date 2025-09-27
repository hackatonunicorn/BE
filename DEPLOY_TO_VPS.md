# Развертывание Startup VC Platform на VPS сервере

## Предварительные требования

У вас есть:
- ✅ VPS сервер с Ubuntu
- ✅ IP адрес сервера
- ✅ SSH доступ к серверу

## Шаг 1: Подключение к серверу

```bash
# Подключитесь к серверу по SSH
ssh root@YOUR_VPS_IP
# или если у вас другой пользователь
ssh username@YOUR_VPS_IP
```

## Шаг 2: Подготовка сервера

### Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### Установка необходимых пакетов
```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev nginx postgresql postgresql-contrib redis-server supervisor git curl wget htop
```

### Проверка версии Python
```bash
python3.11 --version
# Должно показать Python 3.11.x
```

## Шаг 3: Настройка базы данных PostgreSQL

### Инициализация PostgreSQL
```bash
sudo -u postgres createuser --interactive
# Введите имя: startup_vc_user
# Создать суперпользователя? y

sudo -u postgres createdb startup_vc_db
```

### Настройка пароля
```bash
sudo -u postgres psql

```

В PostgreSQL консоли выполните:
```sql
ALTER USER startup_vc_user PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE startup_vc_db TO startup_vc_user;
\q
```

### Настройка PostgreSQL для подключений
```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Найдите и измените:
```
listen_addresses = '*'
```

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Добавьте в конец файла:
```
host    startup_vc_db    startup_vc_user    0.0.0.0/0    md5
```

Перезапустите PostgreSQL:
```bash
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

## Шаг 4: Настройка Redis

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка работы Redis
redis-cli ping
# Должно вернуть PONG
```

## Шаг 5: Создание пользователя для приложения

```bash
sudo adduser --system --group --home /opt/startup-vc startup-vc
```

## Шаг 6: Загрузка кода приложения

### Вариант 1: Загрузка через SCP (с вашего локального компьютера)

На вашем локальном компьютере выполните:
```bash
# Создайте архив проекта
tar -czf startup-vc-platform.tar.gz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' .

# Загрузите на сервер
scp startup-vc-platform.tar.gz root@YOUR_VPS_IP:/opt/startup-vc/
```

На сервере:
```bash
cd /opt/startup-vc
sudo tar -xzf startup-vc-platform.tar.gz
sudo chown -R startup-vc:startup-vc /opt/startup-vc
```

### Вариант 2: Клонирование из Git (если у вас есть репозиторий)

```bash
cd /opt/startup-vc
sudo -u startup-vc git clone https://github.com/your-username/startup-vc-platform.git app
```

### Вариант 3: Создание файлов вручную

```bash
cd /opt/startup-vc
sudo -u startup-vc mkdir app
cd app

# Создайте структуру проекта
sudo -u startup-vc mkdir -p {app/{api,core,data,email,ai},alembic/versions,deployment,monitoring,scripts,docs}
```

## Шаг 7: Установка Python зависимостей

```bash
cd /opt/startup-vc
sudo -u startup-vc python3.11 -m venv venv
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install --upgrade pip

# Установка основных зависимостей
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install fastapi uvicorn python-multipart python-dotenv pydantic==1.10.13
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib[bcrypt] email-validator
```

## Шаг 8: Настройка переменных окружения

```bash
sudo -u startup-vc nano /opt/startup-vc/.env
```

Содержимое `.env` файла:
```env
# Database
DATABASE_URL=postgresql://startup_vc_user:secure_password_123@localhost:5432/startup_vc_db

# Security
JWT_SECRET_KEY=your_super_secret_jwt_key_here_minimum_32_characters_long_please_change_this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=Startup VC Platform
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# File Storage
UPLOAD_DIR=/opt/startup-vc/uploads
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/startup-vc/logs/app.log
```

## Шаг 9: Создание необходимых директорий

```bash
sudo -u startup-vc mkdir -p /opt/startup-vc/{logs,uploads,static,backups}
sudo chmod 755 /opt/startup-vc/{logs,uploads,static,backups}
```

## Шаг 10: Запуск миграций базы данных

```bash
cd /opt/startup-vc/app
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head
```

## Шаг 11: Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/startup-vc
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;  # Замените на ваш IP или домен

    # Static files
    location /static/ {
        alias /opt/startup-vc/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads/ {
        alias /opt/startup-vc/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API and application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # File upload size
        client_max_body_size 10M;
    }
}
```

Активируйте конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/startup-vc /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Шаг 12: Настройка Supervisor

```bash
sudo nano /etc/supervisor/conf.d/startup-vc.conf
```

Содержимое:
```ini
[program:startup-vc]
command=/opt/startup-vc/venv/bin/uvicorn minimal_app:app --host 127.0.0.1 --port 8000 --workers 2
directory=/opt/startup-vc/app
user=startup-vc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/startup-vc/logs/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/startup-vc/venv/bin"
```

Перезапустите Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start startup-vc
```

## Шаг 13: Настройка брандмауэра

```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## Шаг 14: Проверка работы

### Проверка статуса сервисов
```bash
sudo systemctl status nginx postgresql redis-server supervisor
sudo supervisorctl status
```

### Проверка приложения
```bash
# Проверка health check
curl http://localhost:8000/health

# Проверка через внешний IP
curl http://YOUR_VPS_IP/health
```

### Просмотр логов
```bash
sudo tail -f /opt/startup-vc/logs/app.log
```

## Шаг 15: Настройка SSL (опционально, но рекомендуется)

### Установка Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Получение SSL сертификата (если у вас есть домен)
```bash
sudo certbot --nginx -d your-domain.com
```

### Автоматическое обновление сертификата
```bash
sudo crontab -e
# Добавьте строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Управление приложением

### Перезапуск приложения
```bash
sudo supervisorctl restart startup-vc
```

### Просмотр логов
```bash
sudo tail -f /opt/startup-vc/logs/app.log
```

### Обновление приложения
```bash
cd /opt/startup-vc/app
sudo -u startup-vc git pull  # если используете git
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head
sudo supervisorctl restart startup-vc
```

### Проверка использования ресурсов
```bash
htop
df -h
free -h
```

## Доступ к приложению

После успешного развертывания ваше приложение будет доступно по адресу:

- **HTTP**: `http://YOUR_VPS_IP`
- **API документация**: `http://YOUR_VPS_IP/docs`
- **Health check**: `http://YOUR_VPS_IP/health`
- **API эндпоинты**: `http://YOUR_VPS_IP/api/`

## Основные эндпоинты для тестирования

```bash
# Health check
curl http://YOUR_VPS_IP/health

# API health
curl http://YOUR_VPS_IP/api/health

# Регистрация пользователя
curl -X POST "http://YOUR_VPS_IP/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123",
    "full_name": "Test User",
    "first_name": "Test",
    "last_name": "User",
    "company_name": "Test Company",
    "role": "startup"
  }'

# Вход пользователя
curl -X POST "http://YOUR_VPS_IP/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123"
  }'
```

## Устранение неполадок

### Если приложение не запускается:
```bash
# Проверьте логи
sudo tail -f /opt/startup-vc/logs/app.log

# Проверьте статус
sudo supervisorctl status startup-vc

# Проверьте подключение к БД
sudo -u postgres psql -d startup_vc_db -c "\dt"
```

### Если Nginx не работает:
```bash
# Проверьте конфигурацию
sudo nginx -t

# Проверьте статус
sudo systemctl status nginx

# Проверьте логи
sudo tail -f /var/log/nginx/error.log
```

### Если проблемы с базой данных:
```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Проверьте подключение
sudo -u postgres psql -d startup_vc_db

# Проверьте логи
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

**Важно**: Замените `YOUR_VPS_IP` на реальный IP адрес вашего сервера во всех командах и конфигурациях.

**Время развертывания**: 30-45 минут  
**Сложность**: Средняя  
**Результат**: Полностью работающее приложение на VPS
