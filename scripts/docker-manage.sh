#!/bin/bash

# ===========================================
# Startup VC Platform - Docker Management Script
# ===========================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
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

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
        exit 1
    fi
}

# Проверка файла .env
check_env() {
    if [ ! -f ".env" ]; then
        print_warning "Файл .env не найден. Создаю из шаблона..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_success "Файл .env создан из env.example"
            print_warning "Пожалуйста, отредактируйте .env файл перед запуском!"
            exit 1
        else
            print_error "Файл env.example не найден. Создайте .env файл вручную."
            exit 1
        fi
    fi
}

# Функция показа помощи
show_help() {
    echo "🐳 Startup VC Platform - Docker Management"
    echo "=========================================="
    echo ""
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  start       - Запуск всех сервисов (разработка)"
    echo "  start-prod  - Запуск продакшен стека"
    echo "  stop        - Остановка всех сервисов"
    echo "  restart     - Перезапуск всех сервисов"
    echo "  restart-prod - Перезапуск продакшен стека"
    echo "  status      - Показать статус контейнеров"
    echo "  logs        - Показать логи всех сервисов"
    echo "  logs [service] - Показать логи конкретного сервиса"
    echo "  shell [service] - Подключиться к контейнеру"
    echo "  build       - Пересобрать образы"
    echo "  build-prod  - Пересобрать продакшен образы"
    echo "  update      - Обновить и перезапустить"
    echo "  backup      - Создать резервную копию БД"
    echo "  restore     - Восстановить БД из резервной копии"
    echo "  clean       - Очистить неиспользуемые ресурсы"
    echo "  migrate     - Запустить миграции БД"
    echo "  health      - Проверить здоровье сервисов"
    echo "  monitor     - Показать мониторинг ресурсов"
    echo "  help        - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start"
    echo "  $0 logs web"
    echo "  $0 shell db"
    echo "  $0 backup"
}

# Запуск разработки
start_dev() {
    print_message "Запуск сервисов для разработки..."
    docker-compose up -d
    print_success "Сервисы запущены!"
    print_message "Приложение доступно по адресу: http://localhost:8000"
    print_message "API документация: http://localhost:8000/docs"
}

# Запуск продакшена
start_prod() {
    print_message "Запуск продакшен стека..."
    docker-compose -f docker-compose.prod.yml up -d
    print_success "Продакшен стек запущен!"
    print_message "Приложение доступно по адресу: http://localhost"
    print_message "Grafana: http://localhost:3000 (admin/admin123)"
    print_message "Prometheus: http://localhost:9090"
    print_message "Kibana: http://localhost:5601"
}

# Остановка сервисов
stop_services() {
    print_message "Остановка сервисов..."
    docker-compose down
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "Сервисы остановлены!"
}

# Перезапуск сервисов
restart_services() {
    print_message "Перезапуск сервисов..."
    docker-compose restart
    print_success "Сервисы перезапущены!"
}

# Перезапуск продакшена
restart_prod() {
    print_message "Перезапуск продакшен стека..."
    docker-compose -f docker-compose.prod.yml restart
    print_success "Продакшен стек перезапущен!"
}

# Показать статус
show_status() {
    print_message "Статус контейнеров:"
    echo ""
    docker-compose ps
    echo ""
    print_message "Статус продакшен контейнеров:"
    docker-compose -f docker-compose.prod.yml ps 2>/dev/null || print_warning "Продакшен стек не запущен"
}

# Показать логи
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        print_message "Логи всех сервисов:"
        docker-compose logs -f
    else
        print_message "Логи сервиса $service:"
        docker-compose logs -f "$service"
    fi
}

# Подключиться к контейнеру
shell_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "Укажите имя сервиса для подключения"
        echo "Доступные сервисы:"
        docker-compose ps --services
        exit 1
    fi
    
    print_message "Подключение к контейнеру $service..."
    docker-compose exec "$service" bash
}

# Пересобрать образы
build_images() {
    print_message "Пересборка образов..."
    docker-compose build --no-cache
    print_success "Образы пересобраны!"
}

# Пересобрать продакшен образы
build_prod_images() {
    print_message "Пересборка продакшен образов..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    print_success "Продакшен образы пересобраны!"
}

# Обновить и перезапустить
update_services() {
    print_message "Обновление сервисов..."
    
    # Остановка сервисов
    docker-compose down
    
    # Обновление образов
    docker-compose pull
    
    # Перезапуск
    docker-compose up -d
    
    # Запуск миграций
    print_message "Запуск миграций БД..."
    docker-compose exec web alembic upgrade head
    
    print_success "Сервисы обновлены и перезапущены!"
}

# Резервное копирование
backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_message "Создание резервной копии БД..."
    
    docker-compose exec -T db pg_dump -U postgres startup_vc_platform > "$backup_file"
    
    if [ $? -eq 0 ]; then
        print_success "Резервная копия создана: $backup_file"
    else
        print_error "Ошибка при создании резервной копии"
        exit 1
    fi
}

# Восстановление БД
restore_database() {
    local backup_file=$1
    if [ -z "$backup_file" ]; then
        print_error "Укажите файл резервной копии"
        echo "Использование: $0 restore backup_file.sql"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Файл резервной копии не найден: $backup_file"
        exit 1
    fi
    
    print_warning "Восстановление БД из файла: $backup_file"
    read -p "Это действие перезапишет текущую БД. Продолжить? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec -T db psql -U postgres -d startup_vc_platform < "$backup_file"
        print_success "БД восстановлена из резервной копии!"
    else
        print_message "Восстановление отменено"
    fi
}

# Очистка ресурсов
clean_resources() {
    print_message "Очистка неиспользуемых ресурсов..."
    
    # Остановка всех контейнеров
    docker-compose down
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Удаление неиспользуемых образов
    docker image prune -f
    
    # Удаление неиспользуемых томов
    docker volume prune -f
    
    # Удаление неиспользуемых сетей
    docker network prune -f
    
    print_success "Очистка завершена!"
}

# Запуск миграций
run_migrations() {
    print_message "Запуск миграций БД..."
    docker-compose exec web alembic upgrade head
    print_success "Миграции выполнены!"
}

# Проверка здоровья
check_health() {
    print_message "Проверка здоровья сервисов..."
    
    # Проверка приложения
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "✅ Приложение работает"
    else
        print_error "❌ Приложение недоступно"
    fi
    
    # Проверка БД
    if docker-compose exec db pg_isready -U postgres >/dev/null 2>&1; then
        print_success "✅ База данных работает"
    else
        print_error "❌ База данных недоступна"
    fi
    
    # Проверка Redis
    if docker-compose exec redis redis-cli ping >/dev/null 2>&1; then
        print_success "✅ Redis работает"
    else
        print_error "❌ Redis недоступен"
    fi
}

# Мониторинг ресурсов
show_monitor() {
    print_message "Мониторинг ресурсов:"
    echo ""
    docker stats --no-stream
}

# Основная логика
main() {
    check_docker
    check_env
    
    case "${1:-help}" in
        start)
            start_dev
            ;;
        start-prod)
            start_prod
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        restart-prod)
            restart_prod
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        shell)
            shell_service "$2"
            ;;
        build)
            build_images
            ;;
        build-prod)
            build_prod_images
            ;;
        update)
            update_services
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$2"
            ;;
        clean)
            clean_resources
            ;;
        migrate)
            run_migrations
            ;;
        health)
            check_health
            ;;
        monitor)
            show_monitor
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Запуск скрипта
main "$@"
