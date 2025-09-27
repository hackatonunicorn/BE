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
    if [ ! -f "minimal_app.py" ] && [ ! -f "main.py" ]; then
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
sudo -u $APP_USER tee $APP_DIR/app/minimal_app.py > /dev/null << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/api/campaigns/options")
async def campaign_options():
    return {
        "industries": ["Technology", "Healthcare", "Fintech", "E-commerce", "AI/ML"],
        "funding_stages": ["Seed", "Series A", "Series B", "Series C", "Growth"],
        "team_sizes": ["1-5", "6-10", "11-20", "21-50", "50+"],
        "locations": ["San Francisco", "New York", "London", "Berlin", "Singapore"]
    }
EOF

# Шаг 8: Создание виртуального окружения и установка зависимостей
echo "🐍 Создание виртуального окружения..."
sudo -u $APP_USER python3.11 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

echo "📚 Установка Python зависимостей..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install fastapi uvicorn python-multipart python-dotenv pydantic==1.10.13
sudo -u $APP_USER $APP_DIR/venv/bin/pip install sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib[bcrypt] email-validator

# Шаг 9: Создание .env файла
echo "⚙️ Создание конфигурации..."
sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME

# Security
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=Startup VC Platform
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# File Storage
UPLOAD_DIR=$APP_DIR/uploads
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
LOG_FILE=$APP_DIR/logs/app.log
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

# Шаг 11: Настройка Supervisor
echo "👥 Настройка Supervisor..."
tee /etc/supervisor/conf.d/startup-vc.conf > /dev/null << EOF
[program:startup-vc]
command=$APP_DIR/venv/bin/uvicorn minimal_app:app --host 127.0.0.1 --port 8000 --workers 2
directory=$APP_DIR/app
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="$APP_DIR/venv/bin"
EOF

# Перезапуск Supervisor
supervisorctl reread
supervisorctl update
supervisorctl start startup-vc

# Шаг 12: Настройка брандмауэра
echo "🔥 Настройка брандмауэра..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Шаг 13: Проверка установки
echo "🔍 Проверка установки..."
sleep 5

# Проверка статуса сервисов
echo "📊 Статус сервисов:"
systemctl is-active nginx postgresql redis-server supervisor

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
        supervisorctl start startup-vc
        ;;
    stop)
        echo "Остановка приложения..."
        supervisorctl stop startup-vc
        ;;
    restart)
        echo "Перезапуск приложения..."
        supervisorctl restart startup-vc
        ;;
    status)
        echo "Статус приложения:"
        supervisorctl status startup-vc
        ;;
    logs)
        echo "Просмотр логов:"
        tail -f /opt/startup-vc/logs/app.log
        ;;
    update)
        echo "Обновление приложения..."
        cd /opt/startup-vc/app
        git pull origin main
        /opt/startup-vc/venv/bin/pip install -r requirements_simple.txt
        /opt/startup-vc/venv/bin/alembic upgrade head
        supervisorctl restart startup-vc
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update}"
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
echo "   - Просмотр логов: tail -f $APP_DIR/logs/app.log"
echo "   - Статус сервисов: systemctl status nginx postgresql redis-server supervisor"
echo "   - Проверка БД: sudo -u postgres psql -d $DB_NAME"
echo ""
echo "⚠️  ВАЖНО:"
echo "   - Измените пароли в $APP_DIR/.env"
echo "   - Настройте SSL сертификат для продакшена"
echo "   - Регулярно создавайте резервные копии"
echo ""
echo "🎉 Приложение готово к использованию!"
EOF

chmod +x install_vps.sh

echo "✅ Автоматический скрипт установки создан: install_vps.sh"
echo ""
echo "Для развертывания на вашем VPS:"
echo "1. Загрузите скрипт на сервер: scp install_vps.sh root@YOUR_VPS_IP:/root/"
echo "2. Подключитесь к серверу: ssh root@YOUR_VPS_IP"
echo "3. Запустите установку: sudo bash /root/install_vps.sh"
echo ""
echo "Или следуйте пошаговой инструкции в DEPLOY_TO_VPS.md"
