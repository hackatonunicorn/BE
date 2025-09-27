"""
EmailGateway - основной класс для управления email коммуникациями
"""
import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import uuid
import asyncio
from sqlalchemy.orm import Session

from app.email.smtp_handler import smtp_handler, EmailDeliveryError
from app.email.imap_handler import imap_handler, IMAPConnectionError
from app.email.email_parser import email_parser
from app.core.database import get_db
from app.data.models import Email, EmailThread, Communication, Startup, VCFund

logger = logging.getLogger(__name__)


class EmailGatewayError(Exception):
    """Базовое исключение для EmailGateway"""
    pass


class EmailGateway:
    """
    Основной шлюз для управления email коммуникациями между стартапами и ВК
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self.smtp_handler = smtp_handler
        self.imap_handler = imap_handler
        self.email_parser = email_parser
        
        # Настройки прокси-email
        self.proxy_email_domain = os.getenv('PROXY_EMAIL_DOMAIN', 'startup-connect.com')
        self.system_email = os.getenv('SYSTEM_EMAIL', 'system@startup-connect.com')
        
        logger.info("EmailGateway initialized")
    
    def send_email(self, 
                   to: str,
                   subject: str,
                   body: str,
                   startup_context: Dict[str, Any],
                   html_body: Optional[str] = None,
                   thread_id: Optional[str] = None,
                   schedule_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Отправляет email от имени стартапа через прокси-email
        
        Args:
            to: Email получателя (ВК)
            subject: Тема письма
            body: Содержимое письма
            startup_context: Контекст стартапа (id, name, email, etc.)
            html_body: HTML версия письма (опционально)
            thread_id: ID треда для группировки (опционально)
            schedule_at: Время отправки (опционально, для отложенной отправки)
        
        Returns:
            Dict с результатом отправки и метаданными
        """
        try:
            # Получаем или создаем сессию БД
            if not self.db:
                self.db = next(get_db())
            
            # Извлекаем данные стартапа
            startup_id = startup_context.get('id')
            startup_name = startup_context.get('name', 'Startup')
            startup_email = startup_context.get('email', '')
            contact_person = startup_context.get('contact_person', 'Founder')
            
            # Генерируем прокси-email для стартапа
            proxy_email = self._generate_proxy_email(startup_id, startup_name)
            
            # Настраиваем Reply-To на реальный email стартапа
            reply_to = startup_email if startup_email else proxy_email
            
            # Подготавливаем заголовки
            headers = {
                'X-Startup-ID': str(startup_id),
                'X-Startup-Name': startup_name,
                'X-Original-Sender': startup_email,
                'Reply-To': reply_to
            }
            
            # Если это часть треда, добавляем связанные заголовки
            if thread_id:
                headers['In-Reply-To'] = f'<{thread_id}>'
                headers['References'] = f'<{thread_id}>'
            
            # Персонализируем подпись
            signature = self._create_email_signature(contact_person, startup_name, startup_email)
            full_body = f"{body}\n\n{signature}"
            
            if html_body:
                html_signature = self._create_html_signature(contact_person, startup_name, startup_email)
                html_body = f"{html_body}<br><br>{html_signature}"
            
            # Отправляем email
            send_result = self.smtp_handler.send_email(
                to_email=to,
                subject=subject,
                body=full_body,
                from_email=proxy_email,
                from_name=f"{contact_person} from {startup_name}",
                html_body=html_body,
                reply_to=reply_to,
                headers=headers,
                thread_id=thread_id
            )
            
            # Сохраняем в БД
            email_record = self._save_outbound_email(
                send_result, startup_context, to, subject, full_body, html_body, thread_id
            )
            
            logger.info(f"Email sent successfully from {proxy_email} to {to}")
            
            return {
                'status': 'sent',
                'email_id': email_record.id,
                'message_id': send_result.get('message_id'),
                'proxy_email': proxy_email,
                'thread_id': thread_id or send_result.get('message_id'),
                'send_result': send_result,
                'scheduled_at': schedule_at.isoformat() if schedule_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise EmailGatewayError(f"Email sending failed: {str(e)}")
    
    def receive_emails(self, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получает и обрабатывает входящие emails
        
        Args:
            since_date: Дата, с которой получать письма (по умолчанию - последний час)
        
        Returns:
            Список обработанных emails
        """
        try:
            # Получаем raw emails из IMAP
            raw_emails = self.imap_handler.fetch_new_emails(since_date)
            
            if not raw_emails:
                logger.info("No new emails received")
                return []
            
            processed_emails = []
            
            for raw_email in raw_emails:
                try:
                    # Парсим email
                    parsed_email = self.email_parser.parse_email_content(raw_email)
                    
                    # Проверяем, не bounce ли это
                    if parsed_email.get('bounce_detected'):
                        self._handle_bounce_email(parsed_email)
                        continue
                    
                    # Проверяем, не автоответ ли это
                    if parsed_email.get('auto_reply_detected'):
                        self._handle_auto_reply(parsed_email)
                        # Но все равно сохраняем для истории
                    
                    # Сохраняем в БД
                    email_record = self._save_inbound_email(parsed_email)
                    
                    # Добавляем к результату
                    processed_emails.append({
                        'email_id': email_record.id,
                        'parsed_data': parsed_email,
                        'classification': parsed_email.get('classification'),
                        'requires_action': self._requires_action(parsed_email)
                    })
                    
                    logger.info(f"Processed inbound email: {parsed_email.get('message_id')}")
                    
                except Exception as e:
                    logger.error(f"Error processing email: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_emails)} emails")
            return processed_emails
            
        except Exception as e:
            logger.error(f"Failed to receive emails: {e}")
            raise EmailGatewayError(f"Email receiving failed: {str(e)}")
    
    def parse_reply(self, email_content: Dict[str, Any], original_thread_id: str) -> Dict[str, Any]:
        """
        Парсит ответ на отправленное письмо
        
        Args:
            email_content: Содержимое email
            original_thread_id: ID оригинального треда
        
        Returns:
            Словарь с результатами парсинга
        """
        try:
            # Парсим email
            parsed_email = self.email_parser.parse_email_content(email_content)
            
            # Извлекаем thread_id из ответа
            thread_id = self.email_parser.extract_thread_id_from_reply(
                email_content, original_thread_id
            )
            
            # Находим связанный тред в БД
            email_thread = self._find_or_create_thread(thread_id, parsed_email)
            
            # Обновляем статистику треда
            self._update_thread_stats(email_thread, parsed_email)
            
            # Определяем необходимые действия
            suggested_actions = self._suggest_actions_for_reply(parsed_email)
            
            return {
                'thread_id': thread_id,
                'email_thread_id': email_thread.id,
                'parsed_email': parsed_email,
                'classification': parsed_email.get('classification'),
                'suggested_actions': suggested_actions,
                'requires_human_review': self._requires_human_review(parsed_email),
                'auto_reply_detected': parsed_email.get('auto_reply_detected', False),
                'bounce_detected': parsed_email.get('bounce_detected', False)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse reply: {e}")
            raise EmailGatewayError(f"Reply parsing failed: {str(e)}")
    
    def update_thread_status(self, thread_id: str, status: str, notes: Optional[str] = None) -> bool:
        """
        Обновляет статус email треда
        
        Args:
            thread_id: ID треда
            status: Новый статус (active, closed, bounced, error)
            notes: Дополнительные заметки
        
        Returns:
            True если обновление успешно
        """
        try:
            if not self.db:
                self.db = next(get_db())
            
            # Находим тред
            email_thread = self.db.query(EmailThread).filter(
                EmailThread.thread_id == thread_id
            ).first()
            
            if not email_thread:
                logger.error(f"Thread not found: {thread_id}")
                return False
            
            # Обновляем статус
            email_thread.status = status
            email_thread.updated_at = datetime.now()
            
            # Если есть связанная коммуникация, обновляем и её
            if email_thread.communication_id:
                communication = self.db.query(Communication).filter(
                    Communication.id == email_thread.communication_id
                ).first()
                
                if communication:
                    # Обновляем статус коммуникации в зависимости от статуса треда
                    if status == 'closed':
                        communication.status = 'closed'
                    elif status == 'bounced' or status == 'error':
                        communication.status = 'failed'
                        communication.escalated_to_human = True
                    
                    communication.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Thread status updated: {thread_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update thread status: {e}")
            if self.db:
                self.db.rollback()
            return False
    
    def get_thread_emails(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает все emails в треде"""
        try:
            if not self.db:
                self.db = next(get_db())
            
            # Находим тред
            email_thread = self.db.query(EmailThread).filter(
                EmailThread.thread_id == thread_id
            ).first()
            
            if not email_thread:
                return []
            
            # Получаем emails из БД
            emails = self.db.query(Email).filter(
                Email.email_thread_id == email_thread.id
            ).order_by(Email.created_at.desc()).limit(limit).all()
            
            result = []
            for email_record in emails:
                result.append({
                    'id': email_record.id,
                    'message_id': email_record.message_id,
                    'sender_email': email_record.sender_email,
                    'recipient_email': email_record.recipient_email,
                    'subject': email_record.subject,
                    'body': email_record.body,
                    'direction': email_record.direction,
                    'status': email_record.status,
                    'sent_at': email_record.sent_at.isoformat() if email_record.sent_at else None,
                    'created_at': email_record.created_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get thread emails: {e}")
            return []
    
    def handle_delivery_status(self, message_id: str, status: str, details: Dict[str, Any]) -> bool:
        """Обрабатывает обновления статуса доставки от провайдера"""
        try:
            if not self.db:
                self.db = next(get_db())
            
            # Находим email по message_id
            email_record = self.db.query(Email).filter(
                Email.message_id == message_id
            ).first()
            
            if not email_record:
                logger.warning(f"Email not found for message_id: {message_id}")
                return False
            
            # Обновляем статус
            email_record.status = status
            email_record.delivery_status = details
            email_record.updated_at = datetime.now()
            
            # Обновляем временные метки в зависимости от статуса
            if status == 'delivered':
                email_record.delivered_at = datetime.now()
            elif status == 'opened':
                email_record.opened_at = datetime.now()
            elif status == 'clicked':
                email_record.clicked_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Email status updated: {message_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle delivery status: {e}")
            if self.db:
                self.db.rollback()
            return False
    
    def _generate_proxy_email(self, startup_id: int, startup_name: str) -> str:
        """Генерирует прокси-email для стартапа"""
        # Очищаем имя стартапа для использования в email
        clean_name = ''.join(c for c in startup_name.lower() if c.isalnum())[:20]
        return f"{clean_name}.{startup_id}@{self.proxy_email_domain}"
    
    def _create_email_signature(self, contact_person: str, startup_name: str, email: str) -> str:
        """Создает текстовую подпись для email"""
        return f"""--
{contact_person}
{startup_name}
{email}

Sent via StartupConnect Platform"""
    
    def _create_html_signature(self, contact_person: str, startup_name: str, email: str) -> str:
        """Создает HTML подпись для email"""
        return f"""<div style="border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px; color: #666;">
<strong>{contact_person}</strong><br>
{startup_name}<br>
<a href="mailto:{email}">{email}</a><br><br>
<small>Sent via StartupConnect Platform</small>
</div>"""
    
    def _save_outbound_email(self, send_result: Dict[str, Any], startup_context: Dict[str, Any],
                           to: str, subject: str, body: str, html_body: Optional[str],
                           thread_id: Optional[str]) -> Email:
        """Сохраняет исходящий email в БД"""
        try:
            if not self.db:
                self.db = next(get_db())
            
            # Находим или создаем тред
            email_thread = self._find_or_create_thread_for_outbound(
                thread_id or send_result.get('message_id'), 
                startup_context, to, subject
            )
            
            # Создаем запись email
            email_record = Email(
                email_thread_id=email_thread.id,
                message_id=send_result.get('message_id', ''),
                sender_email=send_result.get('from_email', ''),
                recipient_email=to,
                subject=subject,
                body=body,
                html_body=html_body,
                direction='outbound',
                status='sent' if send_result.get('status') == 'sent' else 'pending',
                delivery_status=send_result.get('provider_response', {}),
                headers=send_result.get('headers', {}),
                sent_at=datetime.now() if send_result.get('status') == 'sent' else None
            )
            
            self.db.add(email_record)
            self.db.commit()
            self.db.refresh(email_record)
            
            # Обновляем статистику треда
            email_thread.total_emails += 1
            email_thread.last_email_at = datetime.now()
            self.db.commit()
            
            return email_record
            
        except Exception as e:
            logger.error(f"Failed to save outbound email: {e}")
            if self.db:
                self.db.rollback()
            raise
    
    def _save_inbound_email(self, parsed_email: Dict[str, Any]) -> Email:
        """Сохраняет входящий email в БД"""
        try:
            if not self.db:
                self.db = next(get_db())
            
            # Находим или создаем тред
            thread_id = parsed_email.get('thread_info', {}).get('conversation_id', '')
            email_thread = self._find_or_create_thread(thread_id, parsed_email)
            
            # Создаем запись email
            email_record = Email(
                email_thread_id=email_thread.id,
                message_id=parsed_email.get('message_id', ''),
                sender_email=parsed_email.get('sender_email', ''),
                recipient_email=parsed_email.get('recipient_email', ''),
                subject=parsed_email.get('subject', ''),
                body=parsed_email.get('clean_body', ''),
                html_body=parsed_email.get('html_body', ''),
                direction='inbound',
                status='received',
                headers=parsed_email.get('headers', {}),
                attachments=parsed_email.get('attachments', [])
            )
            
            self.db.add(email_record)
            self.db.commit()
            self.db.refresh(email_record)
            
            # Обновляем статистику треда
            email_thread.total_emails += 1
            email_thread.last_email_at = datetime.now()
            self.db.commit()
            
            return email_record
            
        except Exception as e:
            logger.error(f"Failed to save inbound email: {e}")
            if self.db:
                self.db.rollback()
            raise
    
    def _find_or_create_thread(self, thread_id: str, parsed_email: Dict[str, Any]) -> EmailThread:
        """Находит или создает email тред"""
        if not self.db:
            self.db = next(get_db())
        
        # Пытаемся найти существующий тред
        email_thread = self.db.query(EmailThread).filter(
            EmailThread.thread_id == thread_id
        ).first()
        
        if email_thread:
            return email_thread
        
        # Создаем новый тред
        email_thread = EmailThread(
            thread_id=thread_id,
            communication_id=None,  # Будет связано позже
            subject=parsed_email.get('subject', ''),
            status='active',
            total_emails=0,
            last_email_at=datetime.now()
        )
        
        self.db.add(email_thread)
        self.db.commit()
        self.db.refresh(email_thread)
        
        return email_thread
    
    def _find_or_create_thread_for_outbound(self, thread_id: str, startup_context: Dict[str, Any],
                                          to: str, subject: str) -> EmailThread:
        """Находит или создает тред для исходящего email"""
        if not self.db:
            self.db = next(get_db())
        
        # Пытаемся найти существующий тред
        email_thread = self.db.query(EmailThread).filter(
            EmailThread.thread_id == thread_id
        ).first()
        
        if email_thread:
            return email_thread
        
        # Создаем новый тред
        email_thread = EmailThread(
            thread_id=thread_id,
            communication_id=None,  # Может быть связано с Communication
            subject=subject,
            status='active',
            total_emails=0,
            last_email_at=datetime.now()
        )
        
        self.db.add(email_thread)
        self.db.commit()
        self.db.refresh(email_thread)
        
        return email_thread
    
    def _update_thread_stats(self, email_thread: EmailThread, parsed_email: Dict[str, Any]):
        """Обновляет статистику треда"""
        email_thread.total_emails += 1
        email_thread.last_email_at = datetime.now()
        email_thread.updated_at = datetime.now()
        
        # Обновляем статус треда на основе классификации
        classification = parsed_email.get('classification', {})
        if classification:
            if classification.get('classification') == 'not_interested':
                email_thread.status = 'closed'
            elif classification.get('classification') == 'out_of_office':
                # Не меняем статус для автоответов
                pass
        
        self.db.commit()
    
    def _handle_bounce_email(self, parsed_email: Dict[str, Any]):
        """Обрабатывает bounce email"""
        logger.warning(f"Bounce email detected: {parsed_email.get('message_id')}")
        
        # Ищем оригинальный email и обновляем его статус
        # Логика поиска по thread_id или другим идентификаторам
        # Обновляем статус треда на 'bounced'
        pass
    
    def _handle_auto_reply(self, parsed_email: Dict[str, Any]):
        """Обрабатывает автоответ"""
        logger.info(f"Auto-reply detected: {parsed_email.get('message_id')}")
        
        # Логируем автоответ, но не требуем человеческого вмешательства
        # Возможно, планируем повторную отправку после указанной даты
        pass
    
    def _requires_action(self, parsed_email: Dict[str, Any]) -> bool:
        """Определяет, требует ли email действий"""
        classification = parsed_email.get('classification', {})
        
        if not classification:
            return True  # Неклассифицированные требуют внимания
        
        action_required_types = ['interested', 'meeting_request', 'request_more_info']
        return classification.get('classification') in action_required_types
    
    def _requires_human_review(self, parsed_email: Dict[str, Any]) -> bool:
        """Определяет, требует ли email человеческого обзора"""
        classification = parsed_email.get('classification', {})
        
        if not classification:
            return True
        
        return classification.get('requires_human_review', False)
    
    def _suggest_actions_for_reply(self, parsed_email: Dict[str, Any]) -> List[str]:
        """Предлагает действия на основе классификации ответа"""
        classification = parsed_email.get('classification', {})
        
        if not classification:
            return ['Manual review required']
        
        suggested_action = classification.get('suggested_action', '')
        
        if suggested_action:
            return [suggested_action]
        
        return ['No specific action suggested']


# Создаем глобальный экземпляр
email_gateway = EmailGateway()
