"""
Pydantic models for API validation and serialization
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, EmailStr
import uuid


class StartupStage(str, Enum):
    """Стадии развития стартапа"""
    IDEA = "idea"
    MVP = "mvp"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    GROWTH = "growth"


class CommunicationStatus(str, Enum):
    """Статусы коммуникации"""
    INITIALIZED = "initialized"
    SENT_INITIAL_EMAIL = "sent_initial_email"
    AWAITING_RESPONSE = "awaiting_response"
    FOLLOW_UP_SENT = "follow_up_sent"
    MEETING_REQUESTED = "meeting_requested"
    MEETING_SCHEDULED = "meeting_scheduled"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    CLOSED_REJECTED = "closed_rejected"
    CLOSED_SUCCESSFUL = "closed_successful"


class NotificationType(str, Enum):
    """Типы уведомлений"""
    NEW_FUND_RESPONSE = "new_fund_response"
    MEETING_SCHEDULED = "meeting_scheduled"
    COMMUNICATION_ESCALATED = "communication_escalated"
    WEEKLY_PROGRESS_REPORT = "weekly_progress_report"
    SYSTEM_ERROR = "system_error"


# Base Models
class BaseResponse(BaseModel):
    """Базовая модель ответа"""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Модель ошибки"""
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Startup Models
class StartupBase(BaseModel):
    """Базовая модель стартапа"""
    name: str = Field(..., min_length=1, max_length=255, description="Название стартапа")
    industry: str = Field(..., min_length=1, max_length=100, description="Отрасль")
    stage: StartupStage = Field(..., description="Стадия развития")
    description: Optional[str] = Field(None, max_length=2000, description="Описание стартапа")
    email: EmailStr = Field(..., description="Email для связи")
    contact_person: str = Field(..., min_length=1, max_length=255, description="Контактное лицо")
    website: Optional[str] = Field(None, description="Веб-сайт")
    location: Optional[str] = Field(None, max_length=255, description="Локация")
    funding_goal: Optional[float] = Field(None, gt=0, description="Цель по привлечению средств")


class StartupCreate(StartupBase):
    """Модель для создания стартапа"""
    pass


class StartupUpdate(BaseModel):
    """Модель для обновления стартапа"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, min_length=1, max_length=100)
    stage: Optional[StartupStage] = None
    description: Optional[str] = Field(None, max_length=2000)
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    funding_goal: Optional[float] = Field(None, gt=0)


class StartupResponse(StartupBase):
    """Модель ответа для стартапа"""
    id: int
    pitch_deck_path: Optional[str] = None
    pitch_analysis_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PitchDeckUpload(BaseModel):
    """Модель для загрузки pitch deck"""
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, description="Размер файла в байтах")
    file_type: str = Field(..., regex=r'\.(pdf|pptx|docx|txt)$', description="Тип файла")
    content: str = Field(..., description="Base64 encoded content")


class PitchAnalysisResponse(BaseModel):
    """Модель ответа анализа pitch deck"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    startup_id: int
    file_name: str
    analysis_status: str = Field(..., description="Статус анализа")
    analysis_result: Optional[Dict[str, Any]] = None
    extracted_text: Optional[str] = None
    key_metrics: Optional[Dict[str, Any]] = None
    team_info: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    financial_projections: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    processing_time_seconds: Optional[float] = None


# Communication Models
class CommunicationBase(BaseModel):
    """Базовая модель коммуникации"""
    startup_id: int = Field(..., gt=0)
    vc_fund_id: int = Field(..., gt=0)
    status: CommunicationStatus = Field(default=CommunicationStatus.INITIALIZED)


class CommunicationCreate(CommunicationBase):
    """Модель для создания коммуникации"""
    pass


class CommunicationUpdate(BaseModel):
    """Модель для обновления коммуникации"""
    status: Optional[CommunicationStatus] = None
    escalated_to_human: Optional[bool] = None


class CommunicationResponse(CommunicationBase):
    """Модель ответа для коммуникации"""
    id: int
    email_thread_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    generated_emails: Optional[Dict[str, Any]] = None
    escalated_to_human: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Related data
    startup_name: Optional[str] = None
    vc_fund_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class CommunicationTimelineItem(BaseModel):
    """Элемент временной шкалы коммуникации"""
    timestamp: datetime
    event_type: str
    description: str
    actor: str
    metadata: Optional[Dict[str, Any]] = None


class CommunicationTimeline(BaseModel):
    """Временная шкала коммуникации"""
    communication_id: int
    items: List[CommunicationTimelineItem]
    total_events: int


class OutreachRequest(BaseModel):
    """Запрос на инициацию outreach"""
    fund_ids: List[int] = Field(..., min_items=1, max_items=20, description="Список ID фондов")
    custom_message: Optional[str] = Field(None, max_length=1000, description="Кастомное сообщение")
    priority: Optional[str] = Field("normal", regex="^(low|normal|high|urgent)$")
    scheduled_at: Optional[datetime] = Field(None, description="Запланированное время отправки")


class EscalationRequest(BaseModel):
    """Запрос на эскалацию"""
    reason: str = Field(..., min_length=1, max_length=500, description="Причина эскалации")
    urgency: str = Field("normal", regex="^(low|normal|high|urgent)$")
    notes: Optional[str] = Field(None, max_length=1000, description="Дополнительные заметки")
    assign_to: Optional[str] = Field(None, description="Назначить конкретному менеджеру")


