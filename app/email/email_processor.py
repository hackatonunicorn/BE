"""
EmailProcessor - автоматизированный pipeline для обработки email коммуникаций
"""
import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import json

from app.email.email_gateway import email_gateway, EmailGatewayError
from app.email.imap_handler import imap_handler
from app.email.email_parser import email_parser
from app.core.database import get_db
from app.data.models import Email, EmailThread, Communication, Startup, VCFund
from app.data.repositories import get_email_repository, get_email_thread_repository, communication_repository

# Импорт AI компонентов
try:
    from app.ai.response_classifier import response_classifier
    from app.ai.email_generator import email_generator
except ImportError:
    response_classifier = None
    email_generator = None

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Статусы обработки email"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    ESCALATED = "escalated"


class ActionType(Enum):
    """Типы действий после обработки"""
    NO_ACTION = "no_action"
    SEND_FOLLOW_UP = "send_follow_up"
    SCHEDULE_MEETING = "schedule_meeting"
    SEND_DOCUMENTS = "send_documents"
    UPDATE_STATUS = "update_status"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    CLOSE_THREAD = "close_thread"


@dataclass
class EmailProcessingResult:
    """Результат обработки email"""
    email_id: str
    status: ProcessingStatus
    action_taken: ActionType
    classification: Optional[Dict[str, Any]] = None
    generated_response: Optional[Dict[str, Any]] = None
    escalation_reason: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processed_at: Optional[datetime] = None


@dataclass
class EscalationTrigger:
    """Триггеры для эскалации"""
    meeting_request: bool = False
    document_request: bool = False
    rejection: bool = False
    urgent_keywords: bool = False
    low_confidence: bool = False
    error_occurred: bool = False


