# 🚀 Отчет о системе кампаний

## Обзор

Создана полнофункциональная система управления кампаниями рассылки инвесторам для Startup VC Platform, строго соответствующая требованиям из предоставленных скриншотов.

## 🏗 Архитектура системы

### Компоненты

1. **Модели данных** (`app/data/models.py`)
   - `Campaign` - основная модель кампании
   - Enum'ы для всех опций: `Industry`, `FundingStage`, `TeamSize`, `FundraisingTimeline`, `PreviousFunding`, `UseOfFunds`
   - Связи с пользователями и стартапами

2. **Схемы валидации** (`app/api/campaign_schemas.py`)
   - Pydantic модели для валидации входных данных
   - Схемы для пошагового создания кампаний
   - Response модели для API

3. **Репозиторий** (`app/data/repositories/campaign_repository.py`)
   - CRUD операции для кампаний
   - Поиск и фильтрация
   - Статистика и метрики

4. **API Endpoints** (`app/api/campaigns.py`)
   - Полный набор REST API для управления кампаниями
   - Пошаговое создание кампаний
   - Управление статусами

## 📋 Функциональность согласно скриншотам

### Шаг 1: Company Information

**Поля согласно скриншоту:**
- ✅ **Company Name** (обязательное) - `company_name`
- ✅ **Company Website** (необязательное) - `company_website`
- ✅ **Industry** (обязательное) - `industry` (dropdown с 16 опциями)
- ✅ **Current Funding Stage** (обязательное) - `current_funding_stage`
- ✅ **Team Size** (обязательное) - `team_size` (5 вариантов: 1-5, 6-20, 21-50, 51-100, 100+)
- ✅ **Location** (обязательное) - `location`
- ✅ **Pitch Deck Upload** (обязательное) - `pitch_deck_url`

**Доступные опции Industry:**
- SaaS, FinTech, HealthTech, EdTech, E-commerce, Marketplace
- AI/ML, Blockchain, Gaming, Media, Real Estate, Transportation
- Energy, Manufacturing, Agriculture, Security

**Доступные опции Funding Stage:**
- Pre-seed, Seed, Series A, Series B, Series C+

**Доступные опции Team Size:**
- 1-5 employees, 6-20 employees, 21-50 employees, 51-100 employees, 100+ employees

### Шаг 2: Fundraising Goals

**Поля согласно скриншоту:**
- ✅ **Target Raise Amount** - `target_raise_amount` (слайдер от $30K до $10M)
- ✅ **Fundraising Timeline** (обязательное) - `fundraising_timeline`
- ✅ **Use of Funds** (обязательное, множественный выбор) - `use_of_funds`
- ✅ **Previous Funding** (обязательное) - `previous_funding`

**Доступные опции Timeline:**
- 3-6 months, 6-12 months, 12+ months

**Доступные опции Use of Funds (множественный выбор):**
- Product Development, Team Expansion, Marketing & Sales, Operations
- Technology Infrastructure, Market Expansion, Research & Development, Working Capital

**Доступные опции Previous Funding:**
- None - First time raising, Friends & Family, Angel Investors
- Seed Round, Series A, Series B+

### Список кампаний

**Поля согласно скриншоту таблицы:**
- ✅ **Campaign Name** - `name` + `description`
- ✅ **Status** - `status` (Draft, Active, Completed, Paused)
- ✅ **Sent** - `sent_count`
- ✅ **Replied** - `replied_count`
- ✅ **Meetings** - `meetings_count`
- ✅ **Response Rate** - `response_rate` (автоматический расчет)
- ✅ **Actions** - API для редактирования и удаления

## 🔧 API Endpoints

### Основные операции

```bash
# Получить опции для создания кампаний
GET /api/campaigns/options

# Получить список кампаний
GET /api/campaigns/
GET /api/campaigns/?status=active&search=tech&industry=saas

# Создать кампанию
POST /api/campaigns/

# Получить кампанию по ID
GET /api/campaigns/{campaign_id}

# Обновить кампанию
PUT /api/campaigns/{campaign_id}

# Удалить кампанию
DELETE /api/campaigns/{campaign_id}
```

### Управление статусами

```bash
# Обновить статус кампании
PATCH /api/campaigns/{campaign_id}/status
{"status": "active"}

# Запустить кампанию
POST /api/campaigns/{campaign_id}/launch

# Приостановить кампанию
POST /api/campaigns/{campaign_id}/pause

# Завершить кампанию
POST /api/campaigns/{campaign_id}/complete
```

### Пошаговое создание

