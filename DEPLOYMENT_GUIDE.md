# 🚀 Руководство по развертыванию Startup VC Platform

## 🎯 Быстрый старт (Автоматическая установка)

Для быстрого развертывания используйте автоматический скрипт:

```bash
# Скачайте скрипт на сервер
wget https://raw.githubusercontent.com/your-username/startup-vc-platform/main/install_vps.sh

# Запустите автоматическую установку
sudo bash install_vps.sh
```

Скрипт автоматически:
- Установит все зависимости
- Настроит PostgreSQL и Redis
- Создаст пользователя приложения
- Склонирует проект
- Настроит systemd сервисы
- Запустит приложение

## 📁 Структура проекта

```
startup-vc-platform/
├── app/                    # Основное приложение
│   ├── main.py           # Точка входа FastAPI
│   ├── core/             # Основная логика
│   ├── api/              # API endpoints
│   ├── data/             # Модели и репозитории
│   ├── ai/               # AI модули
│   ├── email/            # Email система
│   └── integrations/     # Внешние интеграции
├── alembic/              # Миграции БД
├── run.py                # Точка входа приложения
├── requirements.txt      # Зависимости
├── .env                  # Переменные окружения
├── install_vps.sh       # Автоматический скрипт установки
└── DEPLOYMENT_GUIDE.md   # Это руководство
```

## 📋 Предварительные требования

### Системные требования
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 4GB (минимум), 8GB (рекомендуется)
- **CPU**: 2 ядра (минимум), 4 ядра (рекомендуется)
- **Диск**: 20GB SSD (минимум), 50GB SSD (рекомендуется)

### Необходимые пакеты
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx
- Git

## 🔧 Установка на Ubuntu/Debian

### Шаг 1: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### Шаг 2: Установка Python 3.11

```bash
# Добавление репозитория deadsnakes
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Установка Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Установка pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
```

### Шаг 3: Установка PostgreSQL

```bash
# Установка PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Запуск и включение PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание пользователя и базы данных
sudo -u postgres createuser --interactive --pwprompt startup_vc_user
sudo -u postgres createdb startup_vc_db

# Настройка прав доступа
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE startup_vc_db TO startup_vc_user;"
```

### Шаг 4: Установка Redis

```bash
# Установка Redis
sudo apt install -y redis-server

# Запуск и включение Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка работы Redis
redis-cli ping
```

### Шаг 5: Установка Nginx

```bash
# Установка Nginx
sudo apt install -y nginx

# Запуск и включение Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 📦 Развертывание приложения

### Шаг 1: Создание пользователя приложения

```bash
# Создание пользователя
sudo adduser --system --group --home /opt/startup-vc startup-vc

# Создание директорий
sudo mkdir -p /opt/startup-vc/{app,logs,uploads,static,backups}
sudo chown -R startup-vc:startup-vc /opt/startup-vc
```

### Шаг 2: Клонирование проекта

```bash
# Переход в директорию приложения
cd /opt/startup-vc

# Клонирование репозитория
sudo -u startup-vc git clone https://github.com/your-username/startup-vc-platform.git app

# Переход в директорию проекта
cd app
```

### Шаг 3: Создание виртуального окружения

```bash
# Создание виртуального окружения
sudo -u startup-vc python3.11 -m venv /opt/startup-vc/venv

# Активация виртуального окружения
source /opt/startup-vc/venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

### Шаг 4: Установка зависимостей

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Или установка по категориям
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic
pip install python-jose[cryptography] passlib[bcrypt] email-validator
pip install celery redis python-dotenv
```

### Шаг 5: Настройка переменных окружения

```bash
# Создание .env файла
sudo -u startup-vc nano /opt/startup-vc/app/.env
```

**Содержимое .env файла:**
```env
# Основные настройки
PROJECT_NAME=Startup-VC Communication Platform
SECRET_KEY=your-secret-key-here-change-this-in-production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# База данных
POSTGRES_SERVER=localhost
POSTGRES_USER=startup_vc_user
POSTGRES_PASSWORD=your_database_password
POSTGRES_DB=startup_vc_db
DATABASE_URL=postgresql://startup_vc_user:your_database_password@localhost:5432/startup_vc_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
JWT_SECRET_KEY=your-jwt-secret-key-here-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Email (настройте под ваши нужды)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@startup-vc-platform.com
EMAILS_FROM_NAME=Startup-VC Platform

# AI (опционально)
OPENAI_API_KEY=your-openai-api-key-here

# Первый суперпользователь
FIRST_SUPERUSER=admin@startup-vc-platform.com
FIRST_SUPERUSER_PASSWORD=admin123

# Файлы
MAX_FILE_SIZE=10485760
UPLOAD_FOLDER=uploads

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://YOUR_SERVER_IP:8000

# Производительность
WORKERS=2
```

### Шаг 6: Запуск миграций базы данных

```bash
# Активация виртуального окружения
source /opt/startup-vc/venv/bin/activate

# Запуск миграций
cd /opt/startup-vc/app
alembic upgrade head
```

## 🚀 Запуск приложения

### Вариант 1: Прямой запуск (для тестирования)

```bash
# Активация виртуального окружения
source /opt/startup-vc/venv/bin/activate

# Переход в директорию приложения
cd /opt/startup-vc/app

# Запуск приложения
python run.py
```

### Вариант 2: Запуск с Gunicorn (рекомендуется для продакшена)

```bash
# Установка Gunicorn
pip install gunicorn

