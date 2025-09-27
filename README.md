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
- **Systemd** - управление сервисами
- **Nginx** - reverse proxy
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и очереди

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/startup-vc-platform.git
cd startup-vc-platform

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env .env.local
# Отредактируйте .env.local файл

# Запуск приложения
python run.py
```

### Развертывание на VPS

```bash
# Пошаговое развертывание
# Следуйте инструкциям в DEPLOYMENT_GUIDE.md

# Или используйте автоматический скрипт
sudo bash install_vps.sh
```

## 📚 Документация

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Полное руководство по развертыванию
- **[install_vps.sh](./install_vps.sh)** - Автоматический скрипт установки

## 🔧 Управление

### Systemd команды
```bash
# Управление основным приложением
sudo systemctl start startup-vc      # Запуск
sudo systemctl stop startup-vc        # Остановка
sudo systemctl restart startup-vc     # Перезапуск
sudo systemctl status startup-vc      # Статус

# Управление фоновыми задачами
sudo systemctl start startup-vc-celery startup-vc-celery-beat
sudo systemctl stop startup-vc-celery startup-vc-celery-beat

# Просмотр логов
sudo journalctl -u startup-vc -f
```

### Основные команды
```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск приложения
python run.py

# Запуск с Gunicorn (продакшен)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Миграции БД
alembic upgrade head

# Запуск Celery worker
celery -A app.core.celery_app worker --loglevel=info
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
- **API документация**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Системный мониторинг
```bash
# Проверка статуса сервисов
sudo systemctl status startup-vc startup-vc-celery startup-vc-celery-beat

# Просмотр логов
sudo journalctl -u startup-vc -f

# Мониторинг ресурсов
htop
df -h
free -h
```

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