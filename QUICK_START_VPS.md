# Быстрый старт - Развертывание на VPS

## Минимальные требования
- VPS с Ubuntu 22.04+
- 2 GB RAM, 2 CPU, 20 GB SSD
- Домен с A-записью на IP сервера

## Автоматический скрипт установки

Создайте файл `install.sh` на сервере:

```bash
#!/bin/bash

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.11 python3.11-venv python3.11-dev nginx postgresql postgresql-contrib redis-server supervisor certbot python3-certbot-nginx git curl

# Создание пользователя
sudo adduser --system --group --home /opt/startup-vc startup-vc

# Клонирование репозитория (замените на ваш репозиторий)
sudo -u startup-vc git clone https://github.com/your-repo/startup-vc-platform.git /opt/startup-vc/app

# Создание виртуального окружения
sudo -u startup-vc python3.11 -m venv /opt/startup-vc/venv
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install --upgrade pip

# Установка зависимостей
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install fastapi uvicorn python-multipart python-dotenv pydantic==1.10.13
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib[bcrypt] email-validator

# Настройка PostgreSQL
sudo -u postgres createuser startup_vc_user
sudo -u postgres createdb startup_vc_db
sudo -u postgres psql -c "ALTER USER startup_vc_user PASSWORD 'secure_password_123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE startup_vc_db TO startup_vc_user;"

# Создание .env файла
sudo -u startup-vc tee /opt/startup-vc/.env > /dev/null <<EOF
DATABASE_URL=postgresql://startup_vc_user:secure_password_123@localhost:5432/startup_vc_db
JWT_SECRET_KEY=your_super_secret_jwt_key_here_minimum_32_characters_long
DEBUG=False
ENVIRONMENT=production
EOF

# Создание директорий
sudo -u startup-vc mkdir -p /opt/startup-vc/{logs,uploads,static,backups}

# Запуск миграций
cd /opt/startup-vc/app
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head

echo "Установка завершена! Теперь настройте Nginx и SSL."
```

## Быстрая настройка Nginx

```bash
# Создание конфигурации Nginx
sudo tee /etc/nginx/sites-available/startup-vc > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/startup-vc /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## Настройка Supervisor

```bash
# Конфигурация приложения
sudo tee /etc/supervisor/conf.d/startup-vc.conf > /dev/null <<EOF
[program:startup-vc]
command=/opt/startup-vc/venv/bin/uvicorn minimal_app:app --host 127.0.0.1 --port 8000 --workers 2
directory=/opt/startup-vc/app
user=startup-vc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/startup-vc/logs/app.log
environment=PATH="/opt/startup-vc/venv/bin"
EOF

# Перезапуск Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start startup-vc
```

## Получение SSL сертификата

```bash
# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление сертификата
sudo crontab -e
# Добавьте: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Проверка работы

```bash
# Проверка статуса
sudo supervisorctl status
sudo systemctl status nginx postgresql redis-server

# Проверка приложения
curl http://localhost:8000/health
curl https://your-domain.com/health
```

## Команды управления

```bash
# Перезапуск приложения
sudo supervisorctl restart startup-vc

# Просмотр логов
sudo tail -f /opt/startup-vc/logs/app.log

# Обновление приложения
cd /opt/startup-vc/app
sudo -u startup-vc git pull
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head
sudo supervisorctl restart startup-vc
```

## Важные замечания

1. **Замените пароли**: Обязательно измените все пароли в .env файле
2. **Настройте домен**: Убедитесь, что домен указывает на IP вашего сервера
3. **Безопасность**: Настройте firewall и SSH ключи
4. **Резервное копирование**: Настройте автоматическое резервное копирование

## Структура файлов на сервере

```
/opt/startup-vc/
├── app/                 # Код приложения
├── venv/               # Виртуальное окружение
├── logs/               # Логи приложения
├── uploads/            # Загруженные файлы
├── static/             # Статические файлы
├── backups/            # Резервные копии
└── .env               # Переменные окружения
```

## Доступные эндпоинты

- `https://your-domain.com/` - Главная страница
- `https://your-domain.com/docs` - API документация
- `https://your-domain.com/health` - Health check
- `https://your-domain.com/api/auth/register` - Регистрация
- `https://your-domain.com/api/auth/login` - Вход
- `https://your-domain.com/api/campaigns/` - Управление кампаниями

## Мониторинг

```bash
# Использование ресурсов
htop

# Статус сервисов
sudo systemctl status nginx postgresql redis-server supervisor

# Проверка портов
sudo netstat -tlnp | grep :8000
```

---

**Время развертывания**: ~30 минут  
**Сложность**: Средняя  
**Поддержка**: Ubuntu 22.04+