```bash
# Шаг 1: Company Information
POST /api/campaigns/create/step1
{
  "name": "My Campaign",
  "company_name": "TechFlow Inc.",
  "company_website": "https://techflow.com",
  "industry": "saas",
  "current_funding_stage": "seed",
  "team_size": "6-20",
  "location": "San Francisco, CA",
  "pitch_deck_url": "https://..."
}

# Шаг 2: Fundraising Goals
PUT /api/campaigns/{campaign_id}/step2
{
  "target_raise_amount": 1000000.0,
  "fundraising_timeline": "6-12 months",
  "use_of_funds": ["product_development", "team_expansion"],
  "previous_funding": "friends_family"
}
```

### Статистика и аналитика

```bash
# Получить статистику кампаний
GET /api/campaigns/stats

# Массовое обновление статусов
POST /api/campaigns/bulk-status-update
{
  "campaign_ids": [1, 2, 3],
  "status": "active"
}

# Загрузка pitch deck
POST /api/campaigns/{campaign_id}/upload-pitch-deck
```

## 📊 Модель данных

### Таблица campaigns

```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    startup_id INTEGER REFERENCES startups(id),
    
    -- Campaign basic info
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status campaignstatus NOT NULL DEFAULT 'draft',
    
    -- Company Information (Step 1)
    company_name VARCHAR(200) NOT NULL,
    company_website VARCHAR(500),
    industry industry NOT NULL,
    current_funding_stage fundingstage NOT NULL,
    team_size teamsize NOT NULL,
    location VARCHAR(200) NOT NULL,
    pitch_deck_url VARCHAR(500),
    
    -- Fundraising Goals (Step 2)
    target_raise_amount FLOAT NOT NULL,
    fundraising_timeline fundraisingtimeline NOT NULL,
    use_of_funds JSON NOT NULL,
    previous_funding previousfunding NOT NULL,
    
    -- Campaign metrics
    sent_count INTEGER DEFAULT 0,
    replied_count INTEGER DEFAULT 0,
    meetings_count INTEGER DEFAULT 0,
    response_rate FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    launched_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Enum типы

```sql
-- Статусы кампаний
CREATE TYPE campaignstatus AS ENUM ('draft', 'active', 'paused', 'completed');

-- Индустрии
CREATE TYPE industry AS ENUM (
    'saas', 'fintech', 'healthtech', 'edtech', 'ecommerce', 'marketplace',
    'ai_ml', 'blockchain', 'gaming', 'media', 'real_estate', 'transportation',
    'energy', 'manufacturing', 'agriculture', 'security'
);

-- Стадии финансирования
CREATE TYPE fundingstage AS ENUM ('preseed', 'seed', 'series_a', 'series_b', 'series_c_plus');

-- Размеры команды
CREATE TYPE teamsize AS ENUM ('1-5', '6-20', '21-50', '51-100', '100+');

-- Временные рамки сбора средств
CREATE TYPE fundraisingtimeline AS ENUM ('3-6 months', '6-12 months', '12+ months');

-- Предыдущее финансирование
CREATE TYPE previousfunding AS ENUM (
    'none', 'friends_family', 'angel_investors', 'seed_round', 'series_a', 'series_b_plus'
);
```

## 🔒 Безопасность и валидация

### Валидация данных

```python
# Валидация суммы сбора
@validator('target_raise_amount')
def validate_raise_amount(cls, v):
    if v < 30000 or v > 10000000:
        raise ValueError('Target raise amount must be between $30K and $10M')
    return v

# Валидация использования средств
@validator('use_of_funds')
def validate_use_of_funds(cls, v):
    if not v:
        raise ValueError('At least one use of funds must be selected')
    return v
```

### Авторизация

- Все endpoints требуют аутентификации
- Пользователи могут управлять только своими кампаниями
- Проверка прав доступа на уровне репозитория

### Изоляция данных

```python
def get_user_campaign_by_id(self, campaign_id: int, user_id: int) -> Optional[Campaign]:
    """Get a specific campaign by ID that belongs to a user"""
    return (
        self.db.query(Campaign)
        .filter(
            and_(
                Campaign.id == campaign_id,
                Campaign.user_id == user_id
            )
        )
        .first()
    )
```

## 📈 Метрики и аналитика

### Автоматический расчет метрик

```python
def update_metrics(self, campaign_id: int, metrics: Dict[str, int]) -> Optional[Campaign]:
    """Update campaign metrics"""
    campaign = self.get_by_id(campaign_id)
    if campaign:
        # Update counts
        if 'sent_count' in metrics:
            campaign.sent_count = metrics['sent_count']
        if 'replied_count' in metrics:
            campaign.replied_count = metrics['replied_count']
        if 'meetings_count' in metrics:
            campaign.meetings_count = metrics['meetings_count']
        
        # Calculate response rate
        if campaign.sent_count > 0:
            campaign.response_rate = (campaign.replied_count / campaign.sent_count) * 100
        else:
            campaign.response_rate = 0.0
