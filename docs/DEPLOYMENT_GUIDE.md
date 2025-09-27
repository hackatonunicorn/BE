# 🚀 Руководство по развертыванию

Полное руководство по развертыванию Startup-VC Platform в production среде.

## 📋 Содержание

- [Подготовка сервера](#-подготовка-сервера)
- [Конфигурация окружения](#-конфигурация-окружения)
- [SSL сертификаты](#-ssl-сертификаты)
- [Развертывание](#-развертывание)
- [Мониторинг](#-мониторинг)
- [Бэкапы](#-бэкапы)
- [Масштабирование](#-масштабирование)
- [Обновления](#-обновления)

## 🖥 Подготовка сервера

### Требования к серверу

**Минимальные требования:**
- CPU: 4 ядра
- RAM: 8GB
- Диск: 100GB SSD
- Сеть: 1Gbps

**Рекомендуемые требования:**
- CPU: 8 ядер
- RAM: 16GB
- Диск: 500GB SSD
- Сеть: 10Gbps

### Операционная система

**Ubuntu 22.04 LTS (рекомендуется):**

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите необходимые пакеты
sudo apt install -y curl wget git unzip software-properties-common

# Настройте часовой пояс
sudo timedatectl set-timezone UTC
```

**CentOS 8 / RHEL 8:**

```bash
# Обновите систему
sudo yum update -y

# Установите необходимые пакеты
sudo yum install -y curl wget git unzip
```

### Установка Docker

```bash
# Скачайте и запустите установочный скрипт Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Установите Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверьте установку
docker --version
docker-compose --version
```

### Настройка файрвола

```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## ⚙️ Конфигурация окружения

### Создание пользователя приложения

```bash
# Создайте пользователя для приложения
sudo useradd -m -s /bin/bash startup-vc
sudo usermod -aG docker startup-vc

# Создайте директории
sudo mkdir -p /opt/startup-vc/{logs,backups,uploads,ssl,config}
sudo chown -R startup-vc:startup-vc /opt/startup-vc

# Переключитесь на пользователя приложения
sudo su - startup-vc
```

### Клонирование репозитория

```bash
# Перейдите в домашнюю директорию
cd /opt/startup-vc

# Клонируйте репозиторий
git clone https://github.com/your-org/startup-vc-platform.git .

# Создайте ветку для production
git checkout -b production
```

### Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте конфигурацию
nano .env
```

**Пример .env файла для production:**

```bash
# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
POSTGRES_DB=startup_vc_prod
POSTGRES_USER=startup_vc_user
POSTGRES_PASSWORD=your_secure_database_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://startup_vc_user:your_secure_database_password_here@postgres:5432/startup_vc_prod

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_secure_redis_password_here
REDIS_URL=redis://:your_secure_redis_password_here@redis:6379/0

# Security
SECRET_KEY=your_super_secret_key_minimum_32_characters_long
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters_long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# External APIs
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration
SMTP_SERVER=smtp.your-provider.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@your-domain.com
EMAIL_PASSWORD=your_email_password_here
FROM_EMAIL=noreply@your-domain.com

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Monitoring
GRAFANA_PASSWORD=your_secure_grafana_password_here
PROMETHEUS_RETENTION=30d

# Backup
BACKUP_S3_BUCKET=your-backup-bucket-name
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
BACKUP_RETENTION_DAYS=30

# Domain Configuration
DOMAIN_NAME=your-domain.com
SSL_EMAIL=admin@your-domain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20

# File Upload
MAX_FILE_SIZE=50MB
ALLOWED_FILE_TYPES=pdf,pptx,docx,txt

# Notification
NOTIFICATION_WEBHOOK=https://your-domain.com/api/v1/webhooks/notifications
```

### Генерация секретных ключей

```bash
# Генерируйте SECRET_KEY
openssl rand -hex 32

# Генерируйте JWT_SECRET_KEY
openssl rand -hex 32

# Генерируйте пароли
openssl rand -base64 32
```

## 🔒 SSL сертификаты

### Получение Let's Encrypt сертификата

```bash
# Установите Certbot
sudo apt install -y certbot

# Получите сертификат
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com -d monitoring.your-domain.com

# Проверьте сертификат
sudo certbot certificates
```

### Настройка автоматического обновления

```bash
# Создайте скрипт обновления
sudo nano /opt/startup-vc/scripts/renew-ssl.sh
```

```bash
#!/bin/bash
# Скрипт обновления SSL сертификатов

# Обновите сертификат
certbot renew --quiet

# Скопируйте новые сертификаты
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/startup-vc/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/startup-vc/ssl/key.pem

# Установите правильные права
chmod 644 /opt/startup-vc/ssl/cert.pem
chmod 600 /opt/startup-vc/ssl/key.pem

# Перезапустите Nginx
docker-compose -f /opt/startup-vc/docker-compose.prod.yml restart nginx

echo "SSL certificates renewed successfully"
```

```bash
# Сделайте скрипт исполняемым
sudo chmod +x /opt/startup-vc/scripts/renew-ssl.sh

# Добавьте в crontab
sudo crontab -e
# Добавьте строку:
0 2 * * * /opt/startup-vc/scripts/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

### Копирование сертификатов

```bash
# Скопируйте сертификаты в директорию проекта
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/startup-vc/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/startup-vc/ssl/key.pem

# Установите права доступа
sudo chown startup-vc:startup-vc /opt/startup-vc/ssl/*
sudo chmod 644 /opt/startup-vc/ssl/cert.pem
sudo chmod 600 /opt/startup-vc/ssl/key.pem
```

## 🚀 Развертывание

### Первоначальное развертывание

```bash
# Перейдите в директорию проекта
cd /opt/startup-vc

# Создайте необходимые директории
mkdir -p {logs,backups,uploads,ssl,config}

# Скопируйте конфигурационные файлы
cp -r deployment/nginx/ssl/* ssl/

# Запустите только базы данных для инициализации
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Подождите, пока базы данных запустятся
sleep 30

# Выполните миграции
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Создайте суперпользователя
docker-compose -f docker-compose.prod.yml run --rm app python -c "
from app.core.database import get_db
from app.data.models import User
from app.core.auth import get_password_hash
import json

db = next(get_db())
superuser = User(
    username='admin',
    email='admin@your-domain.com',
    full_name='System Administrator',
    hashed_password=get_password_hash('admin_password_change_me'),
    is_superuser=True,
    is_active=True
)
db.add(superuser)
db.commit()
print('Superuser created successfully')
"

# Запустите все сервисы
docker-compose -f docker-compose.prod.yml up -d

# Проверьте статус всех сервисов
docker-compose -f docker-compose.prod.yml ps
```

### Проверка развертывания

```bash
# Проверьте health check
curl -k https://your-domain.com/health

# Проверьте API документацию
curl -k https://your-domain.com/docs

# Проверьте мониторинг
curl -k https://monitoring.your-domain.com/grafana

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f app
```

### Настройка systemd сервисов

```bash
# Создайте systemd сервис
sudo nano /etc/systemd/system/startup-vc.service
```

```ini
[Unit]
Description=Startup VC Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/startup-vc
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=startup-vc

[Install]
WantedBy=multi-user.target
```

```bash
# Включите и запустите сервис
sudo systemctl daemon-reload
sudo systemctl enable startup-vc.service
sudo systemctl start startup-vc.service

# Проверьте статус
sudo systemctl status startup-vc.service
```

## 📊 Мониторинг

### Настройка базовой аутентификации для мониторинга

```bash
# Создайте файл с паролями для мониторинга
sudo htpasswd -c /opt/startup-vc/monitoring/.htpasswd admin
# Введите пароль для admin

# Создайте дополнительные пользователи
sudo htpasswd /opt/startup-vc/monitoring/.htpasswd monitoring-user
```

### Настройка алертов

```bash
# Создайте конфигурацию Alertmanager
nano monitoring/alertmanager/alertmanager.yml
```

```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@your-domain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'https://your-domain.com/api/v1/webhooks/alerts'
    send_resolved: true
  email_configs:
  - to: 'admin@your-domain.com'
    subject: 'Startup VC Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

### Настройка Grafana дашбордов

```bash
# Импортируйте дашборды
curl -X POST \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/startup-vc-overview.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

## 💾 Бэкапы

### Настройка автоматических бэкапов

```bash
# Создайте скрипт бэкапа
nano scripts/backup.sh
```

```bash
#!/bin/bash
# Автоматический бэкап базы данных

BACKUP_DIR="/opt/startup-vc/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

# Создайте бэкап
docker-compose -f /opt/startup-vc/docker-compose.prod.yml exec -T postgres pg_dump -U startup_vc_user startup_vc_prod > "$BACKUP_FILE"

# Сожмите бэкап
gzip "$BACKUP_FILE"

# Загрузите в S3 (если настроено)
if [ -n "$BACKUP_S3_BUCKET" ]; then
    aws s3 cp "${BACKUP_FILE}.gz" "s3://$BACKUP_S3_BUCKET/database-backups/"
fi

# Удалите старые бэкапы (старше 30 дней)
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

```bash
# Сделайте скрипт исполняемым
chmod +x scripts/backup.sh

# Добавьте в crontab для ежедневных бэкапов
crontab -e
# Добавьте строку:
0 3 * * * /opt/startup-vc/scripts/backup.sh >> /var/log/startup-vc-backup.log 2>&1
```

### Восстановление из бэкапа

```bash
# Создайте скрипт восстановления
nano scripts/restore.sh
```

```bash
#!/bin/bash
# Восстановление из бэкапа

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Остановите приложение
docker-compose -f /opt/startup-vc/docker-compose.prod.yml stop app

# Восстановите базу данных
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker-compose -f /opt/startup-vc/docker-compose.prod.yml exec -T postgres psql -U startup_vc_user -d startup_vc_prod
else
    docker-compose -f /opt/startup-vc/docker-compose.prod.yml exec -T postgres psql -U startup_vc_user -d startup_vc_prod < "$BACKUP_FILE"
fi

# Запустите приложение
docker-compose -f /opt/startup-vc/docker-compose.prod.yml start app

echo "Restore completed from: $BACKUP_FILE"
```

```bash
# Сделайте скрипт исполняемым
chmod +x scripts/restore.sh
```

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Увеличьте количество экземпляров приложения
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Увеличьте количество Celery worker'ов
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=5
```

### Настройка load balancer

```bash
# Обновите nginx конфигурацию
nano deployment/nginx/conf.d/default.conf
```

```nginx
upstream app_backend {
    least_conn;
    server app_1:8000 max_fails=3 fail_timeout=30s;
    server app_2:8000 max_fails=3 fail_timeout=30s;
    server app_3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

### Мониторинг производительности

```bash
# Установите htop для мониторинга ресурсов
sudo apt install -y htop

# Мониторинг Docker ресурсов
docker stats

# Мониторинг логов
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

## 🔄 Обновления

### Процедура обновления

```bash
# Создайте скрипт обновления
nano scripts/update.sh
```

```bash
#!/bin/bash
# Скрипт обновления приложения

set -e

echo "Starting application update..."

# Создайте бэкап перед обновлением
./scripts/backup.sh

# Получите последние изменения
git fetch origin
git checkout production
git pull origin production

# Пересоберите образы
docker-compose -f docker-compose.prod.yml build

# Выполните миграции
docker-compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Перезапустите сервисы с нулевым downtime
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Проверьте health check
sleep 30
curl -f https://your-domain.com/health || {
    echo "Health check failed, rolling back..."
    git checkout HEAD~1
    docker-compose -f docker-compose.prod.yml up -d --force-recreate
    exit 1
}

echo "Update completed successfully!"
```

```bash
# Сделайте скрипт исполняемым
chmod +x scripts/update.sh
```

### Zero-downtime deployment

```bash
# Создайте скрипт для zero-downtime deployment
nano scripts/zero-downtime-deploy.sh
```

```bash
#!/bin/bash
# Zero-downtime deployment

set -e

# Создайте новый образ
docker-compose -f docker-compose.prod.yml build app

# Запустите новый контейнер параллельно
docker-compose -f docker-compose.prod.yml up -d --scale app=4 --no-recreate

# Подождите, пока новый контейнер запустится
sleep 30

# Проверьте health check нового контейнера
NEW_CONTAINER=$(docker-compose -f docker-compose.prod.yml ps -q app | head -1)
docker exec $NEW_CONTAINER curl -f http://localhost:8000/health

# Удалите старые контейнеры
docker-compose -f docker-compose.prod.yml up -d --scale app=3 --no-recreate

echo "Zero-downtime deployment completed!"
```

## 🔧 Поддержка и обслуживание

### Еженедельные задачи

```bash
# Создайте скрипт еженедельного обслуживания
nano scripts/weekly-maintenance.sh
```

```bash
#!/bin/bash
# Еженедельное обслуживание системы

echo "Starting weekly maintenance..."

# Очистите неиспользуемые Docker ресурсы
docker system prune -f

# Очистите старые логи
find /opt/startup-vc/logs -name "*.log" -mtime +7 -delete

# Обновите статистику базы данных
docker-compose -f docker-compose.prod.yml exec postgres psql -U startup_vc_user -d startup_vc_prod -c "ANALYZE;"

# Перезапустите сервисы для освобождения памяти
docker-compose -f docker-compose.prod.yml restart app

echo "Weekly maintenance completed!"
```

```bash
# Добавьте в crontab
crontab -e
# Добавьте строку:
0 2 * * 0 /opt/startup-vc/scripts/weekly-maintenance.sh >> /var/log/weekly-maintenance.log 2>&1
```

### Мониторинг дискового пространства

```bash
# Создайте скрипт мониторинга места на диске
nano scripts/disk-monitor.sh
```

```bash
#!/bin/bash
# Мониторинг дискового пространства

DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
    
    # Отправьте уведомление
    curl -X POST "$NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"High disk usage: ${DISK_USAGE}%\", \"level\": \"warning\"}"
fi

if [ $DISK_USAGE -gt 90 ]; then
    echo "CRITICAL: Disk usage is ${DISK_USAGE}%"
    
    # Очистите старые бэкапы
    find /opt/startup-vc/backups -name "backup_*.sql.gz" -mtime +7 -delete
    
    # Очистите Docker образы
    docker image prune -f
fi
```

## ✅ Чек-лист развертывания

### Перед запуском

- [ ] Сервер подготовлен и настроен
- [ ] Docker и Docker Compose установлены
- [ ] SSL сертификаты получены и настроены
- [ ] Переменные окружения настроены
- [ ] Файрволл настроен
- [ ] DNS записи настроены

### После запуска

- [ ] Все сервисы запущены и работают
- [ ] Health check проходит успешно
- [ ] API документация доступна
- [ ] Мониторинг работает
- [ ] Бэкапы настроены
- [ ] Алерты настроены
- [ ] Обновления настроены

### Регулярные проверки

- [ ] Мониторинг дискового пространства
- [ ] Проверка логов на ошибки
- [ ] Проверка производительности
- [ ] Обновление зависимостей
- [ ] Тестирование бэкапов
- [ ] Проверка SSL сертификатов

---

**Важно:** Всегда тестируйте изменения в staging окружении перед применением в production!
