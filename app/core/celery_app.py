"""
Celery configuration for background task processing
"""
import os
import logging
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from celery.schedules import crontab
from kombu import Queue
import redis
from datetime import timedelta

from app.core.config_simple import settings

logger = logging.getLogger(__name__)

# Redis connection for Celery broker and result backend
redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

# Create Celery app
celery_app = Celery(
    "startup_vc_tasks",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.analysis_tasks", 
        "app.tasks.reporting_tasks",
        "app.tasks.cleanup_tasks",
        "app.tasks.matching_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing and queues
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.analysis_tasks.*": {"queue": "analysis"},
        "app.tasks.reporting_tasks.*": {"queue": "reporting"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "app.tasks.matching_tasks.*": {"queue": "matching"},
    },
    
    # Queue configuration with priorities
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("high_priority", routing_key="high_priority"),
        Queue("email", routing_key="email"),
        Queue("analysis", routing_key="analysis"),
        Queue("reporting", routing_key="reporting"),
        Queue("cleanup", routing_key="cleanup"),
        Queue("matching", routing_key="matching"),
    ),
    
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # 1 hour
    result_backend_max_retries=3,
    
    # Task retry settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat scheduler settings
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="celerybeat-schedule",
    
    # Monitoring settings
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Periodic tasks (Beat schedule)
    beat_schedule={
        # Email processing - every 5 minutes
        "process-incoming-emails": {
            "task": "app.tasks.email_tasks.process_incoming_emails",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "email", "priority": 8}
        },
        
        # Follow-up sending - every hour
        "send-scheduled-follow-ups": {
            "task": "app.tasks.email_tasks.send_scheduled_follow_ups",
            "schedule": timedelta(hours=1),
            "options": {"queue": "email", "priority": 6}
        },
        
        # Pitch deck analysis - every 30 minutes
        "analyze-pending-pitch-decks": {
            "task": "app.tasks.analysis_tasks.analyze_pending_pitch_decks",
            "schedule": timedelta(minutes=30),
            "options": {"queue": "analysis", "priority": 7}
        },
        
        # Daily reports - every day at 9 AM UTC
        "generate-daily-reports": {
            "task": "app.tasks.reporting_tasks.generate_daily_reports",
            "schedule": crontab(hour=9, minute=0),
            "options": {"queue": "reporting", "priority": 5}
        },
        
        # Weekly cleanup - every Monday at 2 AM UTC
        "cleanup-old-communications": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_communications",
            "schedule": crontab(hour=2, minute=0, day_of_week=1),
            "options": {"queue": "cleanup", "priority": 3}
        },
        
        # Fund matching scores - daily at 6 AM UTC
        "update-fund-matching-scores": {
            "task": "app.tasks.matching_tasks.update_fund_matching_scores",
            "schedule": crontab(hour=6, minute=0),
            "options": {"queue": "matching", "priority": 4}
        },
        
        # Health check - every 10 minutes
        "system-health-check": {
            "task": "app.tasks.system_tasks.system_health_check",
            "schedule": timedelta(minutes=10),
            "options": {"queue": "default", "priority": 9}
        },
        
        # Notification processing - every 2 minutes
        "process-notification-queue": {
            "task": "app.tasks.notification_tasks.process_notification_queue",
            "schedule": timedelta(minutes=2),
            "options": {"queue": "default", "priority": 7}
        },
    }
)

# Custom retry configuration for different task types
CELERY_TASK_ANNOTATIONS = {
    "app.tasks.email_tasks.*": {
        "rate_limit": "100/m",
        "max_retries": 5,
        "default_retry_delay": 60,
        "retry_backoff": True,
        "retry_backoff_max": 600,
        "retry_jitter": True,
    },
    "app.tasks.analysis_tasks.*": {
        "rate_limit": "50/m",
        "max_retries": 3,
        "default_retry_delay": 120,
        "retry_backoff": True,
        "retry_backoff_max": 900,
    },
    "app.tasks.reporting_tasks.*": {
        "rate_limit": "10/m",
        "max_retries": 2,
        "default_retry_delay": 300,
    },
    "app.tasks.cleanup_tasks.*": {
        "rate_limit": "5/m",
        "max_retries": 1,
        "default_retry_delay": 600,
    },
    "app.tasks.matching_tasks.*": {
        "rate_limit": "20/m",
        "max_retries": 3,
        "default_retry_delay": 180,
    },
}

celery_app.conf.task_annotations = CELERY_TASK_ANNOTATIONS


# Redis connection for health checks
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


