# Инструкция по развертыванию Startup VC Platform на VPS сервере

## Системные требования

### Минимальные требования:
- **CPU**: 2 ядра
- **RAM**: 4 GB
- **Диск**: 20 GB SSD
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+

### Рекомендуемые требования:
- **CPU**: 4 ядра
- **RAM**: 8 GB
- **Диск**: 50 GB SSD
- **ОС**: Ubuntu 22.04 LTS

## Подготовка сервера

### 1. Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
# или для новых версий
sudo dnf update -y
```

### 2. Установка необходимых пакетов

```bash
# Ubuntu/Debian
sudo apt install -y curl wget git nginx postgresql postgresql-contrib redis-server supervisor htop

# CentOS/RHEL
sudo yum install -y curl wget git nginx postgresql-server postgresql-contrib redis supervisor htop
```

### 3. Установка Python 3.11+

```bash
# Ubuntu 22.04+ (Python 3.11 уже включен)
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Для более старых версий Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# CentOS/RHEL
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
```

## Настройка базы данных PostgreSQL

### 1. Инициализация PostgreSQL

```bash
# Ubuntu/Debian
sudo -u postgres createuser --interactive
# Введите имя пользователя: startup_vc_user
# Создать суперпользователя? y

sudo -u postgres createdb startup_vc_db

# CentOS/RHEL
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres createuser --interactive
sudo -u postgres createdb startup_vc_db
```

### 2. Настройка пароля для пользователя

```bash
sudo -u postgres psql
```

```sql
ALTER USER startup_vc_user PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE startup_vc_db TO startup_vc_user;
\q
```

### 3. Настройка PostgreSQL для удаленных подключений

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

Добавьте в конец:
```
host    startup_vc_db    startup_vc_user    0.0.0.0/0    md5
```

Перезапустите PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Настройка Redis

### 1. Настройка Redis

```bash
sudo nano /etc/redis/redis.conf
```

Найдите и измените:
```
bind 127.0.0.1 ::1
# на
bind 0.0.0.0

# Добавьте пароль для безопасности
requirepass your_redis_password_here
```

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## Развертывание приложения

### 1. Создание пользователя для приложения

```bash
sudo adduser --system --group --home /opt/startup-vc startup-vc
```

### 2. Клонирование репозитория

```bash
sudo -u startup-vc git clone https://github.com/your-repo/startup-vc-platform.git /opt/startup-vc/app
cd /opt/startup-vc/app
```

### 3. Создание виртуального окружения

```bash
sudo -u startup-vc python3.11 -m venv /opt/startup-vc/venv
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install --upgrade pip
```

### 4. Установка зависимостей

```bash
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install -r requirements_simple.txt
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib[bcrypt] email-validator
```

### 5. Настройка переменных окружения

```bash
sudo -u startup-vc nano /opt/startup-vc/.env
```

Содержимое `.env`:
```env
# Database
DATABASE_URL=postgresql://startup_vc_user:your_secure_password_here@localhost:5432/startup_vc_db

# Redis
REDIS_URL=redis://:your_redis_password_here@localhost:6379/0

# Security
JWT_SECRET_KEY=your_super_secret_jwt_key_here_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=Startup VC Platform
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# Email (настройте согласно вашему провайдеру)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=True

# External APIs (optional)
CLAUDE_API_KEY=your-claude-api-key
OPENAI_API_KEY=your-openai-api-key

# File Storage
UPLOAD_DIR=/opt/startup-vc/uploads
MAX_FILE_SIZE=10485760  # 10MB

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/startup-vc/logs/app.log
```

### 6. Создание необходимых директорий

```bash
sudo -u startup-vc mkdir -p /opt/startup-vc/{logs,uploads,static,backups}
sudo chmod 755 /opt/startup-vc/{logs,uploads,static,backups}
```

### 7. Запуск миграций базы данных

```bash
cd /opt/startup-vc/app
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head
```

## Настройка Nginx

### 1. Создание конфигурации Nginx

```bash
sudo nano /etc/nginx/sites-available/startup-vc
```

Содержимое:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # File upload size
    client_max_body_size 10M;

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
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/startup-vc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Настройка SSL сертификата (Let's Encrypt)

### 1. Установка Certbot

```bash
# Ubuntu/Debian
sudo apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo dnf install -y certbot python3-certbot-nginx
```

### 2. Получение SSL сертификата

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Настройка Supervisor

### 1. Создание конфигурации для FastAPI

```bash
sudo nano /etc/supervisor/conf.d/startup-vc.conf
```

Содержимое:
```ini
[program:startup-vc]
command=/opt/startup-vc/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
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

### 2. Создание конфигурации для Celery Worker

```bash
sudo nano /etc/supervisor/conf.d/startup-vc-celery.conf
```

Содержимое:
```ini
[program:startup-vc-celery]
command=/opt/startup-vc/venv/bin/celery -A app.core.celery_app worker --loglevel=info --concurrency=2
directory=/opt/startup-vc/app
user=startup-vc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/startup-vc/logs/celery.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/startup-vc/venv/bin"
```

### 3. Создание конфигурации для Celery Beat

