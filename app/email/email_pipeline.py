"""
Email Pipeline - основной класс для автоматизированной обработки email коммуникаций
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from app.email.email_processor import email_processor, ProcessingStatus, ActionType, EmailProcessingResult
from app.email.task_scheduler import email_task_scheduler
from app.email.queue_manager import email_queue_manager, QueuePriority, QueueStatus
from app.email.email_gateway import email_gateway
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmailPipeline:
    """
    Основной pipeline для автоматизированной обработки email коммуникаций
    """
    
    def __init__(self):
        self.processor = email_processor
        self.scheduler = email_task_scheduler
        self.queue_manager = email_queue_manager
        self.email_gateway = email_gateway
        
        # Настройки pipeline
        self.pipeline_enabled = os.getenv('EMAIL_PIPELINE_ENABLED', 'true').lower() == 'true'
        self.auto_response_enabled = os.getenv('AUTO_RESPONSE_ENABLED', 'true').lower() == 'true'
        self.escalation_enabled = os.getenv('ESCALATION_ENABLED', 'true').lower() == 'true'
        
        # Статистика
        self.pipeline_statistics = {
            'total_processed': 0,
            'successful_responses': 0,
            'escalated_cases': 0,
            'failed_operations': 0,
            'last_run': None,
            'average_processing_time': 0.0
        }
        
        logger.info("EmailPipeline initialized")
    
    async def start_pipeline(self):
        """Запуск всего pipeline"""
        try:
            if not self.pipeline_enabled:
                logger.info("Email pipeline is disabled")
                return
            
            logger.info("Starting email processing pipeline")
            
            # Запускаем планировщик задач
            await self.scheduler.start()
            
            # Запускаем обработчик очередей
            await self._start_queue_processor()
            
            logger.info("Email processing pipeline started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start email pipeline: {e}")
            raise
    
    async def stop_pipeline(self):
        """Остановка pipeline"""
        try:
            logger.info("Stopping email processing pipeline")
            
            # Останавливаем планировщик
            await self.scheduler.stop()
            
            # Останавливаем обработчик очередей
            await self._stop_queue_processor()
            
            logger.info("Email processing pipeline stopped")
            
        except Exception as e:
            logger.error(f"Error stopping email pipeline: {e}")
    
    async def _start_queue_processor(self):
        """Запуск обработчика очередей"""
        # Создаем фоновую задачу для обработки очередей
        asyncio.create_task(self._queue_processing_loop())
        logger.info("Queue processor started")
    
    async def _stop_queue_processor(self):
        """Остановка обработчика очередей"""
        # Здесь можно добавить логику для graceful shutdown
        logger.info("Queue processor stopped")
    
    async def _queue_processing_loop(self):
        """Основной цикл обработки очередей"""
        while True:
            try:
                # Обрабатываем задачи из очереди
                await self._process_queue_tasks()
                
                # Небольшая пауза между итерациями
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in queue processing loop: {e}")
                await asyncio.sleep(10)  # Больше времени на восстановление при ошибке
    
    async def _process_queue_tasks(self):
        """Обработка задач из очередей"""
        try:
            # Обрабатываем задачи обработки emails
            await self._process_email_tasks()
            
            # Обрабатываем задачи генерации ответов
            await self._process_response_generation_tasks()
            
            # Обрабатываем задачи уведомлений
            await self._process_notification_tasks()
            
            # Обрабатываем задачи повторов
            await self._process_retry_tasks()
            
        except Exception as e:
            logger.error(f"Error processing queue tasks: {e}")
    
    async def _process_email_tasks(self):
        """Обработка задач email из очереди"""
        try:
            task = await self.queue_manager.get_next_task("email_processing")
            if not task:
                return
            
            logger.info(f"Processing email task {task.id}")
            
            try:
                # Выполняем обработку email
                results = await self.processor.process_incoming_emails()
                
                # Обновляем статистику
                self.pipeline_statistics['total_processed'] += len(results)
                
                # Отмечаем задачу как завершенную
                await self.queue_manager.complete_task(task.id, {
                    'results': [result.__dict__ for result in results],
                    'processed_count': len(results)
                })
                
                logger.info(f"Completed email processing task {task.id}")
                
            except Exception as e:
                logger.error(f"Error processing email task {task.id}: {e}")
                await self.queue_manager.fail_task(task.id, str(e))
                
        except Exception as e:
            logger.error(f"Error in email task processing: {e}")
    
    async def _process_response_generation_tasks(self):
        """Обработка задач генерации ответов"""
        try:
            task = await self.queue_manager.get_next_task("response_generation")
            if not task:
                return
            
            logger.info(f"Processing response generation task {task.id}")
            
            try:
                data = task.data
                startup_info = data.get('startup_info', {})
                vc_info = data.get('vc_info', {})
                classification = data.get('classification', {})
                
                # Генерируем ответ
                response = await self._generate_automated_response(
                    startup_info, vc_info, classification
                )
                
                if response and self.auto_response_enabled:
                    # Отправляем ответ
                    send_result = await self._send_automated_response(response, startup_info)
                    
                    if send_result:
                        self.pipeline_statistics['successful_responses'] += 1
                
                # Отмечаем задачу как завершенную
                await self.queue_manager.complete_task(task.id, {
                    'response_generated': response is not None,
                    'response_sent': send_result if response else False
                })
                
                logger.info(f"Completed response generation task {task.id}")
                
            except Exception as e:
                logger.error(f"Error processing response generation task {task.id}: {e}")
                await self.queue_manager.fail_task(task.id, str(e))
                
        except Exception as e:
            logger.error(f"Error in response generation task processing: {e}")
    
    async def _process_notification_tasks(self):
        """Обработка задач уведомлений"""
        try:
            task = await self.queue_manager.get_next_task("notification")
            if not task:
                return
            
            logger.info(f"Processing notification task {task.id}")
            
            try:
                notification_data = task.data
                
                # Отправляем уведомление
                await self._send_notification(notification_data)
                
                # Отмечаем задачу как завершенную
                await self.queue_manager.complete_task(task.id, {
                    'notification_sent': True
                })
                
                logger.info(f"Completed notification task {task.id}")
                
            except Exception as e:
                logger.error(f"Error processing notification task {task.id}: {e}")
                await self.queue_manager.fail_task(task.id, str(e))
                
        except Exception as e:
            logger.error(f"Error in notification task processing: {e}")
    
    async def _process_retry_tasks(self):
        """Обработка задач повторов"""
        try:
            task = await self.queue_manager.get_next_task("retry")
            if not task:
                return
            
            logger.info(f"Processing retry task {task.id}")
            
            try:
                # Выполняем повторную обработку
                original_task_data = task.data
                
                # Повторяем операцию в зависимости от типа
                if task.metadata.get('original_task_type') == 'email_processing':
                    await self._process_single_email_retry(original_task_data)
                elif task.metadata.get('original_task_type') == 'response_generation':
                    await self._process_response_generation_retry(original_task_data)
                
                # Отмечаем задачу как завершенную
                await self.queue_manager.complete_task(task.id, {
                    'retry_successful': True,
                    'retry_count': task.metadata.get('retry_count', 1)
                })
                
                logger.info(f"Completed retry task {task.id}")
                
            except Exception as e:
                logger.error(f"Error processing retry task {task.id}: {e}")
                await self.queue_manager.fail_task(task.id, str(e))
                
        except Exception as e:
            logger.error(f"Error in retry task processing: {e}")
    
    async def _generate_automated_response(self, startup_info: Dict[str, Any], 
                                         vc_info: Dict[str, Any], 
                                         classification: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерация автоматизированного ответа"""
        try:
            classification_type = classification.get('classification', 'unclear')
            
            # Определяем тип ответа на основе классификации
            if classification_type == 'interested':
                return await self._generate_interest_response(startup_info, vc_info)
            elif classification_type == 'request_more_info':
                return await self._generate_info_response(startup_info, vc_info)
            elif classification_type == 'meeting_request':
                return await self._generate_meeting_response(startup_info, vc_info)
            else:
                logger.info(f"No automated response needed for classification: {classification_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating automated response: {e}")
            return None
    
    async def _generate_interest_response(self, startup_info: Dict[str, Any], 
                                        vc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация ответа на проявленный интерес"""
        return {
            'subject': f"Thank you for your interest in {startup_info.get('name', 'our company')}",
            'body': f"""Dear {vc_info.get('name', 'Partner')},

Thank you for your interest in {startup_info.get('name', 'our company')}.

We're excited about the potential partnership and would love to discuss how we can work together.

I'm attaching our pitch deck and would be happy to schedule a call at your convenience to explore this opportunity further.

Best regards,
{startup_info.get('contact_person', 'The Team')}
{startup_info.get('name', '')}""",
            'action_type': 'send_documents_and_schedule'
        }
    
    async def _generate_info_response(self, startup_info: Dict[str, Any], 
                                    vc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация ответа на запрос информации"""
        return {
            'subject': f"Re: {startup_info.get('name', 'Partnership Opportunity')} - Requested Information",
            'body': f"""Dear {vc_info.get('name', 'Partner')},

Thank you for your interest in {startup_info.get('name', 'our company')}.

As requested, I'm providing the following information:
- Pitch deck (attached)
- Financial projections
- Team backgrounds
- Market analysis

Please let me know if you need any additional information or would like to schedule a call to discuss further.

Best regards,
{startup_info.get('contact_person', 'The Team')}
{startup_info.get('name', '')}""",
            'action_type': 'send_documents'
        }
    
    async def _generate_meeting_response(self, startup_info: Dict[str, Any], 
                                       vc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация ответа на запрос встречи"""
        return {
            'subject': f"Re: Meeting Request - {startup_info.get('name', 'Partnership Discussion')}",
            'body': f"""Dear {vc_info.get('name', 'Partner')},

Thank you for your interest in scheduling a meeting to discuss {startup_info.get('name', 'our company')}.

I'd be delighted to meet with you. Here are some available time slots:
- Tuesday 2:00-3:00 PM
- Wednesday 10:00-11:00 AM
- Thursday 3:00-4:00 PM

Please let me know which time works best for you, or feel free to suggest an alternative time.

Best regards,
{startup_info.get('contact_person', 'The Team')}
{startup_info.get('name', '')}""",
            'action_type': 'schedule_meeting'
        }
    
    async def _send_automated_response(self, response: Dict[str, Any], 
                                     startup_info: Dict[str, Any]) -> bool:
        """Отправка автоматизированного ответа"""
        try:
            # Получаем информацию о получателе из контекста
            # В реальной реализации это будет извлекаться из исходного email
            
            # Симуляция отправки
            logger.info(f"Sending automated response from {startup_info.get('name')}: {response['subject']}")
            
            # Здесь будет реальная отправка через email_gateway
            # send_result = await self.email_gateway.send_email(...)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending automated response: {e}")
            return False
    
    async def _send_notification(self, notification_data: Dict[str, Any]):
        """Отправка уведомления"""
        try:
            notification_type = notification_data.get('type', 'general')
            
            if notification_type == 'escalation':
                await self._send_escalation_notification(notification_data)
            elif notification_type == 'meeting_request':
                await self._send_meeting_notification(notification_data)
            elif notification_type == 'error':
                await self._send_error_notification(notification_data)
            else:
                logger.info(f"Unknown notification type: {notification_type}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _send_escalation_notification(self, notification_data: Dict[str, Any]):
        """Отправка уведомления об эскалации"""
        try:
            # Здесь можно добавить отправку в Slack, email или другую систему
            escalation_info = {
                'reason': notification_data.get('reason'),
                'email_id': notification_data.get('email_id'),
                'startup_name': notification_data.get('startup_name'),
                'vc_name': notification_data.get('vc_name'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.warning(f"ESCALATION REQUIRED: {json.dumps(escalation_info)}")
            
            # Обновляем статистику
            self.pipeline_statistics['escalated_cases'] += 1
            
        except Exception as e:
            logger.error(f"Error sending escalation notification: {e}")
    
    async def _send_meeting_notification(self, notification_data: Dict[str, Any]):
        """Отправка уведомления о запросе встречи"""
        try:
            meeting_info = {
                'startup_name': notification_data.get('startup_name'),
                'vc_name': notification_data.get('vc_name'),
                'requested_time': notification_data.get('requested_time'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"MEETING REQUEST: {json.dumps(meeting_info)}")
            
        except Exception as e:
            logger.error(f"Error sending meeting notification: {e}")
    
    async def _send_error_notification(self, notification_data: Dict[str, Any]):
        """Отправка уведомления об ошибке"""
        try:
            error_info = {
                'error_type': notification_data.get('error_type'),
                'error_message': notification_data.get('error_message'),
                'component': notification_data.get('component'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.error(f"SYSTEM ERROR: {json.dumps(error_info)}")
            
            # Обновляем статистику
            self.pipeline_statistics['failed_operations'] += 1
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    async def _process_single_email_retry(self, email_data: Dict[str, Any]):
        """Повторная обработка одного email"""
        try:
            # Выполняем повторную обработку
            result = await self.processor._process_single_email(email_data)
            
            if result.status == ProcessingStatus.FAILED:
                raise Exception(f"Retry failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Error in email retry processing: {e}")
            raise
    
    async def _process_response_generation_retry(self, task_data: Dict[str, Any]):
        """Повторная обработка генерации ответа"""
        try:
            # Повторяем генерацию ответа
            startup_info = task_data.get('startup_info', {})
            vc_info = task_data.get('vc_info', {})
            classification = task_data.get('classification', {})
            
            response = await self._generate_automated_response(startup_info, vc_info, classification)
            
            if response and self.auto_response_enabled:
                await self._send_automated_response(response, startup_info)
                
        except Exception as e:
            logger.error(f"Error in response generation retry: {e}")
            raise
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Получение статуса pipeline"""
        try:
            # Получаем статус планировщика
            scheduler_status = self.scheduler.get_job_status()
            
            # Получаем статус очередей
            queue_status = await self.queue_manager.get_queue_status()
            
            # Обновляем время последнего запуска
            self.pipeline_statistics['last_run'] = datetime.now().isoformat()
            
            return {
                'pipeline_enabled': self.pipeline_enabled,
                'auto_response_enabled': self.auto_response_enabled,
                'escalation_enabled': self.escalation_enabled,
                'statistics': self.pipeline_statistics,
                'scheduler_status': scheduler_status,
                'queue_status': queue_status,
                'health_status': await self._check_pipeline_health()
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {'error': str(e)}
    
    async def _check_pipeline_health(self) -> str:
        """Проверка здоровья pipeline"""
        try:
            # Проверяем основные компоненты
            if not self.scheduler.scheduler.running:
                return 'critical'
            
            # Проверяем статистику ошибок
            failed_rate = 0
            if self.pipeline_statistics['total_processed'] > 0:
                failed_rate = (self.pipeline_statistics['failed_operations'] / 
                             self.pipeline_statistics['total_processed']) * 100
            
            if failed_rate > 20:
                return 'critical'
            elif failed_rate > 10:
                return 'warning'
            else:
                return 'healthy'
                
        except Exception as e:
            logger.error(f"Error checking pipeline health: {e}")
            return 'error'
    
    async def manual_trigger_processing(self) -> Dict[str, Any]:
        """Ручной запуск обработки"""
        try:
            logger.info("Manual trigger of email processing")
            
            # Добавляем задачу в очередь
            task_id = await self.queue_manager.add_email_processing_task(
                {'manual_trigger': True},
                QueuePriority.HIGH
            )
            
            return {
                'message': 'Email processing triggered manually',
                'task_id': task_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual trigger: {e}")
            return {'error': str(e)}
    
    async def retry_failed_operations(self) -> Dict[str, Any]:
        """Повторная обработка неудачных операций"""
        try:
            logger.info("Retrying failed operations")
            
            # Получаем неудачные задачи
            failed_tasks = await self.queue_manager.get_failed_tasks()
            
            # Планируем повторы
            retry_ids = await self.queue_manager.retry_failed_tasks()
            
            return {
                'message': f'Retried {len(retry_ids)} failed operations',
                'retry_task_ids': retry_ids,
                'failed_tasks_count': len(failed_tasks),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrying failed operations: {e}")
            return {'error': str(e)}


# Глобальный экземпляр pipeline
email_pipeline = EmailPipeline()