# Task signals for monitoring and logging
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handler called before task execution"""
    logger.info(f"Starting task {task.name} with ID {task_id}")
    
    # Update task status in database
    try:
        from app.tasks.models import TaskExecution
        from app.core.database import get_db
        
        db = next(get_db())
        task_execution = TaskExecution(
            task_id=task_id,
            task_name=task.name,
            status="started",
            args=str(args) if args else None,
            kwargs=str(kwargs) if kwargs else None
        )
        db.add(task_execution)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log task start: {e}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Handler called after task execution"""
    logger.info(f"Completed task {task.name} with ID {task_id}, state: {state}")
    
    # Update task status in database
    try:
        from app.tasks.models import TaskExecution
        from app.core.database import get_db
        
        db = next(get_db())
        task_execution = db.query(TaskExecution).filter(TaskExecution.task_id == task_id).first()
        if task_execution:
            task_execution.status = state
            task_execution.result = str(retval) if retval else None
            task_execution.completed_at = datetime.now()
            db.commit()
    except Exception as e:
        logger.error(f"Failed to log task completion: {e}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handler called when task fails"""
    logger.error(f"Task {sender.name} with ID {task_id} failed: {exception}")
    
    # Update task status and send notification for critical failures
    try:
        from app.tasks.models import TaskExecution
        from app.core.database import get_db
        from app.core.notifications import notification_service
        
        db = next(get_db())
        task_execution = db.query(TaskExecution).filter(TaskExecution.task_id == task_id).first()
        if task_execution:
            task_execution.status = "failed"
            task_execution.error_message = str(exception)
            task_execution.traceback = str(traceback)
            task_execution.completed_at = datetime.now()
            db.commit()
            
            # Send notification for critical task failures
            if sender.name in [
                "app.tasks.email_tasks.process_incoming_emails",
                "app.tasks.analysis_tasks.analyze_pending_pitch_decks",
                "system_health_check"
            ]:
                notification_service.send_notification(
                    user_id=1,  # System admin
                    notification_type="system_error",
                    data={
                        "task_name": sender.name,
                        "task_id": task_id,
                        "error": str(exception),
                        "critical": True
                    }
                )
    except Exception as e:
        logger.error(f"Failed to handle task failure: {e}")


# Custom task base class with enhanced error handling
class BaseTask(celery_app.Task):
    """Base task class with enhanced error handling and monitoring"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful task completion"""
        logger.info(f"Task {self.name} completed successfully: {task_id}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Task {self.name} failed: {task_id}, error: {exc}")
        
        # Implement exponential backoff for retries
        if self.request.retries < self.max_retries:
            countdown = min(300, (2 ** self.request.retries) * 60)  # Max 5 minutes
            logger.info(f"Retrying task {task_id} in {countdown} seconds")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called on task retry"""
        logger.warning(f"Retrying task {self.name}: {task_id}, attempt {self.request.retries + 1}")
    
    def on_revoked(self, task_id, terminated, signum, expired):
        """Called when task is revoked"""
        logger.warning(f"Task {self.name} revoked: {task_id}, terminated: {terminated}")


# Health check functions
def check_redis_connection():
    """Check Redis connection health"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


def check_database_connection():
    """Check database connection health"""
    try:
        from app.core.database import check_db_connection
        return check_db_connection()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_celery_stats():
    """Get Celery worker statistics"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()
        
        return {
            "workers": len(stats) if stats else 0,
            "active_tasks": len(active) if active else 0,
            "scheduled_tasks": len(scheduled) if scheduled else 0,
            "reserved_tasks": len(reserved) if reserved else 0,
            "stats": stats,
            "active": active,
            "scheduled": scheduled,
            "reserved": reserved
        }
    except Exception as e:
        logger.error(f"Failed to get Celery stats: {e}")
        return {"error": str(e)}


# Task monitoring utilities
class TaskMonitor:
    """Task monitoring utilities"""
    
    @staticmethod
    def get_task_status(task_id):
        """Get status of a specific task"""
        try:
            result = celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "info": result.info,
                "traceback": result.traceback
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def revoke_task(task_id, terminate=False):
        """Revoke a running task"""
        try:
            celery_app.control.revoke(task_id, terminate=terminate)
            return {"success": True, "message": f"Task {task_id} revoked"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_queue_lengths():
        """Get queue lengths"""
        try:
            inspect = celery_app.control.inspect()
            active = inspect.active()
            scheduled = inspect.scheduled()
            reserved = inspect.reserved()
            
            queue_lengths = {}
            for worker, tasks in (active or {}).items():
                for task in tasks:
                    queue = task.get("delivery_info", {}).get("routing_key", "default")
                    queue_lengths[queue] = queue_lengths.get(queue, 0) + 1
            
            return queue_lengths
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def purge_queue(queue_name):
        """Purge all tasks from a specific queue"""
        try:
            celery_app.control.purge()
            return {"success": True, "message": f"Queue {queue_name} purged"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Graceful shutdown handling
import signal
import sys

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    
    # Revoke all pending tasks
    try:
        celery_app.control.revoke(terminate=True)
        logger.info("All pending tasks revoked")
    except Exception as e:
        logger.error(f"Failed to revoke tasks: {e}")
    
    # Close database connections
    try:
        from app.core.database import engine
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Failed to close database connections: {e}")
    
    logger.info("Graceful shutdown completed")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Export celery app for use in other modules
__all__ = ["celery_app", "TaskMonitor", "check_redis_connection", "check_database_connection", "get_celery_stats"]
