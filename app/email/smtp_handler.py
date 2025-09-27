"""
SMTPHandler для отправки email через внешние провайдеры (SendGrid/Mailgun)
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

# Импорты для внешних провайдеров
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email as SGEmail, To, Content
except ImportError:
    sendgrid = None

try:
    import requests
except ImportError:
    requests = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Исключение для ошибок доставки email"""
    pass


class SMTPHandler:
    """Обработчик SMTP для отправки email через различные провайдеры"""
    
    def __init__(self, provider: str = "sendgrid"):
        self.provider = provider.lower()
        self.config = self._load_provider_config()
        self._validate_config()
    
    def _load_provider_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию провайдера"""
        if self.provider == "sendgrid":
            return {
                "api_key": os.getenv('SENDGRID_API_KEY') or getattr(settings, 'SENDGRID_API_KEY', None),
                "from_email": os.getenv('SENDGRID_FROM_EMAIL', 'noreply@startupconnect.com'),
                "from_name": os.getenv('SENDGRID_FROM_NAME', 'StartupConnect Platform')
            }
        elif self.provider == "mailgun":
            return {
                "api_key": os.getenv('MAILGUN_API_KEY') or getattr(settings, 'MAILGUN_API_KEY', None),
                "domain": os.getenv('MAILGUN_DOMAIN') or getattr(settings, 'MAILGUN_DOMAIN', None),
                "from_email": os.getenv('MAILGUN_FROM_EMAIL', 'noreply@startupconnect.com'),
                "from_name": os.getenv('MAILGUN_FROM_NAME', 'StartupConnect Platform')
            }
        elif self.provider == "smtp":
            return {
                "host": os.getenv('SMTP_HOST', 'localhost'),
                "port": int(os.getenv('SMTP_PORT', '587')),
                "username": os.getenv('SMTP_USERNAME'),
                "password": os.getenv('SMTP_PASSWORD'),
                "use_tls": os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
                "from_email": os.getenv('SMTP_FROM_EMAIL', 'noreply@startupconnect.com'),
                "from_name": os.getenv('SMTP_FROM_NAME', 'StartupConnect Platform')
            }
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")
    
    def _validate_config(self):
        """Валидирует конфигурацию провайдера"""
        if self.provider == "sendgrid":
            if not self.config.get('api_key'):
                logger.warning("SendGrid API key not configured")
        elif self.provider == "mailgun":
            if not self.config.get('api_key') or not self.config.get('domain'):
                logger.warning("Mailgun API key or domain not configured")
        elif self.provider == "smtp":
            if not self.config.get('host'):
                logger.warning("SMTP host not configured")
    
    def send_email(self, 
                   to_email: str,
                   subject: str,
                   body: str,
                   from_email: Optional[str] = None,
                   from_name: Optional[str] = None,
                   html_body: Optional[str] = None,
                   reply_to: Optional[str] = None,
                   attachments: Optional[List[Dict[str, Any]]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправляет email через выбранного провайдера
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            body: Текст письма
            from_email: Email отправителя (опционально)
            from_name: Имя отправителя (опционально)
            html_body: HTML версия письма (опционально)
            reply_to: Email для ответов (опционально)
            attachments: Список вложений (опционально)
            headers: Дополнительные заголовки (опционально)
            thread_id: ID треда для группировки (опционально)
        
        Returns:
            Dict с результатом отправки
        """
        
        try:
            # Используем конфигурацию по умолчанию если не указано
            sender_email = from_email or self.config['from_email']
            sender_name = from_name or self.config['from_name']
            
            # Генерируем уникальный Message-ID
            message_id = f"<{uuid.uuid4()}@startupconnect.com>"
            
            # Подготавливаем заголовки
            email_headers = headers or {}
            email_headers['Message-ID'] = message_id
            
            if thread_id:
                email_headers['In-Reply-To'] = thread_id
                email_headers['References'] = thread_id
            
            if reply_to:
                email_headers['Reply-To'] = reply_to
            
            # Отправляем через выбранного провайдера
            if self.provider == "sendgrid":
                result = self._send_via_sendgrid(
                    to_email, subject, body, sender_email, sender_name,
                    html_body, email_headers, attachments
                )
            elif self.provider == "mailgun":
                result = self._send_via_mailgun(
                    to_email, subject, body, sender_email, sender_name,
                    html_body, email_headers, attachments
                )
            elif self.provider == "smtp":
                result = self._send_via_smtp(
                    to_email, subject, body, sender_email, sender_name,
                    html_body, email_headers, attachments
                )
            else:
                raise EmailDeliveryError(f"Unsupported provider: {self.provider}")
            
            # Добавляем общие метаданные
            result.update({
                'message_id': message_id,
                'provider': self.provider,
                'sent_at': datetime.now().isoformat(),
                'to_email': to_email,
                'subject': subject
            })
            
            logger.info(f"Email sent successfully via {self.provider}: {message_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email via {self.provider}: {e}")
            raise EmailDeliveryError(f"Email delivery failed: {str(e)}")
    
    def _send_via_sendgrid(self, to_email: str, subject: str, body: str,
                          from_email: str, from_name: str, html_body: Optional[str],
                          headers: Dict[str, str], attachments: Optional[List]) -> Dict[str, Any]:
        """Отправка через SendGrid API"""
        if not sendgrid or not self.config.get('api_key'):
            raise EmailDeliveryError("SendGrid not configured or library not installed")
        
        try:
            sg = sendgrid.SendGridAPIClient(api_key=self.config['api_key'])
            
            from_email_obj = SGEmail(from_email, from_name)
            to_email_obj = To(to_email)
            
            # Создаем письмо
            if html_body:
                content = Content("text/html", html_body)
                mail = Mail(from_email_obj, to_email_obj, subject, plain_text_content=Content("text/plain", body))
                mail.add_content(content)
            else:
                content = Content("text/plain", body)
                mail = Mail(from_email_obj, to_email_obj, subject, content)
            
            # Добавляем кастомные заголовки
            if headers:
                for key, value in headers.items():
                    mail.add_header({key: value})
            
            # Добавляем вложения (если есть)
            if attachments:
                for attachment in attachments:
                    # Логика добавления вложений для SendGrid
                    pass
            
            # Отправляем
            response = sg.send(mail)
            
            return {
                'status': 'sent',
                'provider_response': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.body
                },
                'delivery_status': 'accepted' if response.status_code == 202 else 'failed'
            }
            
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            raise EmailDeliveryError(f"SendGrid delivery failed: {str(e)}")
    
    def _send_via_mailgun(self, to_email: str, subject: str, body: str,
                         from_email: str, from_name: str, html_body: Optional[str],
                         headers: Dict[str, str], attachments: Optional[List]) -> Dict[str, Any]:
        """Отправка через Mailgun API"""
        if not requests or not self.config.get('api_key') or not self.config.get('domain'):
            raise EmailDeliveryError("Mailgun not configured or requests library not installed")
        
        try:
            url = f"https://api.mailgun.net/v3/{self.config['domain']}/messages"
            
            # Подготавливаем данные
            data = {
                'from': f"{from_name} <{from_email}>",
                'to': to_email,
                'subject': subject,
                'text': body
            }
            
            if html_body:
                data['html'] = html_body
            
            # Добавляем кастомные заголовки
            if headers:
                for key, value in headers.items():
                    data[f'h:{key}'] = value
            
            # Отправляем запрос
            response = requests.post(
                url,
                auth=('api', self.config['api_key']),
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            return {
                'status': 'sent',
                'provider_response': response_data,
                'delivery_status': 'accepted',
                'provider_message_id': response_data.get('id')
            }
            
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            raise EmailDeliveryError(f"Mailgun delivery failed: {str(e)}")
    
    def _send_via_smtp(self, to_email: str, subject: str, body: str,
                      from_email: str, from_name: str, html_body: Optional[str],
                      headers: Dict[str, str], attachments: Optional[List]) -> Dict[str, Any]:
        """Отправка через SMTP сервер"""
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            
            # Добавляем кастомные заголовки
            if headers:
                for key, value in headers.items():
                    msg[key] = value
            
            # Добавляем текстовое содержимое
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Добавляем вложения
            if attachments:
                for attachment in attachments:
                    # Логика добавления вложений
                    pass
            
            # Подключаемся к SMTP серверу
            server = smtplib.SMTP(self.config['host'], self.config['port'])
            
            if self.config.get('use_tls'):
                server.starttls()
            
            if self.config.get('username') and self.config.get('password'):
                server.login(self.config['username'], self.config['password'])
            
            # Отправляем
            server.send_message(msg)
            server.quit()
            
            return {
                'status': 'sent',
                'provider_response': {'smtp_server': self.config['host']},
                'delivery_status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise EmailDeliveryError(f"SMTP delivery failed: {str(e)}")
    
    def verify_delivery_status(self, provider_message_id: str) -> Dict[str, Any]:
        """Проверяет статус доставки сообщения"""
        try:
            if self.provider == "sendgrid":
                return self._check_sendgrid_status(provider_message_id)
            elif self.provider == "mailgun":
                return self._check_mailgun_status(provider_message_id)
            else:
                return {'status': 'unknown', 'reason': 'Status checking not supported for this provider'}
        except Exception as e:
            logger.error(f"Failed to check delivery status: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _check_sendgrid_status(self, message_id: str) -> Dict[str, Any]:
        """Проверяет статус в SendGrid"""
        # Реализация проверки статуса через SendGrid API
        return {'status': 'pending', 'reason': 'Status checking not implemented yet'}
    
    def _check_mailgun_status(self, message_id: str) -> Dict[str, Any]:
        """Проверяет статус в Mailgun"""
        # Реализация проверки статуса через Mailgun API
        return {'status': 'pending', 'reason': 'Status checking not implemented yet'}
    
    def handle_webhook(self, provider: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает webhook от провайдера для обновления статуса"""
        try:
            if provider == "sendgrid":
                return self._process_sendgrid_webhook(webhook_data)
            elif provider == "mailgun":
                return self._process_mailgun_webhook(webhook_data)
            else:
                return {'status': 'error', 'reason': f'Unsupported webhook provider: {provider}'}
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _process_sendgrid_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает webhook от SendGrid"""
        # Реализация обработки SendGrid webhook
        return {'status': 'processed', 'events': []}
    
    def _process_mailgun_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает webhook от Mailgun"""
        # Реализация обработки Mailgun webhook
        return {'status': 'processed', 'events': []}


# Создаем глобальный экземпляр
smtp_handler = SMTPHandler()
