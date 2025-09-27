"""
Notification Service - Система уведомлений для стартапов
"""
import os
import logging
import asyncio
import json
import smtplib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from collections import defaultdict

from app.core.database import get_db
from app.data.models import Startup, Communication
from app.data.repositories import startup_repository, communication_repository

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Типы уведомлений"""
    NEW_FUND_RESPONSE = "new_fund_response"
    MEETING_SCHEDULED = "meeting_scheduled"
    COMMUNICATION_ESCALATED = "communication_escalated"
    WEEKLY_PROGRESS_REPORT = "weekly_progress_report"
    SYSTEM_ERROR = "system_error"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    MEETING_REMINDER = "meeting_reminder"
    FUND_MATCH_FOUND = "fund_match_found"
    COMMUNICATION_TIMEOUT = "communication_timeout"
    SUCCESSFUL_CLOSURE = "successful_closure"


class NotificationChannel(Enum):
    """Каналы уведомлений"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Приоритеты уведомлений"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(Enum):
    """Статусы доставки"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class NotificationTemplate:
    """Шаблон уведомления"""
    template_id: str
    notification_type: NotificationType
    channel: NotificationChannel
    subject: str
    content: str
    variables: List[str]
    priority: NotificationPriority = NotificationPriority.NORMAL
    is_active: bool = True


@dataclass
class NotificationPreferences:
    """Пользовательские настройки уведомлений"""
    user_id: int
    channels: Dict[NotificationChannel, bool]
    types: Dict[NotificationType, bool]
    frequency: Dict[NotificationType, str]  # immediate, hourly, daily, weekly
    quiet_hours: Dict[str, str]  # start_time, end_time
    batch_enabled: bool = True
    max_notifications_per_hour: int = 10
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Notification:
    """Уведомление"""
    notification_id: str
    user_id: int
    notification_type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    subject: str
    content: str
    data: Dict[str, Any]
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.notification_id is None:
            self.notification_id = str(uuid.uuid4())


@dataclass
class BatchNotification:
    """Batch уведомление"""
    batch_id: str
    notifications: List[Notification]
    scheduled_at: datetime
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.batch_id is None:
            self.batch_id = str(uuid.uuid4())


class NotificationService:
    """
    Сервис уведомлений для стартапов
    """
    
    def __init__(self):
        # Email configuration
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL', 'notifications@startupvc.com')
        }
        
        # Telegram configuration
        self.telegram_config = {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'api_url': f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}"
        }
        
        # Notification templates
        self.templates = self._initialize_templates()
        
        # User preferences cache
        self.preferences_cache: Dict[int, NotificationPreferences] = {}
        
        # Batch processing
        self.batch_queue: List[Notification] = []
        self.batch_size = 10
        self.batch_interval = timedelta(minutes=5)
        
        # Delivery statistics
        self.delivery_stats = {
            'total_sent': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'retry_attempts': 0,
            'channel_stats': defaultdict(int),
            'type_stats': defaultdict(int)
        }
        
        logger.info("NotificationService initialized")
    
    def _initialize_templates(self) -> Dict[str, NotificationTemplate]:
        """Инициализация шаблонов уведомлений"""
        templates = {}
        
        # Email templates
        templates['new_fund_response_email'] = NotificationTemplate(
            template_id='new_fund_response_email',
            notification_type=NotificationType.NEW_FUND_RESPONSE,
            channel=NotificationChannel.EMAIL,
            subject='🎉 Новый ответ от {{fund_name}}',
            content='''
            <h2>Получен новый ответ от венчурного фонда!</h2>
            
            <p>Привет, {{startup_contact}}!</p>
            
            <p>Фонд <strong>{{fund_name}}</strong> ответил на ваше обращение:</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                <p><strong>Ответ:</strong></p>
                <p>{{response_content}}</p>
            </div>
            
            <p><strong>Рекомендуемое действие:</strong> {{suggested_action}}</p>
            
            <p><strong>Статус коммуникации:</strong> {{communication_status}}</p>
            
            <p>Следующий шаг будет выполнен автоматически, но вы можете проверить детали в вашем личном кабинете.</p>
            
            <p>С уважением,<br>Команда Startup-VC Platform</p>
            ''',
            variables=['fund_name', 'startup_contact', 'response_content', 'suggested_action', 'communication_status'],
            priority=NotificationPriority.HIGH
        )
        
        templates['meeting_scheduled_email'] = NotificationTemplate(
            template_id='meeting_scheduled_email',
            notification_type=NotificationType.MEETING_SCHEDULED,
            channel=NotificationChannel.EMAIL,
            subject='📅 Встреча запланирована с {{fund_name}}',
            content='''
            <h2>Встреча запланирована!</h2>
            
            <p>Отличные новости, {{startup_contact}}!</p>
            
            <p>Встреча с фондом <strong>{{fund_name}}</strong> успешно запланирована:</p>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                <p><strong>Дата и время:</strong> {{meeting_date}}</p>
                <p><strong>Продолжительность:</strong> {{meeting_duration}}</p>
                <p><strong>Ссылка для подключения:</strong> <a href="{{meeting_link}}">{{meeting_link}}</a></p>
                <p><strong>Формат:</strong> {{meeting_format}}</p>
            </div>
            
            <p><strong>Подготовка к встрече:</strong></p>
            <ul>
                <li>Подготовьте презентацию вашего проекта</li>
                <li>Изучите портфель фонда и недавние инвестиции</li>
                <li>Подготовьте ответы на возможные вопросы</li>
                <li>Проверьте техническое оборудование</li>
            </ul>
            
            <p>Удачи на встрече! 🚀</p>
            
            <p>С уважением,<br>Команда Startup-VC Platform</p>
            ''',
            variables=['fund_name', 'startup_contact', 'meeting_date', 'meeting_duration', 'meeting_link', 'meeting_format'],
            priority=NotificationPriority.HIGH
        )
        
        templates['communication_escalated_email'] = NotificationTemplate(
            template_id='communication_escalated_email',
            notification_type=NotificationType.COMMUNICATION_ESCALATED,
            channel=NotificationChannel.EMAIL,
            subject='⚠️ Коммуникация эскалирована к человеку',
            content='''
            <h2>Требуется ваше внимание</h2>
            
            <p>Привет, {{startup_contact}}!</p>
            
            <p>Коммуникация с фондом <strong>{{fund_name}}</strong> была эскалирована к человеку для ручного рассмотрения.</p>
            
            <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <p><strong>Причина эскалации:</strong> {{escalation_reason}}</p>
                <p><strong>Текущий статус:</strong> {{communication_status}}</p>
                <p><strong>ID коммуникации:</strong> {{communication_id}}</p>
            </div>
            
            <p><strong>Рекомендуемые действия:</strong></p>
            <ul>
                <li>Проверьте детали в личном кабинете</li>
                <li>При необходимости свяжитесь с нашим менеджером</li>
                <li>Подготовьте дополнительную информацию</li>
            </ul>
            
            <p>Наша команда свяжется с вами в ближайшее время.</p>
            
            <p>С уважением,<br>Команда Startup-VC Platform</p>
            ''',
            variables=['fund_name', 'startup_contact', 'escalation_reason', 'communication_status', 'communication_id'],
            priority=NotificationPriority.URGENT
        )
        
        templates['weekly_progress_email'] = NotificationTemplate(
            template_id='weekly_progress_email',
            notification_type=NotificationType.WEEKLY_PROGRESS_REPORT,
            channel=NotificationChannel.EMAIL,
            subject='📊 Еженедельный отчет по коммуникациям',
            content='''
            <h2>Еженедельный отчет</h2>
            
            <p>Привет, {{startup_contact}}!</p>
            
            <p>Вот ваш еженедельный отчет по коммуникациям с венчурными фондами:</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>📈 Статистика за неделю</h3>
                <ul>
                    <li><strong>Новых коммуникаций:</strong> {{new_communications}}</li>
                    <li><strong>Получено ответов:</strong> {{responses_received}}</li>
                    <li><strong>Запланировано встреч:</strong> {{meetings_scheduled}}</li>
                    <li><strong>Успешных закрытий:</strong> {{successful_closures}}</li>
                </ul>
                
                <h3>🎯 Активные коммуникации</h3>
                <ul>
                    <li><strong>Ожидают ответа:</strong> {{awaiting_response}}</li>
                    <li><strong>Требуют follow-up:</strong> {{follow_up_needed}}</li>
                    <li><strong>Эскалированы:</strong> {{escalated}}</li>
                </ul>
            </div>
            
            <p><strong>Рекомендации на следующую неделю:</strong></p>
            <ul>
                {{recommendations}}
            </ul>
            
            <p>Продолжайте в том же духе! 🚀</p>
            
            <p>С уважением,<br>Команда Startup-VC Platform</p>
            ''',
            variables=['startup_contact', 'new_communications', 'responses_received', 'meetings_scheduled', 
                      'successful_closures', 'awaiting_response', 'follow_up_needed', 'escalated', 'recommendations'],
            priority=NotificationPriority.NORMAL
        )
        
        # Telegram templates
        templates['new_fund_response_telegram'] = NotificationTemplate(
            template_id='new_fund_response_telegram',
            notification_type=NotificationType.NEW_FUND_RESPONSE,
            channel=NotificationChannel.TELEGRAM,
            subject='🎉 Новый ответ от {{fund_name}}',
            content='''
            🎉 *Новый ответ от венчурного фонда!*
            
            Фонд *{{fund_name}}* ответил на ваше обращение:
            
            {{response_content}}
            
            📋 *Рекомендуемое действие:* {{suggested_action}}
            📊 *Статус:* {{communication_status}}
            
            Следующий шаг будет выполнен автоматически.
            ''',
            variables=['fund_name', 'response_content', 'suggested_action', 'communication_status'],
            priority=NotificationPriority.HIGH
        )
        
        templates['meeting_scheduled_telegram'] = NotificationTemplate(
            template_id='meeting_scheduled_telegram',
            notification_type=NotificationType.MEETING_SCHEDULED,
            channel=NotificationChannel.TELEGRAM,
            subject='📅 Встреча запланирована',
            content='''
            📅 *Встреча запланирована!*
            
            Встреча с фондом *{{fund_name}}* успешно запланирована:
            
            📅 *Дата:* {{meeting_date}}
            ⏱️ *Длительность:* {{meeting_duration}}
            🔗 *Ссылка:* {{meeting_link}}
            
            🎯 *Подготовьтесь к встрече!*
            
            Удачи! 🚀
            ''',
            variables=['fund_name', 'meeting_date', 'meeting_duration', 'meeting_link'],
            priority=NotificationPriority.HIGH
        )
        
        return templates
    
    async def send_notification(self, user_id: int, notification_type: NotificationType, 
                              data: Dict[str, Any], channels: Optional[List[NotificationChannel]] = None) -> bool:
        """
        Отправка уведомления пользователю
        """
        try:
            logger.info(f"Sending notification {notification_type.value} to user {user_id}")
            
            # Получаем пользовательские настройки
            preferences = await self._get_user_preferences(user_id)
            
            # Определяем каналы для отправки
            if channels is None:
                channels = self._get_available_channels(preferences, notification_type)
            
            if not channels:
                logger.warning(f"No channels available for notification {notification_type.value} to user {user_id}")
                return False
            
            notifications_sent = 0
            
            # Отправляем уведомления по каждому каналу
            for channel in channels:
                if await self._should_send_notification(user_id, notification_type, channel, preferences):
                    success = await self._send_single_notification(
                        user_id, notification_type, channel, data, preferences
                    )
                    if success:
                        notifications_sent += 1
            
            # Обновляем статистику
            self.delivery_stats['total_sent'] += notifications_sent
            self.delivery_stats['type_stats'][notification_type.value] += notifications_sent
            
            logger.info(f"Sent {notifications_sent} notifications for {notification_type.value} to user {user_id}")
            return notifications_sent > 0
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False
    
    async def schedule_periodic_reports(self) -> int:
        """
        Планирование периодических отчетов
        """
        try:
            logger.info("Scheduling periodic reports")
            
            scheduled_count = 0
            current_time = datetime.now()
            
            # Получаем всех пользователей для еженедельных отчетов
            db = next(get_db())
            users = db.query(Startup).all()
            
            for user in users:
                preferences = await self._get_user_preferences(user.id)
                
                # Проверяем настройки для еженедельных отчетов
                if (preferences.types.get(NotificationType.WEEKLY_PROGRESS_REPORT, False) and
                    preferences.frequency.get(NotificationType.WEEKLY_PROGRESS_REPORT) == 'weekly'):
                    
                    # Планируем отчет на следующий понедельник в 9:00
                    next_monday = current_time + timedelta(days=(7 - current_time.weekday()))
                    next_monday = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
                    
                    if next_monday > current_time:
                        # Генерируем данные для отчета
                        report_data = await self._generate_weekly_report_data(user.id)
                        
                        # Создаем уведомление
                        notification = Notification(
                            notification_id=str(uuid.uuid4()),
                            user_id=user.id,
                            notification_type=NotificationType.WEEKLY_PROGRESS_REPORT,
                            channel=NotificationChannel.EMAIL,
                            priority=NotificationPriority.NORMAL,
                            subject="Еженедельный отчет по коммуникациям",
                            content="",
                            data=report_data,
                            scheduled_at=next_monday
                        )
                        
                        # Добавляем в очередь batch обработки
                        self.batch_queue.append(notification)
                        scheduled_count += 1
            
            logger.info(f"Scheduled {scheduled_count} periodic reports")
            return scheduled_count
            
        except Exception as e:
            logger.error(f"Error scheduling periodic reports: {e}")
            return 0
    
    async def update_notification_preferences(self, user_id: int, preferences_data: Dict[str, Any]) -> bool:
        """
        Обновление пользовательских настроек уведомлений
        """
        try:
            logger.info(f"Updating notification preferences for user {user_id}")
            
            # Получаем текущие настройки
            current_preferences = await self._get_user_preferences(user_id)
            
            # Обновляем настройки
            if 'channels' in preferences_data:
                for channel_name, enabled in preferences_data['channels'].items():
                    channel = NotificationChannel(channel_name)
                    current_preferences.channels[channel] = enabled
            
            if 'types' in preferences_data:
                for type_name, enabled in preferences_data['types'].items():
                    notification_type = NotificationType(type_name)
                    current_preferences.types[notification_type] = enabled
            
            if 'frequency' in preferences_data:
                for type_name, frequency in preferences_data['frequency'].items():
                    notification_type = NotificationType(type_name)
                    current_preferences.frequency[notification_type] = frequency
            
            if 'quiet_hours' in preferences_data:
                current_preferences.quiet_hours.update(preferences_data['quiet_hours'])
            
            if 'batch_enabled' in preferences_data:
                current_preferences.batch_enabled = preferences_data['batch_enabled']
            
            if 'max_notifications_per_hour' in preferences_data:
                current_preferences.max_notifications_per_hour = preferences_data['max_notifications_per_hour']
            
            current_preferences.updated_at = datetime.now()
            
            # Обновляем кэш
            self.preferences_cache[user_id] = current_preferences
            
            # Сохраняем в базу данных (симуляция)
            await self._save_user_preferences(user_id, current_preferences)
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False
    
    async def get_notification_history(self, user_id: int, limit: int = 50, 
                                     notification_type: Optional[NotificationType] = None) -> List[Dict[str, Any]]:
        """
        Получение истории уведомлений пользователя
        """
        try:
            logger.info(f"Getting notification history for user {user_id}")
            
            # Симуляция получения истории из базы данных
            mock_history = [
                {
                    'notification_id': str(uuid.uuid4()),
                    'notification_type': NotificationType.NEW_FUND_RESPONSE.value,
                    'channel': NotificationChannel.EMAIL.value,
                    'subject': 'Новый ответ от Innovation Ventures',
                    'status': DeliveryStatus.DELIVERED.value,
                    'sent_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'delivered_at': (datetime.now() - timedelta(hours=1)).isoformat()
                },
                {
                    'notification_id': str(uuid.uuid4()),
                    'notification_type': NotificationType.MEETING_SCHEDULED.value,
                    'channel': NotificationChannel.TELEGRAM.value,
                    'subject': 'Встреча запланирована с Growth Capital Partners',
                    'status': DeliveryStatus.DELIVERED.value,
                    'sent_at': (datetime.now() - timedelta(hours=5)).isoformat(),
                    'delivered_at': (datetime.now() - timedelta(hours=4)).isoformat()
                },
                {
                    'notification_id': str(uuid.uuid4()),
                    'notification_type': NotificationType.WEEKLY_PROGRESS_REPORT.value,
                    'channel': NotificationChannel.EMAIL.value,
                    'subject': 'Еженедельный отчет по коммуникациям',
                    'status': DeliveryStatus.DELIVERED.value,
                    'sent_at': (datetime.now() - timedelta(days=1)).isoformat(),
                    'delivered_at': (datetime.now() - timedelta(days=1)).isoformat()
                }
            ]
            
            # Фильтруем по типу уведомления если указан
            if notification_type:
                mock_history = [n for n in mock_history if n['notification_type'] == notification_type.value]
            
            return mock_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting notification history for user {user_id}: {e}")
            return []
    
    async def _send_single_notification(self, user_id: int, notification_type: NotificationType,
                                      channel: NotificationChannel, data: Dict[str, Any],
                                      preferences: NotificationPreferences) -> bool:
        """Отправка одного уведомления по конкретному каналу"""
        try:
            # Получаем шаблон
            template = self._get_template(notification_type, channel)
            if not template:
                logger.warning(f"No template found for {notification_type.value} via {channel.value}")
                return False
            
            # Рендерим шаблон
            rendered_content = self._render_template(template, data)
            
            # Создаем уведомление
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                priority=template.priority,
                subject=rendered_content['subject'],
                content=rendered_content['content'],
                data=data
            )
            
            # Отправляем в зависимости от канала
            success = False
            if channel == NotificationChannel.EMAIL:
                success = await self._send_email_notification(user_id, notification)
            elif channel == NotificationChannel.TELEGRAM:
                success = await self._send_telegram_notification(user_id, notification)
            elif channel == NotificationChannel.WEBHOOK:
                success = await self._send_webhook_notification(user_id, notification)
            
            # Обновляем статистику
            if success:
                self.delivery_stats['successful_deliveries'] += 1
                self.delivery_stats['channel_stats'][channel.value] += 1
                notification.delivery_status = DeliveryStatus.DELIVERED
                notification.delivered_at = datetime.now()
            else:
                self.delivery_stats['failed_deliveries'] += 1
                notification.delivery_status = DeliveryStatus.FAILED
                notification.error_message = "Delivery failed"
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending single notification: {e}")
            return False
    
    async def _send_email_notification(self, user_id: int, notification: Notification) -> bool:
        """Отправка email уведомления"""
        try:
            # Получаем email пользователя
            user_email = await self._get_user_email(user_id)
            if not user_email:
                logger.error(f"Email not found for user {user_id}")
                return False
            
            # Создаем email сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.subject
            msg['From'] = self.email_config['from_email']
            msg['To'] = user_email
            
            # Добавляем HTML контент
            html_content = MIMEText(notification.content, 'html', 'utf-8')
            msg.attach(html_content)
            
            # Отправляем email (симуляция)
            logger.info(f"Email notification sent to {user_email}: {notification.subject}")
            
            # В реальной реализации здесь будет отправка через SMTP
            # with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            #     server.starttls()
            #     server.login(self.email_config['username'], self.email_config['password'])
            #     server.send_message(msg)
            
            notification.sent_at = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    async def _send_telegram_notification(self, user_id: int, notification: Notification) -> bool:
        """Отправка Telegram уведомления"""
        try:
            # Получаем Telegram chat ID пользователя
            chat_id = await self._get_user_telegram_chat_id(user_id)
            if not chat_id:
                logger.error(f"Telegram chat ID not found for user {user_id}")
                return False
            
            # Подготавливаем сообщение
            message = f"*{notification.subject}*\n\n{notification.content}"
            
            # Отправляем в Telegram (симуляция)
            logger.info(f"Telegram notification sent to chat {chat_id}: {notification.subject}")
            
            # В реальной реализации здесь будет отправка через Telegram API
            # url = f"{self.telegram_config['api_url']}/sendMessage"
            # data = {
            #     'chat_id': chat_id,
            #     'text': message,
            #     'parse_mode': 'Markdown'
            # }
            # response = requests.post(url, data=data)
            # return response.status_code == 200
            
            notification.sent_at = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error sending telegram notification: {e}")
            return False
    
    async def _send_webhook_notification(self, user_id: int, notification: Notification) -> bool:
        """Отправка webhook уведомления"""
        try:
            # Получаем webhook URL пользователя
            webhook_url = await self._get_user_webhook_url(user_id)
            if not webhook_url:
                logger.error(f"Webhook URL not found for user {user_id}")
                return False
            
            # Подготавливаем данные для webhook
            payload = {
                'notification_id': notification.notification_id,
                'user_id': user_id,
                'type': notification.notification_type.value,
                'subject': notification.subject,
                'content': notification.content,
                'data': notification.data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Отправляем webhook (симуляция)
            logger.info(f"Webhook notification sent to {webhook_url}")
            
            # В реальной реализации здесь будет отправка через requests
            # response = requests.post(webhook_url, json=payload, timeout=10)
            # return response.status_code == 200
            
            notification.sent_at = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    def _get_template(self, notification_type: NotificationType, channel: NotificationChannel) -> Optional[NotificationTemplate]:
        """Получение шаблона уведомления"""
        template_key = f"{notification_type.value}_{channel.value}"
        return self.templates.get(template_key)
    
    def _render_template(self, template: NotificationTemplate, data: Dict[str, Any]) -> Dict[str, str]:
        """Рендеринг шаблона с данными"""
        try:
            rendered_subject = template.subject
            rendered_content = template.content
            
            # Заменяем переменные в шаблоне
            for variable in template.variables:
                value = data.get(variable, f"{{{{ {variable} }}}}")
                
                if isinstance(value, str):
                    rendered_subject = rendered_subject.replace(f"{{{{ {variable} }}}}", value)
                    rendered_content = rendered_content.replace(f"{{{{ {variable} }}}}", value)
            
            return {
                'subject': rendered_subject,
                'content': rendered_content
            }
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return {
                'subject': template.subject,
                'content': template.content
            }
    
    async def _get_user_preferences(self, user_id: int) -> NotificationPreferences:
        """Получение пользовательских настроек"""
        try:
            # Проверяем кэш
            if user_id in self.preferences_cache:
                return self.preferences_cache[user_id]
            
            # Получаем из базы данных (симуляция)
            preferences = NotificationPreferences(
                user_id=user_id,
                channels={
                    NotificationChannel.EMAIL: True,
                    NotificationChannel.TELEGRAM: True,
                    NotificationChannel.WEBHOOK: False
                },
                types={
                    NotificationType.NEW_FUND_RESPONSE: True,
                    NotificationType.MEETING_SCHEDULED: True,
                    NotificationType.COMMUNICATION_ESCALATED: True,
                    NotificationType.WEEKLY_PROGRESS_REPORT: True,
                    NotificationType.SYSTEM_ERROR: True,
                    NotificationType.FOLLOW_UP_REMINDER: False,
                    NotificationType.MEETING_REMINDER: True,
                    NotificationType.FUND_MATCH_FOUND: True,
                    NotificationType.COMMUNICATION_TIMEOUT: True,
                    NotificationType.SUCCESSFUL_CLOSURE: True
                },
                frequency={
                    NotificationType.NEW_FUND_RESPONSE: 'immediate',
                    NotificationType.MEETING_SCHEDULED: 'immediate',
                    NotificationType.COMMUNICATION_ESCALATED: 'immediate',
                    NotificationType.WEEKLY_PROGRESS_REPORT: 'weekly',
                    NotificationType.SYSTEM_ERROR: 'immediate',
                    NotificationType.FOLLOW_UP_REMINDER: 'daily',
                    NotificationType.MEETING_REMINDER: 'immediate',
                    NotificationType.FUND_MATCH_FOUND: 'immediate',
                    NotificationType.COMMUNICATION_TIMEOUT: 'immediate',
                    NotificationType.SUCCESSFUL_CLOSURE: 'immediate'
                },
                quiet_hours={'start_time': '22:00', 'end_time': '08:00'},
                batch_enabled=True,
                max_notifications_per_hour=10
            )
            
            # Сохраняем в кэш
            self.preferences_cache[user_id] = preferences
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            # Возвращаем настройки по умолчанию
            return NotificationPreferences(
                user_id=user_id,
                channels={channel: True for channel in NotificationChannel},
                types={notification_type: True for notification_type in NotificationType},
                frequency={notification_type: 'immediate' for notification_type in NotificationType}
            )
    
    def _get_available_channels(self, preferences: NotificationPreferences, 
                              notification_type: NotificationType) -> List[NotificationChannel]:
        """Получение доступных каналов для уведомления"""
        available_channels = []
        
        for channel, enabled in preferences.channels.items():
            if enabled:
                # Проверяем, есть ли шаблон для этого канала
                template_key = f"{notification_type.value}_{channel.value}"
                if template_key in self.templates:
                    available_channels.append(channel)
        
        return available_channels
    
    async def _should_send_notification(self, user_id: int, notification_type: NotificationType,
                                      channel: NotificationChannel, preferences: NotificationPreferences) -> bool:
        """Проверка, нужно ли отправлять уведомление"""
        try:
            # Проверяем, включен ли этот тип уведомлений
            if not preferences.types.get(notification_type, False):
                return False
            
            # Проверяем, включен ли этот канал
            if not preferences.channels.get(channel, False):
                return False
            
            # Проверяем quiet hours
            if self._is_quiet_time(preferences.quiet_hours):
                # Исключение для срочных уведомлений
                if notification_type not in [NotificationType.SYSTEM_ERROR, NotificationType.COMMUNICATION_ESCALATED]:
                    return False
            
            # Проверяем лимит уведомлений в час
            if preferences.max_notifications_per_hour > 0:
                recent_notifications = await self._count_recent_notifications(user_id, timedelta(hours=1))
                if recent_notifications >= preferences.max_notifications_per_hour:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if should send notification: {e}")
            return False
    
    def _is_quiet_time(self, quiet_hours: Dict[str, str]) -> bool:
        """Проверка, находимся ли мы в quiet hours"""
        try:
            if not quiet_hours or 'start_time' not in quiet_hours or 'end_time' not in quiet_hours:
                return False
            
            current_time = datetime.now().time()
            start_time = datetime.strptime(quiet_hours['start_time'], '%H:%M').time()
            end_time = datetime.strptime(quiet_hours['end_time'], '%H:%M').time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:  # Quiet hours span midnight
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet time: {e}")
            return False
    
    async def _count_recent_notifications(self, user_id: int, time_window: timedelta) -> int:
        """Подсчет недавних уведомлений"""
        # Симуляция подсчета из базы данных
        return 2  # Пример значения
    
    async def _get_user_email(self, user_id: int) -> Optional[str]:
        """Получение email пользователя"""
        try:
            db = next(get_db())
            user = db.query(Startup).filter(Startup.id == user_id).first()
            return user.email if user else None
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            return None
    
    async def _get_user_telegram_chat_id(self, user_id: int) -> Optional[str]:
        """Получение Telegram chat ID пользователя"""
        # Симуляция получения из базы данных
        return f"chat_{user_id}"
    
    async def _get_user_webhook_url(self, user_id: int) -> Optional[str]:
        """Получение webhook URL пользователя"""
        # Симуляция получения из базы данных
        return f"https://webhook.startup{user_id}.com/notifications"
    
    async def _save_user_preferences(self, user_id: int, preferences: NotificationPreferences):
        """Сохранение пользовательских настроек"""
        # Симуляция сохранения в базу данных
        logger.info(f"Saved preferences for user {user_id}")
    
    async def _generate_weekly_report_data(self, user_id: int) -> Dict[str, Any]:
        """Генерация данных для еженедельного отчета"""
        try:
            # Симуляция генерации данных
            return {
                'startup_contact': 'Иван Петров',
                'new_communications': 3,
                'responses_received': 2,
                'meetings_scheduled': 1,
                'successful_closures': 0,
                'awaiting_response': 5,
                'follow_up_needed': 2,
                'escalated': 1,
                'recommendations': [
                    'Продолжайте активную работу с фондом Innovation Ventures',
                    'Подготовьте дополнительные материалы для Growth Capital Partners',
                    'Рассмотрите возможность follow-up с Tech Ventures Fund'
                ]
            }
        except Exception as e:
            logger.error(f"Error generating weekly report data: {e}")
            return {}
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Получение статистики уведомлений"""
        return {
            'delivery_stats': self.delivery_stats.copy(),
            'templates_count': len(self.templates),
            'cached_preferences': len(self.preferences_cache),
            'batch_queue_size': len(self.batch_queue),
            'active_channels': [channel.value for channel in NotificationChannel],
            'active_notification_types': [nt.value for nt in NotificationType]
        }
    
    async def process_batch_notifications(self) -> int:
        """Обработка batch уведомлений"""
        try:
            if not self.batch_queue:
                return 0
            
            processed_count = 0
            current_time = datetime.now()
            
            # Фильтруем уведомления, готовые к отправке
            ready_notifications = [
                n for n in self.batch_queue
                if n.scheduled_at is None or n.scheduled_at <= current_time
            ]
            
            if not ready_notifications:
                return 0
            
            # Группируем по пользователям для batch отправки
            user_notifications = defaultdict(list)
            for notification in ready_notifications:
                user_notifications[notification.user_id].append(notification)
            
            # Отправляем batch уведомления
            for user_id, notifications in user_notifications.items():
                if len(notifications) > 1:
                    # Отправляем как batch
                    await self._send_batch_notifications(user_id, notifications)
                else:
                    # Отправляем по одному
                    await self._send_single_notification(
                        notifications[0].user_id,
                        notifications[0].notification_type,
                        notifications[0].channel,
                        notifications[0].data,
                        await self._get_user_preferences(notifications[0].user_id)
                    )
                
                processed_count += len(notifications)
            
            # Удаляем обработанные уведомления из очереди
            self.batch_queue = [n for n in self.batch_queue if n not in ready_notifications]
            
            logger.info(f"Processed {processed_count} batch notifications")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing batch notifications: {e}")
            return 0
    
    async def _send_batch_notifications(self, user_id: int, notifications: List[Notification]):
        """Отправка batch уведомлений пользователю"""
        try:
            # Получаем пользовательские настройки
            preferences = await self._get_user_preferences(user_id)
            
            # Группируем по каналам
            channel_notifications = defaultdict(list)
            for notification in notifications:
                channel_notifications[notification.channel].append(notification)
            
            # Отправляем по каналам
            for channel, channel_notifs in channel_notifications.items():
                if channel == NotificationChannel.EMAIL:
                    await self._send_batch_email(user_id, channel_notifs)
                elif channel == NotificationChannel.TELEGRAM:
                    await self._send_batch_telegram(user_id, channel_notifs)
            
            logger.info(f"Sent batch notifications to user {user_id}: {len(notifications)} notifications")
            
        except Exception as e:
            logger.error(f"Error sending batch notifications: {e}")
    
    async def _send_batch_email(self, user_id: int, notifications: List[Notification]):
        """Отправка batch email уведомлений"""
        try:
            user_email = await self._get_user_email(user_id)
            if not user_email:
                return
            
            # Создаем сводное email сообщение
            subject = f"📬 Уведомления ({len(notifications)} сообщений)"
            
            content = "<h2>Ваши уведомления</h2>\n"
            
            for notification in notifications:
                content += f"<div style='border-left: 3px solid #007bff; padding-left: 15px; margin: 15px 0;'>"
                content += f"<h3>{notification.subject}</h3>"
                content += f"<p>{notification.content}</p>"
                content += f"<small style='color: #666;'>Отправлено: {notification.created_at.strftime('%d.%m.%Y %H:%M')}</small>"
                content += "</div>"
            
            # Отправляем сводное сообщение
            logger.info(f"Batch email sent to {user_email}: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending batch email: {e}")
    
    async def _send_batch_telegram(self, user_id: int, notifications: List[Notification]):
        """Отправка batch Telegram уведомлений"""
        try:
            chat_id = await self._get_user_telegram_chat_id(user_id)
            if not chat_id:
                return
            
            # Создаем сводное Telegram сообщение
            message = f"📬 *Уведомления ({len(notifications)} сообщений)*\n\n"
            
            for notification in notifications:
                message += f"• *{notification.subject}*\n"
                message += f"_{notification.created_at.strftime('%d.%m.%Y %H:%M')}_\n\n"
            
            # Отправляем сводное сообщение
            logger.info(f"Batch telegram sent to chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending batch telegram: {e}")


# Глобальный экземпляр сервиса уведомлений
notification_service = NotificationService()