class EmailProcessor:
    """
    Автоматизированный процессор для обработки email коммуникаций
    """
    
    def __init__(self):
        self.email_gateway = email_gateway
        self.imap_handler = imap_handler
        self.email_parser = email_parser
        self.response_classifier = response_classifier
        self.email_generator = email_generator
        
        # Настройки обработки
        self.processing_interval = int(os.getenv('EMAIL_PROCESSING_INTERVAL', '300'))  # 5 минут
        self.max_retries = int(os.getenv('EMAIL_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('EMAIL_RETRY_DELAY', '60'))  # 1 минута
        
        # Триггеры эскалации
        self.escalation_keywords = [
            'urgent', 'asap', 'immediately', 'emergency',
            'legal', 'lawsuit', 'contract', 'agreement',
            'investment', 'funding', 'term sheet', 'due diligence'
        ]
        
        logger.info("EmailProcessor initialized")
    
    async def process_incoming_emails(self) -> List[EmailProcessingResult]:
        """
        Основной метод обработки входящих emails
        """
        results = []
        
        try:
            logger.info("Starting email processing pipeline")
            
            # Шаг 1: Получение новых emails
            new_emails = await self._fetch_new_emails()
            logger.info(f"Found {len(new_emails)} new emails to process")
            
            for email_data in new_emails:
                try:
                    # Обработка каждого email
                    result = await self._process_single_email(email_data)
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('message_id', 'unknown')}: {e}")
                    
                    # Создаем результат с ошибкой
                    error_result = EmailProcessingResult(
                        email_id=email_data.get('message_id', 'unknown'),
                        status=ProcessingStatus.FAILED,
                        action_taken=ActionType.ESCALATE_TO_HUMAN,
                        error_message=str(e),
                        escalation_reason="Processing error"
                    )
                    results.append(error_result)
            
            # Обновляем статистику
            await self._update_processing_statistics(results)
            
            logger.info(f"Email processing completed. Processed {len(results)} emails")
            return results
            
        except Exception as e:
            logger.error(f"Critical error in email processing pipeline: {e}")
            raise EmailGatewayError(f"Email processing pipeline failed: {str(e)}")
    
    async def _fetch_new_emails(self) -> List[Dict[str, Any]]:
        """Получение новых emails из IMAP"""
        try:
            # Получаем emails за последний час
            since_date = datetime.now() - timedelta(hours=1)
            emails = self.imap_handler.fetch_new_emails(since_date)
            
            # Фильтруем уже обработанные emails
            processed_emails = await self._get_processed_email_ids()
            new_emails = [
                email for email in emails 
                if email.get('message_id') not in processed_emails
            ]
            
            return new_emails
            
        except Exception as e:
            logger.error(f"Error fetching new emails: {e}")
            return []
    
    async def _process_single_email(self, email_data: Dict[str, Any]) -> EmailProcessingResult:
        """
        Обработка одного email через весь pipeline
        """
        message_id = email_data.get('message_id', '')
        
        try:
            logger.info(f"Processing email: {message_id}")
            
            # Шаг 2: Парсинг содержимого
            parsed_email = self.email_parser.parse_email_content(email_data)
            
            # Шаг 3: Классификация ответа
            classification = await self._classify_response(parsed_email)
            
            # Шаг 4: Определение следующего действия
            action_type, escalation_trigger = await self._determine_next_action(
                parsed_email, classification
            )
            
            # Шаг 5: Генерация ответа (если нужно)
            generated_response = None
            if action_type in [ActionType.SEND_FOLLOW_UP, ActionType.SEND_DOCUMENTS]:
                generated_response = await self._generate_response(
                    parsed_email, classification, action_type
                )
            
            # Шаг 6: Обновление базы данных
            await self._update_database(parsed_email, classification, action_type)
            
            # Шаг 7: Отправка уведомлений (если нужно)
            if escalation_trigger.any_triggered() or action_type == ActionType.ESCALATE_TO_HUMAN:
                await self._send_escalation_notification(parsed_email, escalation_trigger)
            
            result = EmailProcessingResult(
                email_id=message_id,
                status=ProcessingStatus.COMPLETED,
                action_taken=action_type,
                classification=classification,
                generated_response=generated_response,
                processed_at=datetime.now()
            )
            
            logger.info(f"Successfully processed email: {message_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}")
            
            return EmailProcessingResult(
                email_id=message_id,
                status=ProcessingStatus.FAILED,
                action_taken=ActionType.ESCALATE_TO_HUMAN,
                error_message=str(e),
                escalation_reason="Processing error"
            )
    
    async def _classify_response(self, parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """Классификация ответа с использованием AI"""
        try:
            if not self.response_classifier:
                # Fallback классификация
                return self._fallback_classification(parsed_email)
            
            clean_body = parsed_email.get('clean_body', '')
            if len(clean_body) < 10:
                return {
                    'classification': 'unclear',
                    'confidence': 0.3,
                    'reasoning': 'Insufficient content for classification'
                }
            
            # Контекст для классификации
            context = {
                'sender_email': parsed_email.get('sender_email', ''),
                'sender_name': parsed_email.get('sender_name', ''),
                'subject': parsed_email.get('subject', ''),
                'is_auto_reply': parsed_email.get('auto_reply_detected', False)
            }
            
            # Используем ResponseClassifier
            classification = self.response_classifier.classify_response_sync(clean_body, context)
            
            return classification
            
        except Exception as e:
            logger.error(f"Error in response classification: {e}")
            return self._fallback_classification(parsed_email)
    
    def _fallback_classification(self, parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback классификация без AI"""
        body = parsed_email.get('clean_body', '').lower()
        subject = parsed_email.get('subject', '').lower()
        
        # Простая rule-based классификация
        if any(word in body for word in ['interested', 'would like to', 'please send', 'schedule']):
            return {
                'classification': 'interested',
                'confidence': 0.7,
                'reasoning': 'Contains interest indicators'
            }
        elif any(word in body for word in ['not a fit', 'decline', 'pass', 'not interested']):
            return {
                'classification': 'not_interested',
                'confidence': 0.8,
                'reasoning': 'Contains rejection indicators'
            }
        elif any(word in body for word in ['send', 'provide', 'share', 'deck', 'materials']):
            return {
                'classification': 'request_more_info',
                'confidence': 0.75,
                'reasoning': 'Requests additional information'
            }
        elif any(word in body for word in ['meeting', 'call', 'schedule', 'coffee']):
            return {
                'classification': 'meeting_request',
                'confidence': 0.8,
                'reasoning': 'Requests meeting or call'
            }
        else:
            return {
                'classification': 'unclear',
                'confidence': 0.4,
                'reasoning': 'No clear classification indicators'
            }
    
    async def _determine_next_action(self, parsed_email: Dict[str, Any], 
                                   classification: Dict[str, Any]) -> Tuple[ActionType, EscalationTrigger]:
        """Определение следующего действия на основе классификации"""
        
        escalation_trigger = EscalationTrigger()
        classification_type = classification.get('classification', 'unclear')
        confidence = classification.get('confidence', 0.0)
        
        # Проверяем триггеры эскалации
        body = parsed_email.get('clean_body', '').lower()
        
        # Ургентные ключевые слова
        if any(keyword in body for keyword in self.escalation_keywords):
            escalation_trigger.urgent_keywords = True
        
        # Низкая уверенность в классификации
        if confidence < 0.6:
            escalation_trigger.low_confidence = True
        
        # Определяем действие на основе классификации
        if classification_type == 'meeting_request':
            escalation_trigger.meeting_request = True
            return ActionType.SCHEDULE_MEETING, escalation_trigger
        
        elif classification_type == 'request_more_info':
            escalation_trigger.document_request = True
            return ActionType.SEND_DOCUMENTS, escalation_trigger
        
        elif classification_type == 'interested':
            return ActionType.SEND_FOLLOW_UP, escalation_trigger
        
        elif classification_type == 'not_interested':
            escalation_trigger.rejection = True
            return ActionType.CLOSE_THREAD, escalation_trigger
        
        elif classification_type == 'out_of_office':
            return ActionType.NO_ACTION, escalation_trigger
        
        elif classification_type == 'unclear' or escalation_trigger.any_triggered():
            return ActionType.ESCALATE_TO_HUMAN, escalation_trigger
        
        else:
            return ActionType.UPDATE_STATUS, escalation_trigger
    
    async def _generate_response(self, parsed_email: Dict[str, Any], 
                               classification: Dict[str, Any], action_type: ActionType) -> Optional[Dict[str, Any]]:
        """Генерация ответа на основе классификации"""
        try:
            if not self.email_generator:
                logger.warning("EmailGenerator not available, skipping response generation")
                return None
            
            # Извлекаем информацию о стартапе и ВК из email
            startup_info, vc_info = await self._extract_startup_vc_info(parsed_email)
            
            if not startup_info or not vc_info:
                logger.warning("Could not extract startup/VC info for response generation")
                return None
            
            # Генерируем соответствующий ответ
            if action_type == ActionType.SEND_FOLLOW_UP:
                response = await self._generate_follow_up_response(
                    startup_info, vc_info, classification, parsed_email
                )
            elif action_type == ActionType.SEND_DOCUMENTS:
                response = await self._generate_document_response(
                    startup_info, vc_info, classification, parsed_email
                )
            else:
                response = None
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    async def _generate_follow_up_response(self, startup_info: Dict[str, Any], 
                                         vc_info: Dict[str, Any], 
                                         classification: Dict[str, Any],
                                         parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация follow-up ответа"""
        
        # Определяем контекст предыдущего взаимодействия
        previous_context = parsed_email.get('quoted_text', '')
        vc_response = parsed_email.get('clean_body', '')
        
        # Используем EmailGenerator если доступен
        if self.email_generator:
            try:
                response = self.email_generator.generate_follow_up_sync(
                    startup_info, vc_info, previous_context, vc_response, "interested"
                )
                return response
            except Exception as e:
                logger.error(f"Error with EmailGenerator: {e}")
        
        # Fallback генерация
        return self._generate_simple_follow_up(startup_info, vc_info, classification)
    
    async def _generate_document_response(self, startup_info: Dict[str, Any], 
                                        vc_info: Dict[str, Any], 
                                        classification: Dict[str, Any],
                                        parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация ответа с документами"""
        
        # Извлекаем запрошенные документы
        body = parsed_email.get('clean_body', '').lower()
        requested_docs = []
        
        if 'deck' in body or 'presentation' in body:
            requested_docs.append('pitch deck')
        if 'financial' in body or 'projections' in body:
            requested_docs.append('financial projections')
        if 'business plan' in body:
            requested_docs.append('business plan')
        
        # Простая генерация ответа
        return {
            'subject': f"Re: {parsed_email.get('subject', 'Your Request')} - Documents Attached",
            'body': f"""Dear {vc_info.get('name', 'Partner')},

Thank you for your interest in {startup_info.get('name', 'our company')}.

As requested, I'm attaching the following documents:
{', '.join(requested_docs) if requested_docs else 'our pitch deck and financial projections'}

Please let me know if you need any additional information or would like to schedule a call to discuss further.

Best regards,
{startup_info.get('contact_person', 'The Team')}
{startup_info.get('name', '')}""",
            'requested_documents': requested_docs,
            'action_type': 'send_documents'
        }
    
    def _generate_simple_follow_up(self, startup_info: Dict[str, Any], 
                                 vc_info: Dict[str, Any], 
                                 classification: Dict[str, Any]) -> Dict[str, Any]:
        """Простая генерация follow-up без AI"""
        return {
            'subject': f"Thank you for your interest in {startup_info.get('name', 'our company')}",
            'body': f"""Dear {vc_info.get('name', 'Partner')},

Thank you for your interest in {startup_info.get('name', 'our company')}.

We're excited about the potential partnership and would love to discuss how we can work together.

Would you be available for a brief call this week to explore this opportunity further?

Best regards,
{startup_info.get('contact_person', 'The Team')}
{startup_info.get('name', '')}""",
            'action_type': 'follow_up'
        }
    
    async def _update_database(self, parsed_email: Dict[str, Any], 
                             classification: Dict[str, Any], 
                             action_type: ActionType):
        """Обновление базы данных"""
        try:
            db = next(get_db())
            
            # Находим или создаем email запись
            email_record = db.query(Email).filter(
                Email.message_id == parsed_email.get('message_id')
            ).first()
            
            if email_record:
                # Обновляем существующую запись
                email_record.status = 'processed'
                email_record.updated_at = datetime.now()
            else:
                # Создаем новую запись через email_gateway
                await self._save_processed_email(parsed_email, classification)
            
            # Обновляем статус коммуникации
            await self._update_communication_status(parsed_email, classification, action_type)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            if 'db' in locals():
                db.rollback()
    
    async def _update_communication_status(self, parsed_email: Dict[str, Any], 
                                         classification: Dict[str, Any], 
                                         action_type: ActionType):
        """Обновление статуса коммуникации"""
        try:
            db = next(get_db())
            
            # Находим связанную коммуникацию
            thread_id = parsed_email.get('thread_info', {}).get('conversation_id')
            if not thread_id:
                return
            
            email_thread = db.query(EmailThread).filter(
                EmailThread.thread_id == thread_id
            ).first()
            
            if email_thread and email_thread.communication_id:
                communication = db.query(Communication).filter(
                    Communication.id == email_thread.communication_id
                ).first()
                
                if communication:
                    # Обновляем статус на основе действия
                    if action_type == ActionType.SCHEDULE_MEETING:
                        communication.status = 'meeting_requested'
                    elif action_type == ActionType.CLOSE_THREAD:
                        communication.status = 'closed'
                    elif action_type == ActionType.ESCALATE_TO_HUMAN:
                        communication.escalated_to_human = True
                        communication.status = 'escalated'
                    else:
                        communication.status = 'in_progress'
                    
                    communication.last_message_at = datetime.now()
                    communication.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating communication status: {e}")
    
    async def _send_escalation_notification(self, parsed_email: Dict[str, Any], 
                                          escalation_trigger: EscalationTrigger):
        """Отправка уведомления об эскалации"""
        try:
            # Логируем эскалацию
            escalation_reasons = []
            if escalation_trigger.meeting_request:
                escalation_reasons.append("Meeting request")
            if escalation_trigger.document_request:
                escalation_reasons.append("Document request")
            if escalation_trigger.rejection:
                escalation_reasons.append("Rejection")
            if escalation_trigger.urgent_keywords:
                escalation_reasons.append("Urgent keywords")
            if escalation_trigger.low_confidence:
                escalation_reasons.append("Low confidence classification")
            
            logger.warning(f"Email escalated for human review. Reasons: {', '.join(escalation_reasons)}")
            
            # Здесь можно добавить отправку уведомления в Slack, email или другую систему
            # await self._send_slack_notification(parsed_email, escalation_reasons)
            
        except Exception as e:
            logger.error(f"Error sending escalation notification: {e}")
    
    async def _extract_startup_vc_info(self, parsed_email: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Извлечение информации о стартапе и ВК из email"""
        try:
            db = next(get_db())
            
            # Находим информацию из заголовков email
            headers = parsed_email.get('headers', {})
            startup_id = headers.get('X-Startup-ID')
            vc_email = parsed_email.get('sender_email', '')
            
            startup_info = None
            vc_info = None
            
            # Получаем информацию о стартапе
            if startup_id:
                startup = db.query(Startup).filter(Startup.id == int(startup_id)).first()
                if startup:
                    startup_info = {
                        'id': startup.id,
                        'name': startup.name,
                        'email': startup.email,
                        'contact_person': startup.contact_person,
                        'industry': startup.industry,
                        'stage': startup.stage
                    }
            
            # Получаем информацию о ВК
            vc = db.query(VCFund).filter(VCFund.email == vc_email).first()
            if vc:
                vc_info = {
                    'id': vc.id,
                    'name': vc.name,
                    'email': vc.email,
                    'focus_industries': vc.focus_industries,
                    'investment_stages': vc.investment_stages
                }
            
            return startup_info, vc_info
            
        except Exception as e:
            logger.error(f"Error extracting startup/VC info: {e}")
            return None, None
    
    async def _get_processed_email_ids(self) -> List[str]:
        """Получение списка уже обработанных email ID"""
        try:
            db = next(get_db())
            processed_emails = db.query(Email.message_id).filter(
                Email.status.in_(['processed', 'sent', 'delivered'])
            ).all()
            return [email[0] for email in processed_emails]
        except Exception as e:
            logger.error(f"Error getting processed email IDs: {e}")
            return []
    
    async def _save_processed_email(self, parsed_email: Dict[str, Any], 
                                  classification: Dict[str, Any]):
        """Сохранение обработанного email"""
        try:
            # Используем email_gateway для сохранения
            result = self.email_gateway.parse_reply(
                parsed_email, 
                parsed_email.get('thread_info', {}).get('conversation_id', '')
            )
            
            logger.info(f"Saved processed email: {parsed_email.get('message_id')}")
            
        except Exception as e:
            logger.error(f"Error saving processed email: {e}")
    
    async def _update_processing_statistics(self, results: List[EmailProcessingResult]):
        """Обновление статистики обработки"""
        try:
            total_processed = len(results)
            successful = len([r for r in results if r.status == ProcessingStatus.COMPLETED])
            failed = len([r for r in results if r.status == ProcessingStatus.FAILED])
            escalated = len([r for r in results if r.action_taken == ActionType.ESCALATE_TO_HUMAN])
            
            logger.info(f"Processing statistics - Total: {total_processed}, "
                       f"Successful: {successful}, Failed: {failed}, Escalated: {escalated}")
            
            # Здесь можно сохранить статистику в БД или отправить в систему мониторинга
            
        except Exception as e:
            logger.error(f"Error updating processing statistics: {e}")
    
    async def retry_failed_processing(self) -> List[EmailProcessingResult]:
        """Повторная обработка неудачных операций"""
        try:
            db = next(get_db())
            
            # Находим emails с ошибками
            failed_emails = db.query(Email).filter(
                Email.status == 'failed',
                Email.updated_at > datetime.now() - timedelta(hours=24)
            ).all()
            
            results = []
            for email in failed_emails:
                try:
                    # Восстанавливаем данные email
                    email_data = {
                        'message_id': email.message_id,
                        'sender_email': email.sender_email,
                        'recipient_email': email.recipient_email,
                        'subject': email.subject,
                        'body': email.body,
                        'headers': email.headers or {}
                    }
                    
                    # Повторная обработка
                    result = await self._process_single_email(email_data)
                    result.retry_count = 1  # Увеличиваем счетчик повторов
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Retry failed for email {email.message_id}: {e}")
            
            logger.info(f"Retry processing completed. Retried {len(results)} emails")
            return results
            
        except Exception as e:
            logger.error(f"Error in retry processing: {e}")
            return []


# Глобальный экземпляр процессора
email_processor = EmailProcessor()