# Analytics Models
class DashboardMetrics(BaseModel):
    """Метрики для дашборда"""
    total_communications: int
    active_communications: int
    successful_communications: int
    escalated_communications: int
    average_response_time_hours: float
    success_rate: float
    meeting_conversion_rate: float


class DashboardData(BaseModel):
    """Данные для дашборда стартапа"""
    startup_id: int
    startup_name: str
    metrics: DashboardMetrics
    recent_communications: List[CommunicationResponse]
    upcoming_meetings: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime = Field(default_factory=datetime.now)


class SuccessRateMetrics(BaseModel):
    """Метрики успешности платформы"""
    overall_success_rate: float
    industry_breakdown: Dict[str, float]
    stage_breakdown: Dict[str, float]
    fund_performance: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
    conversion_funnel: Dict[str, int]
    average_deal_size: float
    time_to_close_days: float


class PlatformAnalytics(BaseModel):
    """Аналитика платформы"""
    total_startups: int
    total_vc_funds: int
    total_communications: int
    success_rate_metrics: SuccessRateMetrics
    top_performing_funds: List[Dict[str, Any]]
    most_active_industries: List[Dict[str, Any]]
    geographic_distribution: Dict[str, int]
    period_start: datetime
    period_end: datetime
    generated_at: datetime = Field(default_factory=datetime.now)


# Notification Models
class NotificationRequest(BaseModel):
    """Запрос на отправку уведомления"""
    user_id: int = Field(..., gt=0)
    notification_type: NotificationType
    data: Dict[str, Any] = Field(default_factory=dict)
    channels: List[str] = Field(default=["email"], description="Каналы доставки")
    priority: str = Field("normal", regex="^(low|normal|high|urgent)$")


class NotificationResponse(BaseModel):
    """Ответ на отправку уведомления"""
    notification_id: str
    user_id: int
    status: str
    delivery_status: Dict[str, str]
    sent_at: datetime
    delivered_at: Optional[datetime] = None


# Authentication Models
class Token(BaseModel):
    """Модель токена"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Данные токена"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: List[str] = []


class UserLogin(BaseModel):
    """Модель входа пользователя"""
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class UserRegister(BaseModel):
    """Модель регистрации пользователя"""
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)


# Rate Limiting Models
class RateLimitInfo(BaseModel):
    """Информация о rate limiting"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


# File Upload Models
class FileUploadResponse(BaseModel):
    """Ответ на загрузку файла"""
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    upload_status: str
    upload_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


# Search and Filter Models
class StartupSearchFilters(BaseModel):
    """Фильтры для поиска стартапов"""
    industry: Optional[List[str]] = None
    stage: Optional[List[StartupStage]] = None
    location: Optional[str] = None
    funding_goal_min: Optional[float] = None
    funding_goal_max: Optional[float] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class CommunicationSearchFilters(BaseModel):
    """Фильтры для поиска коммуникаций"""
    status: Optional[List[CommunicationStatus]] = None
    vc_fund_id: Optional[List[int]] = None
    escalated: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Параметры пагинации"""
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(20, ge=1, le=100, description="Размер страницы")
    sort_by: Optional[str] = Field(None, description="Поле для сортировки")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Порядок сортировки")


class PaginatedResponse(BaseModel):
    """Пагинированный ответ"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# Health Check Models
class HealthCheck(BaseModel):
    """Модель проверки здоровья"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    services: Dict[str, str] = Field(default_factory=dict)


# Validation and Custom Validators
class CustomValidators:
    """Кастомные валидаторы"""
    
    @staticmethod
    def validate_funding_goal(v):
        """Валидация цели финансирования"""
        if v is not None and v <= 0:
            raise ValueError("Funding goal must be positive")
        return v
    
    @staticmethod
    def validate_website(v):
        """Валидация веб-сайта"""
        if v is not None and not v.startswith(('http://', 'https://')):
            v = f"https://{v}"
        return v


# Response Models with Custom Fields
class StartupListResponse(BaseModel):
    """Ответ со списком стартапов"""
    startups: List[StartupResponse]
    total_count: int
    page: int
    size: int
    has_more: bool


class CommunicationListResponse(BaseModel):
    """Ответ со списком коммуникаций"""
    communications: List[CommunicationResponse]
    total_count: int
    page: int
    size: int
    has_more: bool


# Error Models
class ValidationErrorDetail(BaseModel):
    """Детали ошибки валидации"""
    field: str
    message: str
    value: Any


class ValidationErrorResponse(ErrorResponse):
    """Ответ с ошибками валидации"""
    validation_errors: List[ValidationErrorDetail]


class NotFoundResponse(ErrorResponse):
    """Ответ для ресурса не найден"""
    resource_type: str
    resource_id: Union[int, str]


class ConflictResponse(ErrorResponse):
    """Ответ для конфликта"""
    conflicting_field: str
    conflicting_value: Any


# Webhook Models
class WebhookEvent(BaseModel):
    """Модель webhook события"""
    event_type: str
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]
    signature: Optional[str] = None


class WebhookSubscription(BaseModel):
    """Модель подписки на webhook"""
    url: str = Field(..., regex=r'^https?://')
    events: List[str]
    secret: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
