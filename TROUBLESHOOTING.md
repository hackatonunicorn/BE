# 🔧 Руководство по устранению неполадок

Этот документ поможет вам решить наиболее распространенные проблемы при работе с Startup-VC Platform.

## 📋 Содержание

- [Общие проблемы](#-общие-проблемы)
- [Проблемы с базой данных](#-проблемы-с-базой-данных)
- [Проблемы с приложением](#-проблемы-с-приложением)
- [Проблемы с Celery](#-проблемы-с-celery)
- [Проблемы с мониторингом](#-проблемы-с-мониторингом)
- [Проблемы с сетью](#-проблемы-с-сетью)
- [Проблемы с производительностью](#-проблемы-с-производительностью)
- [Проблемы с безопасностью](#-проблемы-с-безопасностью)

## 🚨 Общие проблемы

### Система не запускается

**Симптомы:**
- Docker контейнеры не запускаются
- Ошибки при `docker-compose up`

**Диагностика:**
```bash
# Проверьте статус Docker
docker --version
docker-compose --version

# Проверьте доступность портов
netstat -tulpn | grep -E ':(80|443|5432|6379|8000|3000|9090)'

# Проверьте свободное место
df -h
```

**Решения:**
1. **Недостаточно места на диске:**
   ```bash
   # Очистите неиспользуемые Docker ресурсы
   docker system prune -a
   
   # Очистите логи
   docker-compose logs --tail=0 -f > /dev/null
   ```

2. **Порты заняты:**
   ```bash
   # Найдите процессы, использующие порты
   sudo lsof -i :8000
   
   # Остановите конфликтующие сервисы
   sudo systemctl stop nginx  # если конфликтует с портом 80
   ```

3. **Проблемы с Docker:**
   ```bash
   # Перезапустите Docker
   sudo systemctl restart docker
   
   # Проверьте статус
   sudo systemctl status docker
   ```

### Переменные окружения

**Симптомы:**
- Ошибки конфигурации
- Сервисы не могут подключиться к БД

**Диагностика:**
```bash
# Проверьте .env файл
cat .env

# Проверьте переменные в контейнере
docker-compose exec app env | grep -E '(DATABASE|REDIS|SECRET)'
```

**Решения:**
1. **Отсутствует .env файл:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с вашими настройками
   ```

2. **Неправильные значения:**
   ```bash
   # Проверьте формат переменных
   # DATABASE_URL должен быть: postgresql://user:pass@host:port/db
   # REDIS_URL должен быть: redis://host:port/db
   ```

## 🗄 Проблемы с базой данных

### PostgreSQL не запускается

**Симптомы:**
- Контейнер postgres постоянно перезапускается
- Ошибки подключения к БД

**Диагностика:**
```bash
# Проверьте логи PostgreSQL
docker-compose logs postgres

# Проверьте статус контейнера
docker-compose ps postgres

# Проверьте подключение
docker-compose exec postgres pg_isready -U postgres
```

**Решения:**
1. **Проблемы с правами доступа:**
   ```bash
   # Проверьте права на директорию данных
   ls -la postgres-data/
   
   # Исправьте права
   sudo chown -R 999:999 postgres-data/
   ```

2. **Недостаточно места:**
   ```bash
   # Проверьте место на диске
   df -h
   
   # Очистите старые данные
   docker volume prune
   ```

3. **Конфликт портов:**
   ```bash
   # Проверьте, не запущен ли локальный PostgreSQL
   sudo systemctl status postgresql
   
   # Остановите локальный сервис
   sudo systemctl stop postgresql
   ```

### Ошибки миграций

**Симптомы:**
- Ошибки при `alembic upgrade head`
- Таблицы не создаются

**Диагностика:**
```bash
# Проверьте статус миграций
docker-compose exec app alembic current

# Проверьте историю миграций
docker-compose exec app alembic history

# Проверьте подключение к БД
docker-compose exec app python -c "from app.core.database import check_db_connection; print(check_db_connection())"
```

**Решения:**
1. **Проблемы с подключением:**
   ```bash
   # Проверьте переменные БД
   docker-compose exec app env | grep DATABASE
   
   # Тест подключения
   docker-compose exec app python -c "
   from sqlalchemy import create_engine
   engine = create_engine('$DATABASE_URL')
   with engine.connect() as conn:
       print('Connection successful')
   "
   ```

2. **Конфликтующие миграции:**
   ```bash
   # Откатитесь к предыдущей версии
   docker-compose exec app alembic downgrade -1
   
   # Примените миграции заново
   docker-compose exec app alembic upgrade head
   ```

3. **Поврежденная БД:**
   ```bash
   # Создайте резервную копию
   docker-compose exec postgres pg_dump -U postgres startup_vc > backup.sql
   
   # Пересоздайте БД
   docker-compose down
   docker volume rm startup-vc_postgres-data
   docker-compose up -d postgres
   
   # Восстановите данные
   docker-compose exec -T postgres psql -U postgres startup_vc < backup.sql
   ```

## 🚀 Проблемы с приложением

### FastAPI не отвечает

**Симптомы:**
- HTTP 502/503 ошибки
- Приложение не отвечает на запросы

**Диагностика:**
```bash
# Проверьте статус контейнера
docker-compose ps app

# Проверьте логи приложения
docker-compose logs app

# Проверьте health check
curl http://localhost:8000/health

# Проверьте внутри контейнера
docker-compose exec app ps aux
```

**Решения:**
1. **Приложение не запускается:**
   ```bash
   # Проверьте синтаксис Python кода
   docker-compose exec app python -m py_compile app/main.py
   
   # Проверьте импорты
   docker-compose exec app python -c "import app.main"
   ```

2. **Проблемы с зависимостями:**
   ```bash
   # Пересоберите образ
   docker-compose build app
   
   # Проверьте requirements.txt
   docker-compose exec app pip list
   ```

3. **Недостаточно памяти:**
   ```bash
   # Проверьте использование памяти
   docker stats
   
   # Увеличьте лимиты в docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

### Ошибки аутентификации

**Симптомы:**
- 401 Unauthorized ошибки
- JWT токены не работают

**Диагностика:**
```bash
# Проверьте SECRET_KEY
docker-compose exec app python -c "
from app.core.config import settings
print('SECRET_KEY set:', bool(settings.SECRET_KEY))
"

# Тест создания токена
docker-compose exec app python -c "
from app.core.auth import create_access_token
token = create_access_token({'sub': 'test'})
print('Token created:', bool(token))
"
```

**Решения:**
1. **Отсутствует SECRET_KEY:**
   ```bash
   # Добавьте в .env
   echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
   ```

2. **Проблемы с JWT:**
   ```bash
   # Проверьте время системы
   date
   
   # Проверьте настройки токена
   docker-compose exec app python -c "
   from app.core.config import settings
   print('Token expire:', settings.ACCESS_TOKEN_EXPIRE_MINUTES)
   "
   ```

## ⚙️ Проблемы с Celery

### Worker не обрабатывает задачи

**Симптомы:**
- Задачи накапливаются в очереди
- Email не отправляются

**Диагностика:**
```bash
# Проверьте статус worker'ов
docker-compose exec celery-worker celery -A app.core.celery_app inspect active

# Проверьте подключение к Redis
docker-compose exec celery-worker celery -A app.core.celery_app inspect ping

# Проверьте очереди
docker-compose exec redis redis-cli llen celery
```

**Решения:**
1. **Проблемы с Redis:**
   ```bash
   # Проверьте статус Redis
   docker-compose exec redis redis-cli ping
   
   # Очистите очередь
   docker-compose exec redis redis-cli flushall
   ```

2. **Worker не запускается:**
   ```bash
   # Проверьте логи worker'а
   docker-compose logs celery-worker
   
   # Перезапустите worker
   docker-compose restart celery-worker
   ```

3. **Задачи зависают:**
   ```bash
   # Проверьте активные задачи
   docker-compose exec celery-worker celery -A app.core.celery_app inspect active
   
   # Отмените зависшие задачи
   docker-compose exec celery-worker celery -A app.core.celery_app control cancel_consumer celery
   ```

### Beat scheduler не работает

**Симптомы:**
- Периодические задачи не выполняются
- Отчеты не генерируются

**Диагностика:**
```bash
# Проверьте статус beat
docker-compose ps celery-beat

# Проверьте логи beat
docker-compose logs celery-beat

# Проверьте расписание
docker-compose exec celery-beat celery -A app.core.celery_app inspect scheduled
```

**Решения:**
1. **Проблемы с расписанием:**
   ```bash
   # Пересоздайте файл расписания
   docker-compose down
   docker volume rm startup-vc_celery-beat-data
   docker-compose up -d
   ```

2. **Конфликт времени:**
   ```bash
   # Проверьте время в контейнерах
   docker-compose exec celery-beat date
   docker-compose exec app date
   ```

## 📊 Проблемы с мониторингом

### Prometheus не собирает метрики

**Симптомы:**
- Метрики не отображаются в Prometheus
- Графики пустые в Grafana

**Диагностика:**
```bash
# Проверьте статус Prometheus
curl http://localhost:9090/-/healthy

# Проверьте targets
curl http://localhost:9090/api/v1/targets

# Проверьте метрики приложения
curl http://localhost:8000/metrics
```

**Решения:**
1. **Target недоступен:**
   ```bash
   # Проверьте конфигурацию prometheus.yml
   docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
   
   # Проверьте сеть между контейнерами
   docker-compose exec prometheus ping app
   ```

2. **Метрики не экспортируются:**
   ```bash
   # Убедитесь, что приложение запущено
   curl http://app:8000/metrics
   
   # Проверьте конфигурацию metrics в приложении
   docker-compose exec app python -c "
   from app.core.metrics import setup_metrics
   setup_metrics()
   "
   ```

### Grafana не отображает данные

**Симптомы:**
- Дашборды пустые
- Ошибки подключения к Prometheus

**Диагностика:**
```bash
# Проверьте статус Grafana
curl http://localhost:3000/api/health

# Проверьте datasources
curl -u admin:admin http://localhost:3000/api/datasources
```

**Решения:**
1. **Проблемы с datasource:**
   ```bash
   # Пересоздайте datasource
   docker-compose exec grafana grafana-cli admin reset-admin-password admin
   ```

2. **Проблемы с дашбордами:**
   ```bash
   # Проверьте файлы дашбордов
   ls -la monitoring/grafana/dashboards/
   
   # Перезапустите Grafana
   docker-compose restart grafana
   ```

## 🌐 Проблемы с сетью

### Контейнеры не могут связаться

**Симптомы:**
- Connection refused ошибки
- Сервисы не находят друг друга

**Диагностика:**
```bash
# Проверьте Docker сети
docker network ls

# Проверьте подключение между контейнерами
docker-compose exec app ping postgres
docker-compose exec app ping redis

# Проверьте DNS резолюцию
docker-compose exec app nslookup postgres
```

**Решения:**
1. **Проблемы с сетью:**
   ```bash
   # Пересоздайте сеть
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

2. **Проблемы с DNS:**
   ```bash
   # Проверьте /etc/hosts в контейнере
   docker-compose exec app cat /etc/hosts
   
   # Используйте IP адреса вместо имен
   docker-compose exec app ping 172.20.0.2
   ```

### Nginx не проксирует запросы

**Симптомы:**
- 502 Bad Gateway ошибки
- Статические файлы не загружаются

**Диагностика:**
```bash
# Проверьте статус Nginx
docker-compose logs nginx

# Проверьте конфигурацию
docker-compose exec nginx nginx -t

# Проверьте upstream
docker-compose exec nginx curl http://app:8000/health
```

**Решения:**
1. **Неправильная конфигурация:**
   ```bash
   # Проверьте nginx.conf
   docker-compose exec nginx cat /etc/nginx/nginx.conf
   
   # Перезагрузите конфигурацию
   docker-compose exec nginx nginx -s reload
   ```

2. **Проблемы с upstream:**
   ```bash
   # Проверьте доступность upstream
   docker-compose exec nginx curl -v http://app:8000/
   
   # Проверьте балансировку нагрузки
   docker-compose exec nginx curl http://app:8000/health
   ```

## ⚡ Проблемы с производительностью

### Медленная работа приложения

**Симптомы:**
- Высокое время отклика
- Таймауты запросов

**Диагностика:**
```bash
# Проверьте использование ресурсов
docker stats

# Проверьте медленные запросы в БД
docker-compose exec postgres psql -U postgres -d startup_vc -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Проверьте индексы
docker-compose exec postgres psql -U postgres -d startup_vc -c "
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;
"
```

**Решения:**
1. **Проблемы с БД:**
   ```bash
   # Добавьте индексы
   docker-compose exec postgres psql -U postgres -d startup_vc -c "
   CREATE INDEX CONCURRENTLY idx_startups_email ON startups(email);
   CREATE INDEX CONCURRENTLY idx_communications_status ON communications(status);
   "
   
   # Обновите статистику
   docker-compose exec postgres psql -U postgres -d startup_vc -c "ANALYZE;"
   ```

2. **Недостаточно ресурсов:**
   ```bash
   # Увеличьте лимиты памяти
   # В docker-compose.yml:
   deploy:
     resources:
       limits:
         memory: 4G
         cpus: '2.0'
   ```

3. **Проблемы с кэшированием:**
   ```bash
   # Проверьте Redis
   docker-compose exec redis redis-cli info memory
   
   # Очистите кэш
   docker-compose exec redis redis-cli flushall
   ```

### Высокая нагрузка на CPU

**Симптомы:**
- 100% использование CPU
- Медленная работа системы

**Диагностика:**
```bash
# Проверьте процессы с высокой нагрузкой
docker-compose exec app top

# Проверьте профиль Python
docker-compose exec app python -c "
import cProfile
import pstats
# Добавьте профилирование в код
"
```

**Решения:**
1. **Оптимизация кода:**
   - Используйте async/await для I/O операций
   - Добавьте кэширование для часто запрашиваемых данных
   - Оптимизируйте SQL запросы

2. **Масштабирование:**
   ```bash
   # Увеличьте количество worker'ов
   docker-compose up -d --scale app=3
   
   # Используйте load balancer
   # Настройте Nginx для балансировки нагрузки
   ```

## 🔒 Проблемы с безопасностью

### SSL сертификаты

**Симптомы:**
- Ошибки SSL в браузере
- HTTPS не работает

**Диагностика:**
```bash
# Проверьте сертификат
openssl x509 -in deployment/ssl/cert.pem -text -noout

# Проверьте срок действия
openssl x509 -in deployment/ssl/cert.pem -dates -noout

# Тест SSL подключения
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

**Решения:**
1. **Истекший сертификат:**
   ```bash
   # Обновите сертификат
   certbot renew --nginx
   
   # Скопируйте новый сертификат
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/ssl/cert.pem
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/ssl/key.pem
   ```

2. **Неправильная конфигурация:**
   ```bash
   # Проверьте права доступа
   chmod 600 deployment/ssl/key.pem
   chmod 644 deployment/ssl/cert.pem
   
   # Перезапустите Nginx
   docker-compose restart nginx
   ```

### Атаки и подозрительная активность

**Симптомы:**
- Множественные failed login попытки
- Необычный трафик

**Диагностика:**
```bash
# Проверьте логи аутентификации
docker-compose logs app | grep "login"

# Проверьте rate limiting
docker-compose logs nginx | grep "429"

# Проверьте подозрительные IP
docker-compose logs nginx | grep -E "(4[0-9][0-9]|5[0-9][0-9])"
```

**Решения:**
1. **Заблокируйте подозрительные IP:**
   ```bash
   # Добавьте в nginx конфигурацию
   # deny 192.168.1.100;
   
   # Или используйте fail2ban
   apt install fail2ban
   ```

2. **Усильте rate limiting:**
   ```nginx
   # В nginx.conf увеличьте ограничения
   limit_req_zone $binary_remote_addr zone=api:10m rate=5r/s;
   ```

## 🆘 Получение помощи

Если вы не можете решить проблему:

1. **Соберите информацию:**
   ```bash
   # Создайте диагностический отчет
   ./scripts/diagnostic.sh > diagnostic-report.txt
   ```

2. **Проверьте логи:**
   ```bash
   # Соберите все логи
   docker-compose logs > all-logs.txt
   ```

3. **Создайте issue в GitHub** с:
   - Описанием проблемы
   - Шагами для воспроизведения
   - Логами и конфигурацией
   - Диагностическим отчетом

4. **Обратитесь в поддержку:**
   - Email: support@startup-vc.com
   - Discord: [Community Server](https://discord.gg/startup-vc)

## 📝 Полезные команды

### Диагностические скрипты

```bash
# Проверка здоровья системы
./scripts/health-check.sh

# Сбор диагностической информации
./scripts/diagnostic.sh

# Проверка безопасности
./scripts/security-audit.sh

# Тест производительности
./scripts/performance-test.sh
```

### Мониторинг в реальном времени

```bash
# Следить за логами всех сервисов
docker-compose logs -f

# Мониторинг ресурсов
docker stats

# Следить за метриками
curl http://localhost:8000/metrics | grep startup_vc
```

### Резервное копирование

```bash
# Создать бэкап
./scripts/backup.sh

# Восстановить из бэкапа
./scripts/restore.sh backup_file.sql

# Очистить старые бэкапы
./scripts/backup.sh cleanup
```

---

**Помните:** Всегда создавайте резервные копии перед внесением изменений в production систему!
