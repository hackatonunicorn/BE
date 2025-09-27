# Развертывание через GitHub

## Быстрый старт

### 1. Подготовка GitHub репозитория

```bash
# На вашем локальном компьютере
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/startup-vc-platform.git
git push -u origin main
```

### 2. Развертывание на VPS

```bash
# Подключитесь к серверу
ssh root@YOUR_VPS_IP

# Запустите автоматическую установку
sudo bash install_vps.sh

# При запросе введите URL вашего GitHub репозитория:
# https://github.com/YOUR_USERNAME/startup-vc-platform.git
```

### 3. Проверка работы

```bash
# Проверьте статус
curl http://YOUR_VPS_IP/health

# Управление приложением
cd /opt/startup-vc
./manage.sh status
```

## Обновление приложения

### Способ 1: Через скрипт управления
```bash
cd /opt/startup-vc
./manage.sh update
```

### Способ 2: Вручную
```bash
cd /opt/startup-vc/app
sudo -u startup-vc git pull origin main
sudo -u startup-vc /opt/startup-vc/venv/bin/pip install -r requirements_simple.txt
sudo -u startup-vc /opt/startup-vc/venv/bin/alembic upgrade head
sudo supervisorctl restart startup-vc
```

## Преимущества GitHub развертывания

✅ **Автоматические обновления** - просто `git pull`  
✅ **Версионность** - можно откатиться к предыдущей версии  
✅ **Коллаборация** - команда может работать над проектом  
✅ **Резервное копирование** - код хранится в облаке  
✅ **CI/CD готовность** - можно настроить автоматическое развертывание  

## Настройка автоматического развертывания

Создайте GitHub Action для автоматического развертывания:

```yaml
# .github/workflows/deploy.yml
name: Deploy to VPS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USERNAME }}
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /opt/startup-vc
          ./manage.sh update
```

## Структура репозитория

Убедитесь, что в вашем GitHub репозитории есть:

```
startup-vc-platform/
├── app/
│   ├── main.py
│   ├── minimal_app.py
│   └── ...
├── alembic/
├── requirements_simple.txt
├── install_vps.sh
├── DEPLOY_TO_VPS.md
└── README.md
```

## Полезные команды

```bash
# Просмотр статуса
./manage.sh status

# Просмотр логов
./manage.sh logs

# Перезапуск
./manage.sh restart

# Обновление
./manage.sh update
```

---

**Время развертывания**: 5-10 минут  
**Обновление**: 1-2 минуты  
**Готовность**: 100% готово к продакшену