```

### Статистика пользователя

```python
def get_campaign_stats(self, user_id: int) -> Dict[str, Any]:
    """Get campaign statistics for a user"""
    campaigns = self.db.query(Campaign).filter(Campaign.user_id == user_id).all()
    
    stats = {
        'total_campaigns': len(campaigns),
        'active_campaigns': len([c for c in campaigns if c.status == CampaignStatus.ACTIVE]),
        'draft_campaigns': len([c for c in campaigns if c.status == CampaignStatus.DRAFT]),
        'paused_campaigns': len([c for c in campaigns if c.status == CampaignStatus.PAUSED]),
        'completed_campaigns': len([c for c in campaigns if c.status == CampaignStatus.COMPLETED]),
        'total_sent': sum(c.sent_count for c in campaigns),
        'total_replied': sum(c.replied_count for c in campaigns),
        'total_meetings': sum(c.meetings_count for c in campaigns),
        'average_response_rate': 0.0
    }
```

## 🧪 Тестирование

### Автоматические тесты

**Файл:** `test_campaigns.py`

**Тесты:**
- Получение опций кампаний
- Создание кампании
- Получение списка кампаний
- Обновление кампании
- Управление статусами
- Статистика
- Удаление кампании

**Запуск:**
```bash
python test_campaigns.py
```

### Примеры запросов

**Создание кампании:**
```bash
curl -X POST "http://localhost:8000/api/campaigns/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechFlow Campaign",
    "description": "Raising Series A for tech platform",
    "company_name": "TechFlow Inc.",
    "company_website": "https://techflow.com",
    "industry": "saas",
    "current_funding_stage": "series_a",
    "team_size": "6-20",
    "location": "San Francisco, CA",
    "target_raise_amount": 2000000.0,
    "fundraising_timeline": "6-12 months",
    "use_of_funds": ["product_development", "team_expansion"],
    "previous_funding": "seed_round"
  }'
```

**Получение списка кампаний:**
```bash
curl -X GET "http://localhost:8000/api/campaigns/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Обновление статуса:**
```bash
curl -X PATCH "http://localhost:8000/api/campaigns/1/status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

## 🔄 Интеграция с существующей системой

### Связи с другими моделями

```python
# Связь с пользователями
campaign.user_id → users.id

# Связь со стартапами
campaign.startup_id → startups.id

# Связь с коммуникациями
communications.campaign_id → campaigns.id
```

### Обновление модели Communication

```python
class Communication(Base):
    # ... existing fields ...
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="communications")
```

## 📱 Соответствие UI требованиям

### Пошаговое создание

1. **Шаг 1: Company Information**
   - Все поля точно соответствуют скриншоту
   - Dropdown'ы с правильными опциями
   - Валидация обязательных полей

2. **Шаг 2: Fundraising Goals**
   - Слайдер для суммы (30K - 10M)
   - Множественный выбор для использования средств
   - Все dropdown'ы с правильными опциями

3. **Список кампаний**
   - Все колонки из таблицы реализованы
   - Сортировка по всем полям
   - Фильтрация по статусу
   - Действия: редактирование, удаление

### Статусы кампаний

- ✅ **Draft** - черновик
- ✅ **Active** - активная кампания
- ✅ **Paused** - приостановленная
- ✅ **Completed** - завершенная

## 🚀 Развертывание

### Миграции базы данных

```bash
# Создание миграции
alembic revision --autogenerate -m "Add campaign tables"

# Применение миграций
alembic upgrade head
```

### Переменные окружения

```bash
# Никаких дополнительных переменных не требуется
# Используются существующие настройки базы данных
```

## ✅ Заключение

Создана полнофункциональная система управления кампаниями, которая:

- ✅ **Точно соответствует** всем требованиям из скриншотов
- ✅ **Поддерживает пошаговое создание** кампаний
- ✅ **Включает все поля** из UI форм
- ✅ **Реализует все статусы** кампаний
- ✅ **Предоставляет полный CRUD** API
- ✅ **Автоматически рассчитывает** метрики
- ✅ **Обеспечивает безопасность** и изоляцию данных
- ✅ **Включает тесты** для проверки функциональности

Система готова к интеграции с фронтендом и production использованию.

**Ключевые особенности:**
- Полное соответствие UI требованиям
- Гибкая система статусов
- Автоматический расчет метрик
- Безопасная архитектура
- Comprehensive API
- Готовые тесты
