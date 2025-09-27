# 🚀 Startup-VC Communication Platform

Автоматизированная платформа для коммуникации между стартапами и венчурными фондами с использованием ИИ.

## 📋 Оглавление

- [Быстрый старт](#-быстрый-старт)
- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Установка и развертывание](#-установка-и-развертывание)
- [API документация](#-api-документация)
- [Мониторинг](#-мониторинг)
- [Безопасность](#-безопасность)
- [Поддержка](#-поддержка)

## 🚀 Быстрый старт

### Предварительные требования

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- 4GB RAM минимум
- 20GB свободного места

### Быстрая установка

#### Вариант 1: Python (рекомендуется для разработки)

```bash
# Клонируйте репозиторий
git clone https://github.com/your-org/startup-vc-platform.git
cd startup-vc-platform

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Запустите приложение
python run_app.py
```

#### Вариант 2: Docker

```bash
# Клонируйте репозиторий
git clone https://github.com/your-org/startup-vc-platform.git
cd startup-vc-platform

# Скопируйте и настройте переменные окружения
cp .env.example .env
# Отредактируйте .env файл

# Запустите в development режиме
docker-compose up -d

# Или для production
docker-compose -f docker-compose.prod.yml up -d
```

### Первый запуск

1. Откройте браузер и перейдите на `http://localhost:8000`
2. Нажмите "Get Started" или перейдите на `/register`
3. Создайте аккаунт стартапа
4. Войдите в систему через `/login`
5. Настройте профиль стартапа в dashboard
6. Загрузите данные VC фондов (для администраторов)

### Тестирование

```bash
# Запустите тесты аутентификации
python test_auth.py

# Или используйте curl для тестирования API
curl -X POST "http://localhost:8000/api/auth/register" \
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
```

## ✨ Возможности

### 🤖 ИИ-анализ pitch deck
- Автоматический анализ PDF, PPTX, DOCX файлов
- Извлечение ключевых метрик и информации о команде
- Классификация по отраслям и стадиям развития

### 📧 Умная email система
- Персонализированные email шаблоны
- Автоматическая отправка и получение писем
- Классификация ответов от VC фондов
- Follow-up автоматизация

### 🎯 Интеллектуальное сопоставление
- Алгоритм сопоставления стартапов и фондов
- Взвешенная система оценки совместимости
- Исключение дубликатов и недавних обращений

### 🔄 Оркестрация коммуникаций
- Конечный автомат состояний
- Автоматическая эскалация к человеку
- Управление жизненным циклом коммуникаций

### 📊 Мониторинг и аналитика
- Real-time дашборды
- Business метрики и KPI
- Алерты и уведомления
- Детальная аналитика эффективности

## 🏗 Архитектура

### Компоненты системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │    │   Nginx Proxy   │
│                 │    │                 │    │                 │
│ • REST API      │    │ • Email Tasks   │    │ • Load Balancer │
│ • WebSocket     │    │ • AI Analysis   │    │ • SSL/TLS       │
│ • Authentication│    │ • Reporting     │    │ • Rate Limiting │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              Infrastructure                     │
         │                                                 │
         │  PostgreSQL  │  Redis  │  Prometheus  │ Grafana │
         │  • Data      │  • Queue │  • Metrics   │ • Viz   │
         │  • Migrations│  • Cache │  • Alerts    │ • Dash  │
         └─────────────────────────────────────────────────┘
```

### Технологический стек

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery
- **AI/ML**: Claude API, OpenAI API
- **Monitoring**: Prometheus, Grafana, ELK Stack
- **Deployment**: Docker, Docker Compose
- **Reverse Proxy**: Nginx
- **CI/CD**: GitHub Actions

## 🛠 Установка и развертывание

### Development окружение

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env

# Запустите базы данных
docker-compose up -d postgres redis

# Выполните миграции
alembic upgrade head

# Запустите приложение
uvicorn app.main:app --reload

# Запустите Celery worker (в отдельном терминале)
celery -A app.core.celery_app worker --loglevel=info
```

### Production развертывание

#### 1. Подготовка сервера

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установите Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Конфигурация

```bash
# Создайте директории
sudo mkdir -p /opt/startup-vc/{logs,backups,uploads,ssl}

# Скопируйте конфигурационные файлы
sudo cp -r deployment/ /opt/startup-vc/
sudo cp docker-compose.prod.yml /opt/startup-vc/

# Настройте SSL сертификаты
sudo cp your-cert.pem /opt/startup-vc/ssl/cert.pem
sudo cp your-key.pem /opt/startup-vc/ssl/key.pem
sudo chmod 600 /opt/startup-vc/ssl/key.pem
```

#### 3. Переменные окружения

Создайте `.env` файл:

```bash
# Database
POSTGRES_DB=startup_vc_prod
POSTGRES_USER=startup_vc_user
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password

# Application
SECRET_KEY=your_super_secret_key_here
DEBUG=false
ENVIRONMENT=production

# External APIs
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# Email
SMTP_SERVER=smtp.your-provider.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@domain.com
EMAIL_PASSWORD=your_email_password

# Monitoring
GRAFANA_PASSWORD=your_grafana_password

# Backup
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

#### 4. Запуск

```bash
cd /opt/startup-vc
docker-compose -f docker-compose.prod.yml up -d
```

#### 5. Проверка

```bash
# Проверьте статус сервисов
docker-compose -f docker-compose.prod.yml ps

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f app

# Проверьте health check
curl https://your-domain.com/health
```

### Автоматическое развертывание

Используйте скрипт для автоматического развертывания:

```bash
./scripts/deploy.sh production
```

## 📚 API документация

### Автоматическая документация

- **Swagger UI**: `https://your-domain.com/docs`
- **ReDoc**: `https://your-domain.com/redoc`
- **OpenAPI Schema**: `https://your-domain.com/openapi.json`

### Основные endpoints

#### Startup Management
```bash
# Создать стартап
POST /api/startups/
{
  "name": "TechStartup",
  "industry": "Technology",
  "stage": "seed",
  "email": "contact@techstartup.com",
  "contact_person": "John Doe"
}

# Получить информацию о стартапе
GET /api/startups/{id}

# Загрузить pitch deck
POST /api/startups/{id}/pitch-deck
```

#### Communication Management
```bash
# Инициировать outreach
POST /api/startups/{id}/start-outreach
{
  "fund_ids": [1, 2, 3],
  "priority": "high"
}

# Получить коммуникации
GET /api/startups/{id}/communications

# Эскалировать к человеку
POST /api/communications/{id}/escalate
{
  "reason": "Complex negotiation required"
}
```

#### Analytics
```bash
# Получить dashboard данные
GET /api/startups/{id}/dashboard

# Получить аналитику платформы
GET /api/analytics/success-rates
```

### Аутентификация

Все API endpoints требуют аутентификации через JWT токены:

```bash
# Получить токен
POST /api/auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# Использовать токен
Authorization: Bearer <your_jwt_token>
```

## 📊 Мониторинг

### Grafana Dashboards

- **System Overview**: `https://monitoring.your-domain.com/grafana/d/overview`
- **Business Metrics**: `https://monitoring.your-domain.com/grafana/d/business`
- **Infrastructure**: `https://monitoring.your-domain.com/grafana/d/infrastructure`

### Prometheus Metrics

- **Application Metrics**: `https://monitoring.your-domain.com/prometheus`
- **Custom Business Metrics**: `/api/v1/metrics/business`

### Алерты

Система автоматически отправляет алерты при:
- Недоступности сервисов
- Высоком проценте ошибок
- Медленном времени отклика
- Проблемах с базой данных
- Высокой нагрузке на систему

### Логи

Централизованные логи доступны в Kibana:
`https://monitoring.your-domain.com/kibana`

## 🔒 Безопасность

### Рекомендации по безопасности

1. **SSL/TLS**: Всегда используйте HTTPS в production
2. **Пароли**: Используйте сложные пароли для всех сервисов
3. **Секреты**: Храните API ключи в переменных окружения
4. **Обновления**: Регулярно обновляйте зависимости
5. **Бэкапы**: Настройте автоматические бэкапы

### Конфигурация безопасности

```nginx
# Nginx security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=63072000" always;
```

### Аудит безопасности

Выполните проверку безопасности:

```bash
./scripts/security-audit.sh
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Приложение не запускается

```bash
# Проверьте логи
docker-compose logs app

# Проверьте переменные окружения
docker-compose config

# Проверьте подключение к БД
docker-compose exec app python -c "from app.core.database import check_db_connection; print(check_db_connection())"
```

#### 2. Ошибки базы данных

```bash
# Проверьте статус PostgreSQL
docker-compose exec postgres pg_isready

# Выполните миграции
docker-compose exec app alembic upgrade head

# Проверьте подключения
docker-compose exec app python -c "from app.core.database import get_db; print(next(get_db()))"
```

#### 3. Проблемы с Celery

```bash
# Проверьте статус Redis
docker-compose exec redis redis-cli ping

# Проверьте worker'ы
docker-compose exec celery-worker celery -A app.core.celery_app inspect active

# Перезапустите worker'ы
docker-compose restart celery-worker celery-beat
```

#### 4. Проблемы с мониторингом

```bash
# Проверьте Prometheus
curl http://localhost:9090/-/healthy

# Проверьте Grafana
curl http://localhost:3000/api/health

# Проверьте метрики приложения
curl http://localhost:8000/metrics
```

### Логи и диагностика

```bash
# Все логи
docker-compose logs

# Логи конкретного сервиса
docker-compose logs app
docker-compose logs postgres
docker-compose logs redis

# Следить за логами в реальном времени
docker-compose logs -f app
```

### Восстановление из бэкапа

```bash
# Создайте бэкап текущего состояния
./scripts/backup.sh

# Восстановите из бэкапа
./scripts/restore.sh backup_file.sql
```

## 📞 Поддержка

### Получение помощи

1. **Документация**: Проверьте разделы документации
2. **Issues**: Создайте issue в GitHub
3. **Email**: support@startup-vc.com
4. **Discord**: [Join our community](https://discord.gg/startup-vc)

### Сообщение об ошибках

При сообщении об ошибке включите:

```bash
# Системная информация
docker-compose version
docker version

# Логи ошибки
docker-compose logs app | tail -100

# Конфигурация (без секретов)
docker-compose config | grep -v password
```

### Вклад в проект

Мы приветствуем вклад в развитие проекта! См. [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл для деталей.

## 🙏 Благодарности

- FastAPI community за отличный фреймворк
- PostgreSQL и Redis за надежные базы данных
- Prometheus и Grafana за мониторинг
- Все контрибьюторы проекта

---

**Сделано с ❤️ для стартап-сообщества**