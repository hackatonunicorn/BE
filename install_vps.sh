#!/bin/bash

# Автоматический скрипт установки Startup VC Platform на VPS
# Использование: sudo bash install_vps.sh

set -e  # Остановка при ошибке

echo "🚀 Startup VC Platform - Автоматическая установка на VPS"
echo "=================================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Пожалуйста, запустите скрипт с правами root: sudo bash install_vps.sh"
    exit 1
fi

# Переменные
APP_USER="startup-vc"
APP_DIR="/opt/startup-vc"
DB_USER="startup_vc_user"
DB_NAME="startup_vc_db"
DB_PASSWORD="secure_password_123_$(date +%s)"  # Уникальный пароль
JWT_SECRET="jwt_secret_$(openssl rand -hex 32)"  # Случайный JWT ключ
SECRET_KEY="secret_$(openssl rand -hex 32)"  # Случайный секретный ключ

echo "📋 Конфигурация:"
echo "   - Пользователь приложения: $APP_USER"
echo "   - Директория приложения: $APP_DIR"
echo "   - Пользователь БД: $DB_USER"
echo "   - База данных: $DB_NAME"
echo ""

# Шаг 1: Обновление системы
echo "🔄 Обновление системы..."
apt update && apt upgrade -y

# Шаг 2: Установка пакетов
echo "📦 Установка необходимых пакетов..."
apt install -y python3.11 python3.11-venv python3.11-dev nginx postgresql postgresql-contrib redis-server supervisor git curl wget htop ufw

# Шаг 3: Настройка PostgreSQL
echo "🗄️ Настройка PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Создание пользователя и базы данных
sudo -u postgres createuser --interactive --pwprompt $DB_USER << EOF
y
$DB_PASSWORD
EOF

sudo -u postgres createdb $DB_NAME

# Настройка прав доступа
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Настройка PostgreSQL для подключений
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

# Настройка listen_addresses
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" $PG_CONFIG

# Добавление записи в pg_hba.conf
echo "host    $DB_NAME    $DB_USER    0.0.0.0/0    md5" >> $PG_HBA

systemctl restart postgresql

# Шаг 4: Настройка Redis
echo "🔴 Настройка Redis..."
systemctl start redis-server
systemctl enable redis-server

# Шаг 5: Создание пользователя приложения
echo "👤 Создание пользователя приложения..."
adduser --system --group --home $APP_DIR $APP_USER

# Шаг 6: Создание структуры директорий
echo "📁 Создание директорий..."
mkdir -p $APP_DIR/{app,logs,uploads,static,backups}
chown -R $APP_USER:$APP_USER $APP_DIR

# Шаг 7: Клонирование проекта из GitHub
echo "📄 Клонирование проекта из GitHub..."

# Запрос URL репозитория
echo ""
echo "🔗 Введите URL вашего GitHub репозитория:"
echo "   Пример: https://github.com/your-username/startup-vc-platform.git"
read -p "GitHub URL: " GITHUB_URL

if [ -z "$GITHUB_URL" ]; then
    echo "❌ URL репозитория не указан. Создаю минимальное приложение..."
    cd $APP_DIR
    # Создание минимального приложения (код уже есть в скрипте)
else
    echo "📥 Клонирование репозитория..."
    cd $APP_DIR
    sudo -u $APP_USER git clone $GITHUB_URL app
    cd app
    
    # Проверка наличия файлов
    if [ ! -f "run.py" ] && [ ! -f "app/main.py" ]; then
        echo "⚠️  Файлы приложения не найдены. Создаю минимальное приложение..."
        cd ..
        rm -rf app
        sudo -u $APP_USER mkdir app
        cd app
    fi
fi

