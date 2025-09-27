#!/bin/bash

# ===========================================
# Startup VC Platform - Quick VPS Deployment
# ===========================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Пожалуйста, запустите скрипт с правами root: sudo bash quick-deploy.sh"
        exit 1
    fi
}

# Установка Docker
install_docker() {
    print_message "Установка Docker..."
    
    # Обновление пакетов
    apt update
    
    # Установка зависимостей
    apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Добавление GPG ключа Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавление репозитория Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Обновление пакетов и установка Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Запуск и включение Docker
    systemctl start docker
    systemctl enable docker
    
    # Установка Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker установлен!"
}

# Настройка пользователя
setup_user() {
    print_message "Настройка пользователя для Docker..."
    
    # Добавление пользователя в группу docker
    usermod -aG docker $SUDO_USER
    
    print_success "Пользователь настроен!"
}

# Создание директории проекта
setup_project() {
    local project_dir="/opt/startup-vc"
    
    print_message "Создание директории проекта..."
    
    # Создание директории
    mkdir -p "$project_dir"
    cd "$project_dir"
    
    # Создание структуры директорий
    mkdir -p {logs,uploads,backups,scripts}
    
    print_success "Директория проекта создана: $project_dir"
}

# Клонирование проекта
clone_project() {
    print_message "Клонирование проекта..."
    
    # Запрос URL репозитория
    echo ""
    echo "🔗 Введите URL вашего GitHub репозитория:"
    echo "   Пример: https://github.com/your-username/startup-vc-platform.git"
    read -p "GitHub URL: " GITHUB_URL
    
    if [ -n "$GITHUB_URL" ]; then
        git clone "$GITHUB_URL" .
        print_success "Проект клонирован!"
    else
        print_warning "URL не указан. Создаю минимальную структуру..."
        create_minimal_structure
    fi
}

# Создание минимальной структуры
create_minimal_structure() {
    print_message "Создание минимальной структуры проекта..."
    
    # Создание основных файлов
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/startup_vc_platform
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=startup_vc_platform
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
EOF

    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
python-dotenv==1.0.0
EOF

    cat > main.py << 'EOF'
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
    return {"status": "healthy", "api_version": "1.0.0"}
EOF

    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/startup_vc_platform

# Redis
REDIS_URL=redis://redis:6379/0

# Application
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=false
ENVIRONMENT=production
EOF

    print_success "Минимальная структура создана!"
}

# Настройка брандмауэра
setup_firewall() {
    print_message "Настройка брандмауэра..."
    
    # Установка UFW если не установлен
    apt install -y ufw
    
    # Настройка правил
    ufw allow ssh
    ufw allow 80
    ufw allow 443
    ufw allow 8000
    ufw --force enable
    
    print_success "Брандмауэр настроен!"
}

# Запуск приложения
start_application() {
    print_message "Запуск приложения..."
    
    # Запуск контейнеров
    docker-compose up -d
    
    # Ожидание запуска
    sleep 10
    
    # Проверка статуса
    if docker-compose ps | grep -q "Up"; then
        print_success "Приложение запущено!"
    else
        print_error "Ошибка при запуске приложения"
        docker-compose logs
        exit 1
    fi
}

# Проверка работы
check_application() {
    print_message "Проверка работы приложения..."
    
    # Получение IP сервера
    SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
    
    # Проверка локального доступа
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "✅ Локальный доступ работает"
    else
        print_warning "⚠️ Локальный доступ недоступен"
    fi
    
    # Проверка внешнего доступа
    if curl -f http://$SERVER_IP:8000/health >/dev/null 2>&1; then
        print_success "✅ Внешний доступ работает"
    else
        print_warning "⚠️ Внешний доступ недоступен (возможно, брандмауэр)"
    fi
    
    echo ""
    print_message "🌐 Доступ к приложению:"
    echo "   - Локально: http://localhost:8000"
    echo "   - Внешне: http://$SERVER_IP:8000"
    echo "   - Health: http://$SERVER_IP:8000/health"
    echo "   - API Docs: http://$SERVER_IP:8000/docs"
}

# Создание скрипта управления
create_management_script() {
    print_message "Создание скрипта управления..."
    
    cat > manage.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        echo "Запуск приложения..."
        docker-compose up -d
        ;;
    stop)
        echo "Остановка приложения..."
        docker-compose down
        ;;
    restart)
        echo "Перезапуск приложения..."
        docker-compose restart
        ;;
    status)
        echo "Статус приложения:"
        docker-compose ps
        ;;
    logs)
        echo "Просмотр логов:"
        docker-compose logs -f
        ;;
    update)
        echo "Обновление приложения..."
        git pull origin main
        docker-compose down
        docker-compose up -d --build
        ;;
    backup)
        echo "Создание резервной копии БД..."
        docker-compose exec -T db pg_dump -U postgres startup_vc_platform > backup_$(date +%Y%m%d_%H%M%S).sql
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|backup}"
        exit 1
        ;;
esac
EOF

    chmod +x manage.sh
    
    print_success "Скрипт управления создан: ./manage.sh"
}

# Основная функция
main() {
    echo "🚀 Startup VC Platform - Быстрое развертывание на VPS"
    echo "======================================================"
    echo ""
    
    check_root
    install_docker
    setup_user
    setup_project
    clone_project
    setup_firewall
    start_application
    check_application
    create_management_script
    
    echo ""
    print_success "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
    echo "=================================="
    echo ""
    print_message "📋 Информация о развертывании:"
    echo "   - Директория проекта: /opt/startup-vc"
    echo "   - Управление: ./manage.sh [команда]"
    echo ""
    print_message "🔧 Полезные команды:"
    echo "   - Статус: ./manage.sh status"
    echo "   - Логи: ./manage.sh logs"
    echo "   - Перезапуск: ./manage.sh restart"
    echo "   - Обновление: ./manage.sh update"
    echo "   - Резервная копия: ./manage.sh backup"
    echo ""
    print_warning "⚠️ ВАЖНО:"
    echo "   - Измените пароли в .env файле"
    echo "   - Настройте SSL сертификат"
    echo "   - Регулярно создавайте резервные копии"
    echo ""
    print_success "Приложение готово к использованию!"
}

# Запуск скрипта
main "$@"
