"""
Queue Manager для управления очередями email обработки
"""
import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import heapq
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class QueuePriority(Enum):
    """Приоритеты очередей"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class QueueStatus(Enum):
    """Статусы элементов очереди"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """Элемент очереди"""
    id: str
    priority: QueuePriority
    status: QueueStatus
    data: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __lt__(self, other):
        """Сравнение для heapq (приоритетная очередь)"""
        if self.scheduled_at and other.scheduled_at:
            return self.scheduled_at < other.scheduled_at
        elif self.scheduled_at:
            return True
        elif other.scheduled_at:
            return False
        else:
            return self.priority.value > other.priority.value


@dataclass
class QueueStatistics:
    """Статистика очереди"""
    total_items: int = 0
    pending_items: int = 0
    processing_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    retry_items: int = 0
    average_processing_time: float = 0.0
    success_rate: float = 0.0
    last_updated: Optional[datetime] = None


class EmailQueueManager:
    """
    Менеджер очередей для email обработки
    """
    
    def __init__(self):
        # Основные очереди
        self.pending_queue = []  # Приоритетная очередь (heapq)
        self.processing_queue = {}  # Словарь обрабатываемых элементов
        self.completed_queue = deque(maxlen=1000)  # Очередь завершенных
        self.failed_queue = deque(maxlen=1000)  # Очередь неудачных
        
        # Специализированные очереди
        self.email_processing_queue = []  # Обработка входящих emails
        self.response_generation_queue = []  # Генерация ответов
        self.notification_queue = []  # Отправка уведомлений
        self.retry_queue = []  # Повторные попытки
        
        # Настройки
        self.max_concurrent_processing = int(os.getenv('MAX_CONCURRENT_EMAIL_PROCESSING', '5'))
        self.default_retry_delay = int(os.getenv('DEFAULT_RETRY_DELAY', '60'))  # секунды
        self.max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '10000'))
        self.cleanup_interval = int(os.getenv('QUEUE_CLEANUP_INTERVAL', '3600'))  # секунды
        
        # Статистика
        self.statistics = QueueStatistics()
        self.processing_times = defaultdict(list)
        
        # Блокировки для thread safety
        self._lock = asyncio.Lock()
        
        logger.info("EmailQueueManager initialized")
    
    async def add_email_processing_task(self, email_data: Dict[str, Any], 
                                      priority: QueuePriority = QueuePriority.NORMAL,
                                      scheduled_at: Optional[datetime] = None) -> str:
        """Добавление задачи обработки email"""
        return await self._add_task(
            queue_type="email_processing",
            priority=priority,
            data=email_data,
            scheduled_at=scheduled_at,
            metadata={"task_type": "email_processing"}
        )
    
    async def add_response_generation_task(self, startup_info: Dict[str, Any],
                                         vc_info: Dict[str, Any],
                                         classification: Dict[str, Any],
                                         priority: QueuePriority = QueuePriority.HIGH) -> str:
        """Добавление задачи генерации ответа"""
        task_data = {
            "startup_info": startup_info,
            "vc_info": vc_info,
            "classification": classification
        }
        
        return await self._add_task(
            queue_type="response_generation",
            priority=priority,
            data=task_data,
            metadata={"task_type": "response_generation"}
        )
    
    async def add_notification_task(self, notification_data: Dict[str, Any],
                                  priority: QueuePriority = QueuePriority.HIGH) -> str:
        """Добавление задачи отправки уведомления"""
        return await self._add_task(
            queue_type="notification",
            priority=priority,
            data=notification_data,
            metadata={"task_type": "notification"}
        )
    
    async def add_retry_task(self, failed_item_id: str, 
                           retry_delay: Optional[int] = None) -> str:
        """Добавление задачи повторной попытки"""
        retry_delay = retry_delay or self.default_retry_delay
        scheduled_at = datetime.now() + timedelta(seconds=retry_delay)
        
        # Получаем данные из неудачного элемента
        failed_item = await self.get_item(failed_item_id)
        if not failed_item:
            raise ValueError(f"Failed item {failed_item_id} not found")
        
        return await self._add_task(
            queue_type="retry",
            priority=QueuePriority.NORMAL,
            data=failed_item.data,
            scheduled_at=scheduled_at,
            metadata={
                "task_type": "retry",
                "original_item_id": failed_item_id,
                "retry_count": failed_item.retry_count + 1
            }
        )
    
    async def _add_task(self, queue_type: str, priority: QueuePriority,
                       data: Dict[str, Any], scheduled_at: Optional[datetime] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Общий метод добавления задачи"""
        async with self._lock:
            # Проверяем размер очереди
            if len(self.pending_queue) >= self.max_queue_size:
                raise RuntimeError("Queue is full")
            
            # Создаем элемент очереди
            item = QueueItem(
                id=str(uuid.uuid4()),
                priority=priority,
                status=QueueStatus.PENDING,
                data=data,
                created_at=datetime.now(),
                scheduled_at=scheduled_at,
                metadata=metadata or {}
            )
            
            # Добавляем в соответствующую очередь
            if queue_type == "email_processing":
                heapq.heappush(self.email_processing_queue, item)
            elif queue_type == "response_generation":
                heapq.heappush(self.response_generation_queue, item)
            elif queue_type == "notification":
                heapq.heappush(self.notification_queue, item)
            elif queue_type == "retry":
                heapq.heappush(self.retry_queue, item)
            else:
                heapq.heappush(self.pending_queue, item)
            
            # Обновляем статистику
            await self._update_statistics()
            
            logger.info(f"Added {queue_type} task {item.id} with priority {priority.name}")
            return item.id
    
    async def get_next_task(self, queue_type: Optional[str] = None) -> Optional[QueueItem]:
        """Получение следующей задачи для обработки"""
        async with self._lock:
            # Проверяем ограничение на одновременную обработку
            if len(self.processing_queue) >= self.max_concurrent_processing:
                return None
            
            current_time = datetime.now()
            target_queue = None
            
            # Выбираем очередь
            if queue_type == "email_processing" and self.email_processing_queue:
                target_queue = self.email_processing_queue
            elif queue_type == "response_generation" and self.response_generation_queue:
                target_queue = self.response_generation_queue
            elif queue_type == "notification" and self.notification_queue:
                target_queue = self.notification_queue
            elif queue_type == "retry" and self.retry_queue:
                target_queue = self.retry_queue
            elif self.pending_queue:
                target_queue = self.pending_queue
            
            if not target_queue:
                return None
            
            # Ищем задачу готовую к выполнению
            ready_tasks = []
            while target_queue:
                item = heapq.heappop(target_queue)
                
                # Проверяем время выполнения
                if item.scheduled_at and item.scheduled_at > current_time:
                    # Задача еще не готова, возвращаем в очередь
                    heapq.heappush(target_queue, item)
                    break
                
                ready_tasks.append(item)
            
            if not ready_tasks:
                return None
            
            # Выбираем задачу с наивысшим приоритетом
            selected_item = max(ready_tasks, key=lambda x: x.priority.value)
            
            # Остальные задачи возвращаем в очередь
            for item in ready_tasks:
                if item.id != selected_item.id:
                    heapq.heappush(target_queue, item)
            
            # Перемещаем в очередь обработки
            selected_item.status = QueueStatus.PROCESSING
            selected_item.started_at = current_time
            self.processing_queue[selected_item.id] = selected_item
            
            logger.info(f"Retrieved task {selected_item.id} for processing")
            return selected_item
    
    async def complete_task(self, item_id: str, result_data: Optional[Dict[str, Any]] = None):
        """Завершение задачи"""
        async with self._lock:
            if item_id not in self.processing_queue:
                logger.warning(f"Task {item_id} not found in processing queue")
                return
            
            item = self.processing_queue.pop(item_id)
            item.status = QueueStatus.COMPLETED
            item.completed_at = datetime.now()
            
            # Добавляем в очередь завершенных
            self.completed_queue.append(item)
            
            # Обновляем статистику времени обработки
            if item.started_at:
                processing_time = (item.completed_at - item.started_at).total_seconds()
                self.processing_times[item.metadata.get('task_type', 'unknown')].append(processing_time)
            
            # Ограничиваем размер истории
            if len(self.processing_times[item.metadata.get('task_type', 'unknown')]) > 100:
                self.processing_times[item.metadata.get('task_type', 'unknown')].pop(0)
            
            await self._update_statistics()
            
            logger.info(f"Completed task {item_id}")
    
    async def fail_task(self, item_id: str, error_message: str, 
                       should_retry: bool = True) -> Optional[str]:
        """Отметка задачи как неудачной"""
        async with self._lock:
            if item_id not in self.processing_queue:
                logger.warning(f"Task {item_id} not found in processing queue")
                return None
            
            item = self.processing_queue.pop(item_id)
            item.status = QueueStatus.FAILED
            item.completed_at = datetime.now()
            item.error_message = error_message
            
            # Добавляем в очередь неудачных
            self.failed_queue.append(item)
            
            retry_task_id = None
            
            # Проверяем нужно ли повторить
            if should_retry and item.retry_count < item.max_retries:
                try:
                    retry_task_id = await self.add_retry_task(item_id)
                    item.status = QueueStatus.RETRYING
                    logger.info(f"Scheduled retry for task {item_id}")
                except Exception as e:
                    logger.error(f"Failed to schedule retry for task {item_id}: {e}")
            
            await self._update_statistics()
            
            logger.error(f"Failed task {item_id}: {error_message}")
            return retry_task_id
    
    async def cancel_task(self, item_id: str) -> bool:
        """Отмена задачи"""
        async with self._lock:
            # Проверяем в очереди обработки
            if item_id in self.processing_queue:
                item = self.processing_queue.pop(item_id)
                item.status = QueueStatus.CANCELLED
                self.completed_queue.append(item)
                await self._update_statistics()
                logger.info(f"Cancelled processing task {item_id}")
                return True
            
            # Проверяем в ожидающих очередях
            for queue in [self.pending_queue, self.email_processing_queue, 
                         self.response_generation_queue, self.notification_queue, 
                         self.retry_queue]:
                for i, item in enumerate(queue):
                    if item.id == item_id:
                        item.status = QueueStatus.CANCELLED
                        queue.pop(i)
                        self.completed_queue.append(item)
                        await self._update_statistics()
                        logger.info(f"Cancelled pending task {item_id}")
                        return True
            
            logger.warning(f"Task {item_id} not found for cancellation")
            return False
    
    async def get_item(self, item_id: str) -> Optional[QueueItem]:
        """Получение элемента по ID"""
        async with self._lock:
            # Проверяем в очереди обработки
            if item_id in self.processing_queue:
                return self.processing_queue[item_id]
            
            # Проверяем в ожидающих очередях
            for queue in [self.pending_queue, self.email_processing_queue,
                         self.response_generation_queue, self.notification_queue,
                         self.retry_queue]:
                for item in queue:
                    if item.id == item_id:
                        return item
            
            # Проверяем в завершенных
            for item in self.completed_queue:
                if item.id == item_id:
                    return item
            
            for item in self.failed_queue:
                if item.id == item_id:
                    return item
            
            return None
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Получение статуса очередей"""
        async with self._lock:
            return {
                "pending_queue_size": len(self.pending_queue),
                "processing_queue_size": len(self.processing_queue),
                "completed_queue_size": len(self.completed_queue),
                "failed_queue_size": len(self.failed_queue),
                "specialized_queues": {
                    "email_processing": len(self.email_processing_queue),
                    "response_generation": len(self.response_generation_queue),
                    "notification": len(self.notification_queue),
                    "retry": len(self.retry_queue)
                },
                "statistics": asdict(self.statistics),
                "processing_times": dict(self.processing_times),
                "max_concurrent_processing": self.max_concurrent_processing
            }
    
    async def _update_statistics(self):
        """Обновление статистики"""
        # Подсчитываем элементы по статусам
        pending_count = (len(self.pending_queue) + 
                        len(self.email_processing_queue) + 
                        len(self.response_generation_queue) + 
                        len(self.notification_queue) + 
                        len(self.retry_queue))
        
        processing_count = len(self.processing_queue)
        completed_count = len(self.completed_queue)
        failed_count = len(self.failed_queue)
        
        total_count = pending_count + processing_count + completed_count + failed_count
        
        # Рассчитываем среднее время обработки
        avg_processing_time = 0.0
        all_times = []
        for times in self.processing_times.values():
            all_times.extend(times)
        
        if all_times:
            avg_processing_time = sum(all_times) / len(all_times)
        
        # Рассчитываем процент успеха
        success_rate = 0.0
        if completed_count + failed_count > 0:
            success_rate = (completed_count / (completed_count + failed_count)) * 100
        
        self.statistics = QueueStatistics(
            total_items=total_count,
            pending_items=pending_count,
            processing_items=processing_count,
            completed_items=completed_count,
            failed_items=failed_count,
            retry_items=len(self.retry_queue),
            average_processing_time=avg_processing_time,
            success_rate=success_rate,
            last_updated=datetime.now()
        )
    
    async def cleanup_old_items(self, max_age_hours: int = 24):
        """Очистка старых элементов"""
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Очищаем завершенные элементы
            old_completed = [item for item in self.completed_queue 
                           if item.completed_at and item.completed_at < cutoff_time]
            for item in old_completed:
                self.completed_queue.remove(item)
            
            # Очищаем неудачные элементы
            old_failed = [item for item in self.failed_queue 
                         if item.completed_at and item.completed_at < cutoff_time]
            for item in old_failed:
                self.failed_queue.remove(item)
            
            await self._update_statistics()
            
            logger.info(f"Cleaned up {len(old_completed)} completed and {len(old_failed)} failed items")
    
    async def get_failed_tasks(self, limit: int = 50) -> List[QueueItem]:
        """Получение списка неудачных задач"""
        async with self._lock:
            return list(self.failed_queue)[-limit:]
    
    async def retry_failed_tasks(self, max_retries: int = 3) -> List[str]:
        """Повторная обработка неудачных задач"""
        retry_ids = []
        
        async with self._lock:
            for item in self.failed_queue:
                if item.retry_count < max_retries:
                    try:
                        retry_id = await self.add_retry_task(item.id)
                        retry_ids.append(retry_id)
                    except Exception as e:
                        logger.error(f"Failed to retry task {item.id}: {e}")
        
        logger.info(f"Scheduled {len(retry_ids)} failed tasks for retry")
        return retry_ids


# Глобальный экземпляр менеджера очередей
email_queue_manager = EmailQueueManager()
