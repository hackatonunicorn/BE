"""
Task Scheduler для автоматизации email обработки
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from app.email.email_processor import email_processor, EmailProcessingResult
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmailTaskScheduler:
    """
    Планировщик задач для автоматической обработки emails
    """
    
    def __init__(self):
        # Настройки планировщика
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': True,  # Объединять пропущенные задачи
            'max_instances': 1,  # Максимум 1 экземпляр задачи
            'misfire_grace_time': 60  # Время на выполнение пропущенной задачи
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        
        # Настройки задач
        self.email_processing_interval = int(os.getenv('EMAIL_PROCESSING_INTERVAL', '300'))  # 5 минут
        self.retry_interval = int(os.getenv('EMAIL_RETRY_INTERVAL', '600'))  # 10 минут
        self.cleanup_interval = int(os.getenv('EMAIL_CLEANUP_INTERVAL', '3600'))  # 1 час
        
        # Статистика выполнения
        self.job_statistics = {
            'email_processing': {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'last_run': None,
                'last_error': None
            },
            'retry_processing': {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'last_run': None,
                'last_error': None
            },
            'cleanup': {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'last_run': None,
                'last_error': None
            }
        }
        
        # Настройка обработчиков событий
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
        
        logger.info("EmailTaskScheduler initialized")
    
    async def start(self):
        """Запуск планировщика"""
        try:
            # Добавляем задачи
            await self._add_jobs()
            
            # Запускаем планировщик
            self.scheduler.start()
            
            logger.info("Email task scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start email task scheduler: {e}")
            raise
    
    async def stop(self):
        """Остановка планировщика"""
        try:
            self.scheduler.shutdown()
            logger.info("Email task scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping email task scheduler: {e}")
    
    async def _add_jobs(self):
        """Добавление задач в планировщик"""
        
        # Основная задача обработки emails
        self.scheduler.add_job(
            func=self._process_emails_job,
            trigger=IntervalTrigger(seconds=self.email_processing_interval),
            id='email_processing',
            name='Process Incoming Emails',
            replace_existing=True,
            max_instances=1
        )
        
        # Задача повторной обработки неудачных операций
        self.scheduler.add_job(
            func=self._retry_failed_job,
            trigger=IntervalTrigger(seconds=self.retry_interval),
            id='retry_processing',
            name='Retry Failed Email Processing',
            replace_existing=True,
            max_instances=1
        )
        
        # Задача очистки старых данных
        self.scheduler.add_job(
            func=self._cleanup_job,
            trigger=CronTrigger(hour=2, minute=0),  # Каждый день в 2:00
            id='cleanup',
            name='Cleanup Old Data',
            replace_existing=True,
            max_instances=1
        )
        
        # Задача мониторинга производительности
        self.scheduler.add_job(
            func=self._monitoring_job,
            trigger=IntervalTrigger(minutes=30),
            id='monitoring',
            name='Performance Monitoring',
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("Added email processing jobs to scheduler")
    
    async def _process_emails_job(self):
        """Основная задача обработки emails"""
        try:
            logger.info("Starting email processing job")
            
            # Обрабатываем входящие emails
            results = await email_processor.process_incoming_emails()
            
            # Обновляем статистику
            self.job_statistics['email_processing']['total_runs'] += 1
            self.job_statistics['email_processing']['successful_runs'] += 1
            self.job_statistics['email_processing']['last_run'] = datetime.now().isoformat()
            
            logger.info(f"Email processing job completed. Processed {len(results)} emails")
            
        except Exception as e:
            logger.error(f"Email processing job failed: {e}")
            
            # Обновляем статистику ошибок
            self.job_statistics['email_processing']['failed_runs'] += 1
            self.job_statistics['email_processing']['last_error'] = str(e)
            
            # Отправляем уведомление об ошибке
            await self._send_error_notification('email_processing', str(e))
    
    async def _retry_failed_job(self):
        """Задача повторной обработки неудачных операций"""
        try:
            logger.info("Starting retry processing job")
            
            # Повторно обрабатываем неудачные операции
            results = await email_processor.retry_failed_processing()
            
            # Обновляем статистику
            self.job_statistics['retry_processing']['total_runs'] += 1
            self.job_statistics['retry_processing']['successful_runs'] += 1
            self.job_statistics['retry_processing']['last_run'] = datetime.now().isoformat()
            
            logger.info(f"Retry processing job completed. Retried {len(results)} emails")
            
        except Exception as e:
            logger.error(f"Retry processing job failed: {e}")
            
            # Обновляем статистику ошибок
            self.job_statistics['retry_processing']['failed_runs'] += 1
            self.job_statistics['retry_processing']['last_error'] = str(e)
    
    async def _cleanup_job(self):
        """Задача очистки старых данных"""
        try:
            logger.info("Starting cleanup job")
            
            # Очищаем старые логи и временные данные
            await self._cleanup_old_data()
            
            # Обновляем статистику
            self.job_statistics['cleanup']['total_runs'] += 1
            self.job_statistics['cleanup']['successful_runs'] += 1
            self.job_statistics['cleanup']['last_run'] = datetime.now().isoformat()
            
            logger.info("Cleanup job completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup job failed: {e}")
            
            # Обновляем статистику ошибок
            self.job_statistics['cleanup']['failed_runs'] += 1
            self.job_statistics['cleanup']['last_error'] = str(e)
    
    async def _monitoring_job(self):
        """Задача мониторинга производительности"""
        try:
            logger.info("Starting monitoring job")
            
            # Собираем метрики производительности
            metrics = await self._collect_performance_metrics()
            
            # Проверяем здоровье системы
            health_status = await self._check_system_health(metrics)
            
            # Логируем метрики
            logger.info(f"System health: {health_status}")
            logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
            
            # Отправляем уведомление если есть проблемы
            if health_status != 'healthy':
                await self._send_health_alert(health_status, metrics)
            
        except Exception as e:
            logger.error(f"Monitoring job failed: {e}")
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            db = next(get_db())
            
            # Удаляем старые обработанные emails (старше 90 дней)
            cutoff_date = datetime.now() - timedelta(days=90)
            
            from app.data.models import Email
            old_emails = db.query(Email).filter(
                Email.created_at < cutoff_date,
                Email.status.in_(['processed', 'delivered'])
            ).all()
            
            for email in old_emails:
                db.delete(email)
            
            db.commit()
            
            logger.info(f"Cleaned up {len(old_emails)} old email records")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            if 'db' in locals():
                db.rollback()
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Сбор метрик производительности"""
        try:
            db = next(get_db())
            
            # Статистика по emails за последние 24 часа
            since_date = datetime.now() - timedelta(hours=24)
            
            from app.data.models import Email, EmailThread
            
            total_emails = db.query(Email).filter(
                Email.created_at >= since_date
            ).count()
            
            processed_emails = db.query(Email).filter(
                Email.created_at >= since_date,
                Email.status == 'processed'
            ).count()
            
            failed_emails = db.query(Email).filter(
                Email.created_at >= since_date,
                Email.status == 'failed'
            ).count()
            
            active_threads = db.query(EmailThread).filter(
                EmailThread.status == 'active'
            ).count()
            
            metrics = {
                'emails_processed_24h': total_emails,
                'success_rate': (processed_emails / total_emails * 100) if total_emails > 0 else 0,
                'failure_rate': (failed_emails / total_emails * 100) if total_emails > 0 else 0,
                'active_threads': active_threads,
                'job_statistics': self.job_statistics,
                'scheduler_running': self.scheduler.running,
                'timestamp': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {'error': str(e)}
    
    async def _check_system_health(self, metrics: Dict[str, Any]) -> str:
        """Проверка здоровья системы"""
        try:
            # Проверяем успешность обработки
            success_rate = metrics.get('success_rate', 0)
            failure_rate = metrics.get('failure_rate', 0)
            
            if failure_rate > 20:  # Более 20% ошибок
                return 'critical'
            elif failure_rate > 10:  # Более 10% ошибок
                return 'warning'
            elif success_rate < 80:  # Менее 80% успеха
                return 'degraded'
            else:
                return 'healthy'
                
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return 'error'
    
    async def _send_error_notification(self, job_name: str, error_message: str):
        """Отправка уведомления об ошибке"""
        try:
            # Здесь можно добавить отправку в Slack, email или другую систему
            logger.error(f"Job {job_name} failed: {error_message}")
            
            # Простое логирование для демо
            error_data = {
                'job_name': job_name,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat(),
                'severity': 'error'
            }
            
            logger.error(f"Error notification: {json.dumps(error_data)}")
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    async def _send_health_alert(self, health_status: str, metrics: Dict[str, Any]):
        """Отправка уведомления о проблемах со здоровьем системы"""
        try:
            alert_data = {
                'health_status': health_status,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat(),
                'severity': 'warning' if health_status in ['warning', 'degraded'] else 'critical'
            }
            
            logger.warning(f"Health alert: {json.dumps(alert_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error sending health alert: {e}")
    
    def _job_executed(self, event):
        """Обработчик успешного выполнения задачи"""
        logger.info(f"Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Обработчик ошибки выполнения задачи"""
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
    
    def _job_missed(self, event):
        """Обработчик пропущенной задачи"""
        logger.warning(f"Job {event.job_id} was missed")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Получение статуса всех задач"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'scheduler_running': self.scheduler.running,
                'jobs': jobs,
                'statistics': self.job_statistics
            }
            
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {'error': str(e)}
    
    def trigger_job(self, job_id: str) -> bool:
        """Ручной запуск задачи"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Triggered job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """Приостановка задачи"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
                logger.info(f"Paused job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Возобновление задачи"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.resume()
                logger.info(f"Resumed job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False


# Глобальный экземпляр планировщика
email_task_scheduler = EmailTaskScheduler()
