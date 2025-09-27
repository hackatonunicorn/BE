# 🚀 Startup-VC Communication Platform

Полнофункциональная платформа для автоматизации коммуникации между стартапами и венчурными фондами.

## ✨ Основные возможности

- **🤖 AI-анализ** питч-деков и автоматическая генерация персонализированных писем
- **📧 Email-автоматизация** с шаблонами и A/B тестированием
- **🎯 Умное сопоставление** стартапов с подходящими VC фондами
- **📊 Аналитика** и отчетность по кампаниям
- **🔐 Безопасность** с JWT аутентификацией и ролевой моделью
- **📱 REST API** с полной документацией

## 🏗️ Архитектура

### Backend
- **FastAPI** - современный веб-фреймворк
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и очереди
- **Celery** - фоновые задачи
- **SQLAlchemy** - ORM
- **Alembic** - миграции БД

### AI/ML
- **OpenAI GPT-4** - анализ текста и генерация контента
- **LangChain** - обработка документов
- **Custom ML** - классификация ответов

### Инфраструктура
- **Docker** - контейнеризация
- **Nginx** - reverse proxy
- **Prometheus + Grafana** - мониторинг
- **Elasticsearch + Kibana** - логи

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/startup-vc-platform.git
cd startup-vc-platform

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env.example .env
# Отредактируйте .env файл

# Запуск с Docker
docker-compose up -d

# Или запуск напрямую
python run.py
```

### Развертывание на VPS

```bash
# Быстрое развертывание
sudo bash scripts/quick-deploy.sh

# Или пошаговое развертывание
# Следуйте инструкциям в DEPLOY_TO_VPS.md
```

## 📚 Документация

- **[DEPLOY_TO_VPS.md](./DEPLOY_TO_VPS.md)** - Подробное руководство по развертыванию
- **[DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md)** - Развертывание с Docker
- **[PROJECT_STATUS_REPORT.md](./PROJECT_STATUS_REPORT.md)** - Статус проекта
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Решение проблем

## 🔧 Управление

### Docker команды
```bash
# Управление через скрипт
./scripts/docker-manage.sh start      # Запуск
./scripts/docker-manage.sh stop       # Остановка
./scripts/docker-manage.sh logs       # Логи
./scripts/docker-manage.sh backup     # Резервная копия
```

### Основные команды
```bash
# Запуск разработки
docker-compose up -d

# Запуск продакшена
docker-compose -f docker-compose.prod.yml up -d

# Миграции БД
docker-compose exec web alembic upgrade head

# Просмотр логов
docker-compose logs -f
```

## 🌐 API Endpoints

### Основные
- `GET /` - Главная страница
- `GET /health` - Проверка здоровья
- `GET /docs` - Swagger документация

### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/refresh` - Обновление токена

### Стартапы
- `GET /api/v1/startups/` - Список стартапов
- `POST /api/v1/startups/` - Создание стартапа
- `GET /api/v1/startups/{id}` - Детали стартапа

### VC Фонды
- `GET /api/v1/vc-funds/` - Список фондов
- `POST /api/v1/vc-funds/` - Создание фонда

### Кампании
- `GET /api/v1/campaigns/` - Список кампаний
- `POST /api/v1/campaigns/` - Создание кампании
- `POST /api/v1/campaigns/{id}/launch` - Запуск кампании

## 🔐 Безопасность

- **JWT токены** с refresh механизмом
- **Bcrypt** хеширование паролей
- **CORS** настройки
- **Rate limiting** защита от спама
- **Валидация** всех входных данных

## 📊 Мониторинг

### Доступные интерфейсы
- **Приложение**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

## 🛠️ Разработка

### Структура проекта
```
app/
├── api/           # API endpoints
├── core/          # Основная логика
├── data/          # Модели и репозитории
├── ai/            # AI модули
├── email/         # Email система
└── integrations/ # Внешние интеграции
```

### Добавление новых функций
1. Создайте модель в `app/data/models.py`
2. Добавьте репозиторий в `app/data/repositories/`
3. Создайте API endpoint в `app/api/`
4. Добавьте миграцию: `alembic revision --autogenerate`

## 📈 Производительность

- **Асинхронная** обработка запросов
- **Кэширование** с Redis
- **Фоновые задачи** с Celery
- **Оптимизированные** SQL запросы
- **Масштабируемая** архитектура

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE

## 🆘 Поддержка

- **Документация**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Issues**: GitHub Issues
- **Email**: support@startup-vc-platform.com

---

**Статус**: ✅ Готов к продакшену  
**Версия**: 1.0.0  
**Последнее обновление**: 2024