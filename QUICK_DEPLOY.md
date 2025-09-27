# Быстрое развертывание на VPS

## Вариант 1: Автоматическая установка (рекомендуется)

### 1. Загрузите скрипт на сервер
```bash
# На вашем локальном компьютере
scp install_vps.sh root@YOUR_VPS_IP:/root/
```

### 2. Подключитесь к серверу и запустите установку
```bash
ssh root@YOUR_VPS_IP
sudo bash /root/install_vps.sh
```

### 3. Дождитесь завершения (5-10 минут)
Скрипт автоматически:
- Установит все зависимости
- Настроит PostgreSQL и Redis
- Развернет приложение
- Настроит Nginx
- Запустит все сервисы

### 4. Проверьте работу
```bash
# Получите IP сервера
curl ifconfig.me

# Проверьте приложение
curl http://YOUR_VPS_IP/health
```

## Вариант 2: Пошаговая установка

Следуйте подробной инструкции в файле `DEPLOY_TO_VPS.md`

## После установки

### Доступ к приложению:
- **HTTP**: `http://YOUR_VPS_IP`
- **API документация**: `http://YOUR_VPS_IP/docs`
- **Health check**: `http://YOUR_VPS_IP/health`

### Управление приложением:
```bash
# На сервере
cd /opt/startup-vc
./manage.sh start      # Запуск
./manage.sh stop       # Остановка
./manage.sh restart    # Перезапуск
./manage.sh status     # Статус
./manage.sh logs       # Логи
```

### Тестирование API:
```bash
# Health check
curl http://YOUR_VPS_IP/health

# Регистрация пользователя
curl -X POST "http://YOUR_VPS_IP/api/auth/register" \
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

## Важные замечания

1. **Безопасность**: После установки измените пароли в `/opt/startup-vc/.env`
2. **SSL**: Для продакшена настройте SSL сертификат
3. **Домен**: Привяжите домен к IP сервера для удобства
4. **Резервные копии**: Настройте автоматическое резервное копирование

## Время развертывания
- **Автоматическая установка**: 5-10 минут
- **Пошаговая установка**: 30-45 минут

## Поддержка
Если возникнут проблемы, проверьте:
1. Логи приложения: `/opt/startup-vc/logs/app.log`
2. Статус сервисов: `systemctl status nginx postgresql redis-server supervisor`
3. Конфигурацию Nginx: `nginx -t`