# Запуск с Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Вариант 3: Запуск с systemd (автозапуск)

```bash
# Создание systemd сервиса
sudo nano /etc/systemd/system/startup-vc.service
```

**Содержимое файла сервиса:**
```ini
[Unit]
Description=Startup VC Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=startup-vc
Group=startup-vc
WorkingDirectory=/opt/startup-vc/app
Environment=PATH=/opt/startup-vc/venv/bin
ExecStart=/opt/startup-vc/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Запуск сервиса:**
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable startup-vc

# Запуск сервиса
sudo systemctl start startup-vc

# Проверка статуса
sudo systemctl status startup-vc
```

## 🌐 Настройка Nginx

### Создание конфигурации Nginx

```bash
# Создание конфигурации
sudo nano /etc/nginx/sites-available/startup-vc
```

**Содержимое конфигурации:**
```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP;  # Замените на ваш IP или домен

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

**Активация конфигурации:**
```bash
# Создание символической ссылки
sudo ln -s /etc/nginx/sites-available/startup-vc /etc/nginx/sites-enabled/

# Удаление дефолтной конфигурации
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
```

## 🔧 Настройка Celery (фоновые задачи)

### Создание systemd сервиса для Celery Worker

```bash
# Создание сервиса для Celery Worker
sudo nano /etc/systemd/system/startup-vc-celery.service
```

**Содержимое файла:**
```ini
[Unit]
Description=Startup VC Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=startup-vc
Group=startup-vc
WorkingDirectory=/opt/startup-vc/app
Environment=PATH=/opt/startup-vc/venv/bin
ExecStart=/opt/startup-vc/venv/bin/celery -A app.core.celery_app worker --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Создание systemd сервиса для Celery Beat

```bash
# Создание сервиса для Celery Beat
sudo nano /etc/systemd/system/startup-vc-celery-beat.service
```

**Содержимое файла:**
```ini
[Unit]
Description=Startup VC Celery Beat
After=network.target redis.service

[Service]
Type=exec
User=startup-vc
Group=startup-vc
WorkingDirectory=/opt/startup-vc/app
Environment=PATH=/opt/startup-vc/venv/bin
ExecStart=/opt/startup-vc/venv/bin/celery -A app.core.celery_app beat --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Запуск Celery сервисов:**
```bash
# Включение и запуск сервисов
sudo systemctl enable startup-vc-celery startup-vc-celery-beat
sudo systemctl start startup-vc-celery startup-vc-celery-beat

# Проверка статуса
sudo systemctl status startup-vc-celery startup-vc-celery-beat
```

## 🔥 Настройка брандмауэра

```bash
# Установка UFW
sudo apt install -y ufw

# Настройка правил
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 8000
sudo ufw --force enable

# Проверка статуса
sudo ufw status
```

## 📊 Проверка развертывания

### Проверка сервисов

```bash
# Проверка статуса всех сервисов
sudo systemctl status startup-vc startup-vc-celery startup-vc-celery-beat nginx postgresql redis-server

# Проверка логов
sudo journalctl -u startup-vc -f
```

### Проверка приложения

```bash
# Локальная проверка
curl http://localhost:8000/health

# Внешняя проверка
curl http://YOUR_SERVER_IP/health

# Проверка API документации
curl http://YOUR_SERVER_IP/docs
```

## 🛠️ Управление приложением

### Основные команды

```bash
# Запуск приложения
sudo systemctl start startup-vc

# Остановка приложения
sudo systemctl stop startup-vc

# Перезапуск приложения
sudo systemctl restart startup-vc

# Просмотр логов
sudo journalctl -u startup-vc -f

# Проверка статуса
sudo systemctl status startup-vc
```

### Обновление приложения

```bash
# Переход в директорию приложения
cd /opt/startup-vc/app

# Остановка сервисов
sudo systemctl stop startup-vc startup-vc-celery startup-vc-celery-beat

# Обновление кода
sudo -u startup-vc git pull origin main

# Активация виртуального окружения
source /opt/startup-vc/venv/bin/activate

# Обновление зависимостей
pip install -r requirements.txt

# Запуск миграций
alembic upgrade head

# Запуск сервисов
sudo systemctl start startup-vc startup-vc-celery startup-vc-celery-beat
```

## 🔍 Устранение неполадок

### Если приложение не запускается

```bash
# Проверьте логи
sudo journalctl -u startup-vc -f

# Проверьте конфигурацию
sudo nginx -t

# Проверьте подключение к БД
sudo -u postgres psql -d startup_vc_db -c "\dt"
```

### Если проблемы с базой данных

```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Проверьте подключение
sudo -u postgres psql -d startup_vc_db

# Проверьте логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Если проблемы с Redis

```bash
# Проверьте статус Redis
sudo systemctl status redis-server

# Проверьте подключение
redis-cli ping

# Проверьте логи Redis
sudo tail -f /var/log/redis/redis-server.log
```

## 📈 Мониторинг

### Проверка использования ресурсов

```bash
# Мониторинг процессов
htop

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Проверка сетевых подключений
netstat -tulpn | grep :8000
```

## 🎯 Заключение

После выполнения всех шагов ваше приложение будет доступно по адресу:
- **HTTP**: http://YOUR_SERVER_IP
- **API документация**: http://YOUR_SERVER_IP/docs
- **Health check**: http://YOUR_SERVER_IP/health

**Время развертывания**: 30-45 минут  
**Сложность**: Средняя  
**Результат**: Полностью работающее приложение без Docker
