# 🐳 Руководство по развертыванию Startup VC Platform с Docker

## 📋 Предварительные требования

- Ubuntu 20.04+ или аналогичная Linux система
- Минимум 4GB RAM, 2 CPU cores
- 20GB свободного места на диске
- Docker и Docker Compose установлены

## 🚀 Быстрая установка

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Установка дополнительных инструментов
sudo apt install -y git curl wget htop
```

### Шаг 2: Клонирование проекта

```bash
# Создание директории проекта
sudo mkdir -p /opt/startup-vc
cd /opt/startup-vc

# Клонирование репозитория (замените на ваш URL)
git clone https://github.com/your-username/startup-vc-platform.git .

# Или загрузка архива
# wget https://github.com/your-username/startup-vc-platform/archive/main.tar.gz
# tar -xzf main.tar.gz --strip-components=1
```

### Шаг 3: Настройка переменных окружения

```bash
# Копирование шаблона
cp env.example .env

# Редактирование конфигурации
nano .env
```

### Шаг 4: Запуск в режиме разработки

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### Шаг 5: Запуск в продакшене

```bash
# Запуск продакшен стека
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps
```

## 🔧 Конфигурация

### Переменные окружения (.env)

```env
# Основные настройки
PROJECT_NAME=Startup-VC Communication Platform
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=startup_vc_platform
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=redis_password_123

# Email настройки
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@yourplatform.com
EMAILS_FROM_NAME=Startup-VC Platform

# AI настройки
OPENAI_API_KEY=your-openai-api-key

# Безопасность
ACCESS_TOKEN_EXPIRE_MINUTES=11520
JWT_SECRET_KEY=your-jwt-secret-key-here

# Мониторинг
GRAFANA_PASSWORD=admin123

# Резервное копирование
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

## 🏗️ Архитектура контейнеров

### Разработка (docker-compose.yml)

- **web** - FastAPI приложение
- **db** - PostgreSQL база данных
- **redis** - Redis кэш
- **celery** - Celery worker
- **celery-beat** - Celery scheduler

### Продакшен (docker-compose.prod.yml)

- **app** - FastAPI приложение с оптимизациями
- **celery-worker** - Celery worker с ресурсными ограничениями
- **celery-beat** - Celery scheduler
- **celery-flower** - Мониторинг Celery
- **postgres** - PostgreSQL с health checks
- **redis** - Redis с паролем
- **nginx** - Reverse proxy
- **prometheus** - Мониторинг метрик
- **grafana** - Дашборды мониторинга
- **elasticsearch** - Поиск и логи
- **kibana** - Визуализация логов
- **filebeat** - Сбор логов
- **backup** - Автоматическое резервное копирование

## 🚀 Команды управления

### Основные команды

```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка всех сервисов
docker-compose down

# Перезапуск сервисов
docker-compose restart

# Просмотр логов
docker-compose logs -f [service_name]

# Выполнение команд в контейнере
docker-compose exec web bash
docker-compose exec db psql -U postgres -d startup_vc_platform

# Обновление образов
docker-compose pull
docker-compose up -d
```

### Миграции базы данных

```bash
# Запуск миграций
docker-compose exec web alembic upgrade head

# Создание новой миграции
docker-compose exec web alembic revision --autogenerate -m "Description"
```

### Резервное копирование

```bash
# Создание резервной копии БД
docker-compose exec db pg_dump -U postgres startup_vc_platform > backup.sql

# Восстановление из резервной копии
docker-compose exec -T db psql -U postgres startup_vc_platform < backup.sql
```

## 📊 Мониторинг

### Доступные интерфейсы

- **Приложение**: http://your-server-ip
- **API документация**: http://your-server-ip/docs
- **Grafana**: http://your-server-ip:3000 (admin/admin123)
- **Prometheus**: http://your-server-ip:9090
- **Kibana**: http://your-server-ip:5601
- **Celery Flower**: http://your-server-ip:5555

### Health Checks

```bash
# Проверка здоровья приложения
curl http://your-server-ip/health

# Проверка API
curl http://your-server-ip/api/health

# Проверка статуса контейнеров
docker-compose ps
```

## 🔒 Безопасность

### Настройка SSL

```bash
# Установка Certbot
sudo apt install -y certbot

# Получение SSL сертификата
sudo certbot certonly --standalone -d your-domain.com

# Настройка автоматического обновления
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Настройка брандмауэра

```bash
# Разрешение необходимых портов
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 🛠️ Устранение неполадок

### Проблемы с Docker

```bash
# Очистка Docker
docker system prune -a
docker volume prune

# Пересборка образов
docker-compose build --no-cache
```

### Проблемы с базой данных

```bash
# Проверка подключения к БД
docker-compose exec web python -c "from app.core.database import engine; print('DB connected')"

# Сброс БД
docker-compose down -v
docker-compose up -d
```

### Проблемы с памятью

```bash
# Мониторинг использования ресурсов
docker stats

# Ограничение ресурсов в docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Увеличение количества worker'ов
docker-compose up -d --scale celery-worker=3

# Load balancing с Nginx
# Настройка в nginx.conf
upstream app {
    server app:8000;
    server app2:8000;
    server app3:8000;
}
```

### Вертикальное масштабирование

```yaml
# В docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/startup-vc
            git pull origin main
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d --build
```

## 📝 Полезные команды

### Управление логами

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f web

# Ограничение количества строк
docker-compose logs --tail=100 web
```

### Отладка

```bash
# Подключение к контейнеру
docker-compose exec web bash

# Проверка переменных окружения
docker-compose exec web env

# Проверка сетевых подключений
docker-compose exec web netstat -tulpn
```

### Обновление

```bash
# Обновление кода
git pull origin main

# Пересборка и перезапуск
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Применение миграций
docker-compose exec web alembic upgrade head
```

## 🎯 Заключение

Этот Docker-based подход обеспечивает:

- ✅ **Изоляцию** - каждый сервис в отдельном контейнере
- ✅ **Масштабируемость** - легко добавлять новые инстансы
- ✅ **Портативность** - работает на любой системе с Docker
- ✅ **Мониторинг** - полный стек наблюдения
- ✅ **Безопасность** - изоляция и ограничения ресурсов
- ✅ **Автоматизация** - простые команды для управления

**Время развертывания**: 10-15 минут  
**Сложность**: Низкая  
**Результат**: Полностью работающая платформа с мониторингом