```bash
sudo nano /etc/supervisor/conf.d/startup-vc-beat.conf
```

Содержимое:
```ini
[program:startup-vc-beat]
command=/opt/startup-vc/venv/bin/celery -A app.core.celery_app beat --loglevel=info
directory=/opt/startup-vc/app
user=startup-vc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/startup-vc/logs/celery-beat.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/startup-vc/venv/bin"
```

### 4. Перезапуск Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## Настройка брандмауэра

### 1. UFW (Ubuntu)

```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### 2. Firewalld (CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Настройка резервного копирования

### 1. Создание скрипта резервного копирования

```bash
sudo nano /opt/startup-vc/backup.sh
```

Содержимое:
```bash
#!/bin/bash

BACKUP_DIR="/opt/startup-vc/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="startup_vc_db"
DB_USER="startup_vc_user"

# Создание резервной копии базы данных
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Создание резервной копии файлов приложения
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt/startup-vc app uploads

# Удаление старых резервных копий (старше 30 дней)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
sudo chmod +x /opt/startup-vc/backup.sh
```

### 2. Настройка cron для автоматического резервного копирования

```bash
sudo crontab -e
```

Добавьте:
```
# Ежедневное резервное копирование в 2:00
0 2 * * * /opt/startup-vc/backup.sh
```

## Мониторинг и логирование

### 1. Настройка ротации логов

```bash
sudo nano /etc/logrotate.d/startup-vc
```

Содержимое:
```
/opt/startup-vc/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 startup-vc startup-vc
    postrotate
        supervisorctl restart startup-vc
        supervisorctl restart startup-vc-celery
        supervisorctl restart startup-vc-beat
    endscript
}
```

### 2. Настройка мониторинга системы

```bash
# Установка htop для мониторинга
sudo apt install -y htop iotop nethogs

# Проверка статуса сервисов
sudo systemctl status nginx postgresql redis-server supervisor
```

## Проверка развертывания

### 1. Проверка статуса сервисов

```bash
# Проверка всех сервисов
sudo systemctl status nginx postgresql redis-server supervisor

# Проверка процессов приложения
sudo supervisorctl status

# Проверка логов
sudo tail -f /opt/startup-vc/logs/app.log
```

### 2. Тестирование API

```bash
# Проверка health check
curl https://your-domain.com/health

# Проверка API документации
curl https://your-domain.com/docs
```

### 3. Проверка базы данных

```bash
sudo -u postgres psql -d startup_vc_db -c "\dt"
```

## Обновление приложения

### 1. Создание скрипта обновления

```bash
sudo nano /opt/startup-vc/update.sh
```

Содержимое:
```bash
#!/bin/bash

cd /opt/startup-vc/app

# Остановка приложения
sudo supervisorctl stop startup-vc startup-vc-celery startup-vc-beat

# Создание резервной копии
/opt/startup-vc/backup.sh

# Обновление кода
sudo -u startup-vc git pull origin main

# Обновление зависимостей
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install -r requirements_simple.txt

# Запуск миграций
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head

# Запуск приложения
sudo supervisorctl start startup-vc startup-vc-celery startup-vc-beat

echo "Update completed successfully"
```

```bash
sudo chmod +x /opt/startup-vc/update.sh
```

## Безопасность

### 1. Настройка SSH

```bash
sudo nano /etc/ssh/sshd_config
```

Рекомендуемые настройки:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Изменить стандартный порт
```

### 2. Настройка fail2ban

```bash
sudo apt install -y fail2ban

sudo nano /etc/fail2ban/jail.local
```

Содержимое:
```
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222

[nginx-http-auth]
enabled = true
```

### 3. Регулярные обновления

```bash
# Автоматические обновления безопасности
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Масштабирование

### 1. Горизонтальное масштабирование

Для увеличения производительности можно:
- Добавить больше worker процессов в supervisor конфигурации
- Использовать load balancer (nginx upstream)
- Настроить несколько серверов приложения

### 2. Вертикальное масштабирование

- Увеличить RAM и CPU
- Оптимизировать настройки PostgreSQL
- Использовать Redis Cluster для больших нагрузок

## Устранение неполадок

### 1. Проверка логов

```bash
# Логи приложения
sudo tail -f /opt/startup-vc/logs/app.log

# Логи Nginx
sudo tail -f /var/log/nginx/error.log

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 2. Проверка ресурсов

```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Сетевые соединения
netstat -tlnp
```

### 3. Перезапуск сервисов

```bash
# Перезапуск приложения
sudo supervisorctl restart startup-vc

# Перезапуск всех сервисов
sudo systemctl restart nginx postgresql redis-server supervisor
```

## Контакты и поддержка

При возникновении проблем проверьте:
1. Логи приложения: `/opt/startup-vc/logs/`
2. Статус сервисов: `sudo systemctl status`
3. Конфигурацию Nginx: `sudo nginx -t`
4. Подключение к базе данных: `sudo -u postgres psql -d startup_vc_db`

---

**Примечание**: Замените `your-domain.com`, `your_secure_password_here` и другие плейсхолдеры на ваши реальные значения перед развертыванием.
