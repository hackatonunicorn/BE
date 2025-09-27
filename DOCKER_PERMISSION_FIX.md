# 🔧 Исправление проблемы с правами Docker

## Проблема
```
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

## 🚀 Быстрое решение

### 1. Добавление пользователя в группу docker
```bash
# Войдите в систему как root или с sudo
sudo usermod -aG docker $USER

# Перезагрузите сессию (или выйдите и войдите снова)
newgrp docker

# Проверьте, что пользователь добавлен в группу
groups $USER
```

### 2. Перезапуск Docker сервиса
```bash
sudo systemctl restart docker
```

### 3. Проверка работы
```bash
docker --version
docker ps
```

## 🔍 Альтернативные решения

### Если проблема остается:

#### Вариант 1: Изменение прав на сокет
```bash
sudo chmod 666 /var/run/docker.sock
```

#### Вариант 2: Перезапуск системы
```bash
sudo reboot
```

#### Вариант 3: Проверка статуса Docker
```bash
sudo systemctl status docker
sudo systemctl start docker
sudo systemctl enable docker
```

## 🐳 Развертывание Startup VC Platform

После исправления проблемы с правами Docker, вы можете развернуть приложение:

### Быстрое развертывание
```bash
# Клонирование проекта
git clone https://github.com/your-username/startup-vc-platform.git
cd startup-vc-platform

# Настройка переменных окружения
cp env.example .env
nano .env  # Отредактируйте настройки

# Запуск в режиме разработки
docker-compose up -d

# Или запуск продакшен стека
docker-compose -f docker-compose.prod.yml up -d
```

### Использование скриптов управления
```bash
# Сделать скрипт исполняемым
chmod +x scripts/docker-manage.sh

# Запуск приложения
./scripts/docker-manage.sh start

# Просмотр статуса
./scripts/docker-manage.sh status

# Просмотр логов
./scripts/docker-manage.sh logs
```

## 📋 Проверка развертывания

### 1. Проверка контейнеров
```bash
docker-compose ps
```

### 2. Проверка приложения
```bash
curl http://localhost:8000/health
```

### 3. Проверка внешнего доступа
```bash
curl http://YOUR_SERVER_IP:8000/health
```

## 🛠️ Устранение неполадок

### Если контейнеры не запускаются:
```bash
# Просмотр логов
docker-compose logs

# Пересборка образов
docker-compose build --no-cache

# Перезапуск
docker-compose down
docker-compose up -d
```

### Если порты заняты:
```bash
# Проверка занятых портов
sudo netstat -tulpn | grep :8000

# Остановка конфликтующих сервисов
sudo systemctl stop nginx  # если нужно
```

### Если проблемы с памятью:
```bash
# Очистка Docker
docker system prune -a

# Проверка ресурсов
docker stats
```

## 🎯 Следующие шаги

1. **Настройте SSL** для продакшена
2. **Настройте мониторинг** (Grafana, Prometheus)
3. **Настройте резервное копирование**
4. **Настройте CI/CD** для автоматического развертывания

## 📚 Дополнительные ресурсы

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md) - Полное руководство по развертыванию
- [env.production](./env.production) - Шаблон переменных окружения