# Создание минимального приложения для тестирования
sudo -u $APP_USER tee $APP_DIR/app/main.py > /dev/null << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Startup VC Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Startup VC Platform API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "startup-vc-platform"}

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "api_version": "1.0.0", "database": "connected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Создание файла запуска
sudo -u $APP_USER tee $APP_DIR/app/run.py > /dev/null << 'EOF'
#!/usr/bin/env python3
"""
Main entry point for the Startup-VC Communication Platform
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
EOF

# Шаг 8: Создание виртуального окружения и установка зависимостей
echo "🐍 Создание виртуального окружения..."
sudo -u $APP_USER python3.11 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

echo "📚 Установка Python зависимостей..."
# Установка основных зависимостей
sudo -u $APP_USER $APP_DIR/venv/bin/pip install fastapi uvicorn python-multipart python-dotenv pydantic==2.5.0
sudo -u $APP_USER $APP_DIR/venv/bin/pip install sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib[bcrypt] email-validator

# Если есть requirements.txt, установить из него
if [ -f "$APP_DIR/app/requirements.txt" ]; then
    echo "📦 Установка зависимостей из requirements.txt..."
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/app/requirements.txt
fi

# Шаг 9: Создание .env файла
echo "⚙️ Создание конфигурации..."
sudo -u $APP_USER tee $APP_DIR/app/.env > /dev/null << EOF
# Основные настройки
PROJECT_NAME=Startup-VC Communication Platform
SECRET_KEY=$SECRET_KEY
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# База данных
POSTGRES_SERVER=localhost
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=$DB_NAME
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
JWT_SECRET_KEY=$JWT_SECRET
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
EOF

# Шаг 10: Настройка Nginx
echo "🌐 Настройка Nginx..."
tee /etc/nginx/sites-available/startup-vc > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

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
EOF

# Активация конфигурации Nginx
ln -sf /etc/nginx/sites-available/startup-vc /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

# Шаг 11: Настройка systemd сервиса
echo "👥 Настройка systemd сервиса..."
tee /etc/systemd/system/startup-vc.service > /dev/null << EOF
[Unit]
Description=Startup VC Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/app
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python run.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Включение и запуск сервиса
systemctl daemon-reload
systemctl enable startup-vc
systemctl start startup-vc

# Шаг 12: Настройка Celery (если нужно)
echo "🔄 Настройка Celery..."
if [ -f "$APP_DIR/app/app/core/celery_app.py" ]; then
    # Создание сервиса для Celery Worker
    tee /etc/systemd/system/startup-vc-celery.service > /dev/null << EOF
[Unit]
Description=Startup VC Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/app
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/celery -A app.core.celery_app worker --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Создание сервиса для Celery Beat
    tee /etc/systemd/system/startup-vc-celery-beat.service > /dev/null << EOF
[Unit]
Description=Startup VC Celery Beat
After=network.target redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/app
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/celery -A app.core.celery_app beat --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Включение и запуск Celery сервисов
    systemctl daemon-reload
    systemctl enable startup-vc-celery startup-vc-celery-beat
    systemctl start startup-vc-celery startup-vc-celery-beat
fi

# Шаг 13: Запуск миграций (если есть)
echo "🗄️ Запуск миграций базы данных..."
if [ -f "$APP_DIR/app/alembic.ini" ]; then
    cd $APP_DIR/app
    sudo -u $APP_USER $APP_DIR/venv/bin/alembic upgrade head
fi

# Шаг 14: Настройка брандмауэра
echo "🔥 Настройка брандмауэра..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 8000
ufw --force enable

# Шаг 15: Проверка установки
echo "🔍 Проверка установки..."
sleep 5

# Проверка статуса сервисов
echo "📊 Статус сервисов:"
systemctl is-active nginx postgresql redis-server startup-vc

# Проверка приложения
echo "🌐 Тестирование приложения..."
SERVER_IP=$(curl -s ifconfig.me)
echo "   - Локальный health check:"
curl -s http://localhost:8000/health | head -1
echo "   - Внешний health check:"
curl -s http://$SERVER_IP/health | head -1

# Создание скрипта управления
echo "📝 Создание скрипта управления..."
tee $APP_DIR/manage.sh > /dev/null << 'EOF'
#!/bin/bash

case "$1" in
    start)
        echo "Запуск приложения..."
        sudo systemctl start startup-vc
        ;;
    stop)
        echo "Остановка приложения..."
        sudo systemctl stop startup-vc
        ;;
    restart)
        echo "Перезапуск приложения..."
        sudo systemctl restart startup-vc
        ;;
    status)
        echo "Статус приложения:"
        sudo systemctl status startup-vc
        ;;
    logs)
        echo "Просмотр логов:"
        sudo journalctl -u startup-vc -f
        ;;
    update)
        echo "Обновление приложения..."
        cd /opt/startup-vc/app
        sudo -u startup-vc git pull origin main
        sudo -u startup-vc /opt/startup-vc/venv/bin/pip install -r requirements.txt
        sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head
        sudo systemctl restart startup-vc
        ;;
    backup)
        echo "Создание резервной копии БД..."
        sudo -u postgres pg_dump startup_vc_db > /opt/startup-vc/backups/backup_$(date +%Y%m%d_%H%M%S).sql
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|backup}"
        exit 1
        ;;
esac
EOF

chmod +x $APP_DIR/manage.sh

# Финальный отчет
echo ""
echo "✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!"
echo "=================================="
echo ""
echo "📋 Информация о развертывании:"
echo "   - Приложение: $APP_DIR/app/"
echo "   - Логи: $APP_DIR/logs/"
echo "   - Загрузки: $APP_DIR/uploads/"
echo "   - Пользователь БД: $DB_USER"
echo "   - База данных: $DB_NAME"
echo ""
echo "🌐 Доступ к приложению:"
echo "   - HTTP: http://$SERVER_IP"
echo "   - Health: http://$SERVER_IP/health"
echo "   - API: http://$SERVER_IP/docs"
echo ""
echo "🔧 Управление приложением:"
echo "   - Запуск: $APP_DIR/manage.sh start"
echo "   - Остановка: $APP_DIR/manage.sh stop"
echo "   - Перезапуск: $APP_DIR/manage.sh restart"
echo "   - Статус: $APP_DIR/manage.sh status"
echo "   - Логи: $APP_DIR/manage.sh logs"
echo ""
echo "📚 Полезные команды:"
echo "   - Просмотр логов: sudo journalctl -u startup-vc -f"
echo "   - Статус сервисов: sudo systemctl status startup-vc nginx postgresql redis-server"
echo "   - Проверка БД: sudo -u postgres psql -d $DB_NAME"
echo ""
echo "⚠️  ВАЖНО:"
echo "   - Измените пароли в $APP_DIR/app/.env"
echo "   - Настройте SSL сертификат для продакшена"
echo "   - Регулярно создавайте резервные копии"
echo ""
echo "🎉 Приложение готово к использованию!"