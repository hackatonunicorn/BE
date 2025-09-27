"""
Communication Orchestrator - Основная логика управления потоками коммуникаций
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from collections import defaultdict

from app.core.database import get_db
from app.data.models import Startup, VCFund, Communication, Meeting
from app.data.repositories import (
    startup_repository, vc_fund_repository, communication_repository, meeting_repository
)

logger = logging.getLogger(__name__)


class CommunicationState(Enum):
    """Состояния коммуникации"""
    INITIALIZED = "initialized"
    SENT_INITIAL_EMAIL = "sent_initial_email"
    AWAITING_RESPONSE = "awaiting_response"
    FOLLOW_UP_SENT = "follow_up_sent"
    MEETING_REQUESTED = "meeting_requested"
    MEETING_SCHEDULED = "meeting_scheduled"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    CLOSED_REJECTED = "closed_rejected"
    CLOSED_SUCCESSFUL = "closed_successful"


class EscalationTrigger(Enum):
    """Триггеры эскалации"""
    TIMEOUT_NO_RESPONSE = "timeout_no_response"
    MEETING_REQUEST = "meeting_request"
    DOCUMENT_REQUEST = "document_request"
    REJECTION_DETECTED = "rejection_detected"
    URGENT_KEYWORDS = "urgent_keywords"
    LOW_CONFIDENCE_CLASSIFICATION = "low_confidence_classification"
    CUSTOM_RULE_TRIGGER = "custom_rule_trigger"


class ActionType(Enum):
    """Типы действий"""
    SEND_EMAIL = "send_email"
    SCHEDULE_FOLLOW_UP = "schedule_follow_up"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    UPDATE_STATUS = "update_status"
    CREATE_MEETING = "create_meeting"
    SEND_NOTIFICATION = "send_notification"
    ARCHIVE_COMMUNICATION = "archive_communication"


@dataclass
class CommunicationAction:
    """Действие в рамках коммуникации"""
    action_type: ActionType
    communication_id: int
    parameters: Dict[str, Any]
    scheduled_at: Optional[datetime] = None
    priority: int = 1  # 1 = highest, 5 = lowest
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class EscalationRule:
    """Правило эскалации"""
    trigger: EscalationTrigger
    conditions: Dict[str, Any]
    action: ActionType
    parameters: Dict[str, Any]
    priority: int = 1
    is_active: bool = True


@dataclass
class CommunicationFlow:
    """Поток коммуникации"""
    communication_id: int
    startup_id: int
    vc_fund_id: int
    current_state: CommunicationState
    state_history: List[Tuple[CommunicationState, datetime]]
    actions_queue: List[CommunicationAction]
    escalation_rules_applied: List[EscalationRule]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CommunicationOrchestrator:
    """
    Основной оркестратор коммуникаций между стартапами и венчурными фондами
    """
    
    def __init__(self):
        # State machine transitions
        self.state_transitions = {
            CommunicationState.INITIALIZED: [
                CommunicationState.SENT_INITIAL_EMAIL,
                CommunicationState.ESCALATED_TO_HUMAN
            ],
            CommunicationState.SENT_INITIAL_EMAIL: [
                CommunicationState.AWAITING_RESPONSE,
                CommunicationState.ESCALATED_TO_HUMAN
            ],
            CommunicationState.AWAITING_RESPONSE: [
                CommunicationState.FOLLOW_UP_SENT,
                CommunicationState.MEETING_REQUESTED,
                CommunicationState.ESCALATED_TO_HUMAN,
                CommunicationState.CLOSED_REJECTED
            ],
            CommunicationState.FOLLOW_UP_SENT: [
                CommunicationState.AWAITING_RESPONSE,
                CommunicationState.MEETING_REQUESTED,
                CommunicationState.ESCALATED_TO_HUMAN,
                CommunicationState.CLOSED_REJECTED
            ],
            CommunicationState.MEETING_REQUESTED: [
                CommunicationState.MEETING_SCHEDULED,
                CommunicationState.ESCALATED_TO_HUMAN,
                CommunicationState.CLOSED_REJECTED
            ],
            CommunicationState.MEETING_SCHEDULED: [
                CommunicationState.CLOSED_SUCCESSFUL,
                CommunicationState.ESCALATED_TO_HUMAN,
                CommunicationState.CLOSED_REJECTED
            ],
            CommunicationState.ESCALATED_TO_HUMAN: [
                CommunicationState.CLOSED_SUCCESSFUL,
                CommunicationState.CLOSED_REJECTED
            ],
            CommunicationState.CLOSED_REJECTED: [],
            CommunicationState.CLOSED_SUCCESSFUL: []
        }
        
        # Escalation rules
        self.escalation_rules = self._initialize_escalation_rules()
        
        # Timeout configurations
        self.timeout_configs = {
            CommunicationState.AWAITING_RESPONSE: timedelta(days=7),
            CommunicationState.FOLLOW_UP_SENT: timedelta(days=5),
            CommunicationState.MEETING_REQUESTED: timedelta(days=3),
            CommunicationState.MEETING_SCHEDULED: timedelta(days=1)
        }
        
        # Active communication flows
        self.active_flows: Dict[int, CommunicationFlow] = {}
        
        # Action queue for processing
        self.action_queue: List[CommunicationAction] = []
        
        # Statistics
        self.orchestration_stats = {
            'total_communications': 0,
            'successful_communications': 0,
            'escalated_communications': 0,
            'rejected_communications': 0,
            'average_flow_duration': 0.0,
            'actions_processed': 0
        }
        
        logger.info("CommunicationOrchestrator initialized")
    
    def _initialize_escalation_rules(self) -> List[EscalationRule]:
        """Инициализация правил эскалации"""
        rules = [
            EscalationRule(
                trigger=EscalationTrigger.TIMEOUT_NO_RESPONSE,
                conditions={'timeout_days': 7},
                action=ActionType.SCHEDULE_FOLLOW_UP,
                parameters={'template_type': 'follow_up_interested'},
                priority=2
            ),
            EscalationRule(
                trigger=EscalationTrigger.MEETING_REQUEST,
                conditions={'classification': 'meeting_request'},
                action=ActionType.ESCALATE_TO_HUMAN,
                parameters={'reason': 'Meeting request requires human review'},
                priority=1
            ),
            EscalationRule(
                trigger=EscalationTrigger.DOCUMENT_REQUEST,
                conditions={'classification': 'request_more_info'},
                action=ActionType.SEND_EMAIL,
                parameters={'template_type': 'follow_up_more_info'},
                priority=2
            ),
            EscalationRule(
                trigger=EscalationTrigger.REJECTION_DETECTED,
                conditions={'classification': 'not_interested'},
                action=ActionType.UPDATE_STATUS,
                parameters={'new_status': 'closed_rejected'},
                priority=3
            ),
            EscalationRule(
                trigger=EscalationTrigger.URGENT_KEYWORDS,
                conditions={'keywords': ['urgent', 'asap', 'immediately']},
                action=ActionType.ESCALATE_TO_HUMAN,
                parameters={'reason': 'Urgent keywords detected'},
                priority=1
            ),
            EscalationRule(
                trigger=EscalationTrigger.LOW_CONFIDENCE_CLASSIFICATION,
                conditions={'confidence_threshold': 0.6},
                action=ActionType.ESCALATE_TO_HUMAN,
                parameters={'reason': 'Low confidence in AI classification'},
                priority=2
            )
        ]
        return rules
    
    async def initiate_communication(self, startup_id: int, fund_ids: List[int]) -> List[int]:
        """
        Инициация коммуникации между стартапом и фондами
        """
        try:
            logger.info(f"Initiating communication for startup {startup_id} with {len(fund_ids)} funds")
            
            # Получаем данные стартапа
            startup_data = await self._get_startup_data(startup_id)
            if not startup_data:
                raise ValueError(f"Startup {startup_id} not found")
            
            # Создаем коммуникации с каждым фондом
            communication_ids = []
            
            for fund_id in fund_ids:
                # Проверяем, нет ли уже активной коммуникации
                existing_communication = await self._get_active_communication(startup_id, fund_id)
                if existing_communication:
                    logger.warning(f"Active communication already exists between startup {startup_id} and fund {fund_id}")
                    continue
                
                # Создаем новую коммуникацию
                communication_id = await self._create_communication(startup_id, fund_id)
                
                # Создаем поток коммуникации
                flow = CommunicationFlow(
                    communication_id=communication_id,
                    startup_id=startup_id,
                    vc_fund_id=fund_id,
                    current_state=CommunicationState.INITIALIZED,
                    state_history=[(CommunicationState.INITIALIZED, datetime.now())],
                    actions_queue=[],
                    escalation_rules_applied=[],
                    metadata={
                        'startup_name': startup_data['name'],
                        'fund_name': await self._get_fund_name(fund_id),
                        'initiated_at': datetime.now().isoformat()
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Добавляем действие отправки начального email
                initial_email_action = CommunicationAction(
                    action_type=ActionType.SEND_EMAIL,
                    communication_id=communication_id,
                    parameters={
                        'template_type': 'initial_outreach',
                        'startup_data': startup_data,
                        'fund_data': await self._get_fund_data(fund_id)
                    },
                    priority=1
                )
                
                flow.actions_queue.append(initial_email_action)
                self.active_flows[communication_id] = flow
                
                communication_ids.append(communication_id)
                
                logger.info(f"Created communication flow {communication_id} for startup {startup_id} and fund {fund_id}")
            
            # Обновляем статистику
            self.orchestration_stats['total_communications'] += len(communication_ids)
            
            return communication_ids
            
        except Exception as e:
            logger.error(f"Error initiating communication for startup {startup_id}: {e}")
            return []
    
    async def process_fund_response(self, communication_id: int, email_content: str) -> bool:
        """
        Обработка ответа от венчурного фонда
        """
        try:
            logger.info(f"Processing fund response for communication {communication_id}")
            
            if communication_id not in self.active_flows:
                logger.error(f"Communication flow {communication_id} not found")
                return False
            
            flow = self.active_flows[communication_id]
            
            # Классифицируем ответ (симуляция AI классификации)
            classification_result = await self._classify_response(email_content)
            
            # Определяем следующее состояние на основе классификации
            new_state = await self._determine_next_state(flow.current_state, classification_result)
            
            # Переводим в новое состояние
            await self._transition_to_state(flow, new_state, classification_result)
            
            # Проверяем триггеры эскалации
            escalation_needed = await self.check_escalation_triggers(communication_id)
            
            if escalation_needed:
                logger.info(f"Escalation triggered for communication {communication_id}")
                await self._escalate_communication(flow, classification_result)
            
            # Добавляем действия в очередь на основе нового состояния
            await self._add_actions_for_state(flow, new_state, classification_result)
            
            logger.info(f"Successfully processed response for communication {communication_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing fund response for communication {communication_id}: {e}")
            return False
    
    async def check_escalation_triggers(self, communication_id: int) -> bool:
        """
        Проверка триггеров эскалации для коммуникации
        """
        try:
            if communication_id not in self.active_flows:
                return False
            
            flow = self.active_flows[communication_id]
            
            # Проверяем каждое правило эскалации
            for rule in self.escalation_rules:
                if not rule.is_active:
                    continue
                
                if await self._evaluate_escalation_rule(flow, rule):
                    logger.info(f"Escalation trigger {rule.trigger.value} activated for communication {communication_id}")
                    flow.escalation_rules_applied.append(rule)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking escalation triggers for communication {communication_id}: {e}")
            return False
    
    async def schedule_follow_ups(self) -> int:
        """
        Планирование follow-up действий для всех активных коммуникаций
        """
        try:
            logger.info("Scheduling follow-ups for active communications")
            
            scheduled_count = 0
            current_time = datetime.now()
            
            for communication_id, flow in self.active_flows.items():
                # Проверяем таймауты
                if await self._check_timeout(flow):
                    # Добавляем follow-up действие
                    follow_up_action = CommunicationAction(
                        action_type=ActionType.SCHEDULE_FOLLOW_UP,
                        communication_id=communication_id,
                        parameters={
                            'template_type': 'follow_up_interested',
                            'reason': 'timeout_no_response'
                        },
                        scheduled_at=current_time + timedelta(hours=1),
                        priority=2
                    )
                    
                    flow.actions_queue.append(follow_up_action)
                    scheduled_count += 1
                    
                    logger.debug(f"Scheduled follow-up for communication {communication_id}")
            
            logger.info(f"Scheduled {scheduled_count} follow-ups")
            return scheduled_count
            
        except Exception as e:
            logger.error(f"Error scheduling follow-ups: {e}")
            return 0
    
    async def generate_status_report(self, startup_id: int) -> Dict[str, Any]:
        """
        Генерация отчета о статусе коммуникаций стартапа
        """
        try:
            logger.info(f"Generating status report for startup {startup_id}")
            
            # Получаем все коммуникации стартапа
            startup_flows = [
                flow for flow in self.active_flows.values()
                if flow.startup_id == startup_id
            ]
            
            if not startup_flows:
                return {"error": f"No active communications found for startup {startup_id}"}
            
            # Анализируем состояния
            state_distribution = defaultdict(int)
            escalation_count = 0
            total_duration = 0.0
            
            for flow in startup_flows:
                state_distribution[flow.current_state.value] += 1
                
                if flow.current_state == CommunicationState.ESCALATED_TO_HUMAN:
                    escalation_count += 1
                
                duration = (datetime.now() - flow.created_at).days
                total_duration += duration
            
            # Получаем топ фонды по активности
            fund_activity = defaultdict(int)
            for flow in startup_flows:
                fund_activity[flow.vc_fund_id] += len(flow.actions_queue)
            
            top_funds = sorted(fund_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            
            report = {
                "startup_id": startup_id,
                "total_communications": len(startup_flows),
                "state_distribution": dict(state_distribution),
                "escalation_count": escalation_count,
                "escalation_rate": escalation_count / len(startup_flows) if startup_flows else 0,
                "average_duration_days": total_duration / len(startup_flows) if startup_flows else 0,
                "most_active_funds": [
                    {
                        "fund_id": fund_id,
                        "action_count": action_count,
                        "fund_name": await self._get_fund_name(fund_id)
                    }
                    for fund_id, action_count in top_funds
                ],
                "recent_activities": await self._get_recent_activities(startup_flows),
                "next_actions": await self._get_pending_actions(startup_flows),
                "generated_at": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating status report for startup {startup_id}: {e}")
            return {"error": str(e)}
    
    async def _transition_to_state(self, flow: CommunicationFlow, new_state: CommunicationState, 
                                 context: Dict[str, Any] = None):
        """Переход в новое состояние"""
        try:
            current_state = flow.current_state
            
            # Проверяем валидность перехода
            if new_state not in self.state_transitions.get(current_state, []):
                logger.warning(f"Invalid state transition from {current_state.value} to {new_state.value}")
                return False
            
            # Обновляем состояние
            flow.current_state = new_state
            flow.state_history.append((new_state, datetime.now()))
            flow.updated_at = datetime.now()
            
            # Обновляем статус в базе данных
            await self._update_communication_status(flow.communication_id, new_state.value)
            
            # Добавляем контекст в метаданные
            if context:
                flow.metadata[f"transition_to_{new_state.value}"] = {
                    'timestamp': datetime.now().isoformat(),
                    'context': context
                }
            
            logger.info(f"Communication {flow.communication_id} transitioned from {current_state.value} to {new_state.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error transitioning to state {new_state.value}: {e}")
            return False
    
    async def _determine_next_state(self, current_state: CommunicationState, 
                                  classification_result: Dict[str, Any]) -> CommunicationState:
        """Определение следующего состояния на основе классификации"""
        
        classification = classification_result.get('classification', 'unclear')
        confidence = classification_result.get('confidence', 0.0)
        
        if current_state == CommunicationState.INITIALIZED:
            return CommunicationState.SENT_INITIAL_EMAIL
        
        elif current_state == CommunicationState.SENT_INITIAL_EMAIL:
            return CommunicationState.AWAITING_RESPONSE
        
        elif current_state == CommunicationState.AWAITING_RESPONSE:
            if classification == 'interested':
                return CommunicationState.FOLLOW_UP_SENT
            elif classification == 'meeting_request':
                return CommunicationState.MEETING_REQUESTED
            elif classification == 'not_interested':
                return CommunicationState.CLOSED_REJECTED
            elif confidence < 0.6:
                return CommunicationState.ESCALATED_TO_HUMAN
            else:
                return CommunicationState.FOLLOW_UP_SENT
        
        elif current_state == CommunicationState.FOLLOW_UP_SENT:
            if classification == 'meeting_request':
                return CommunicationState.MEETING_REQUESTED
            elif classification == 'not_interested':
                return CommunicationState.CLOSED_REJECTED
            else:
                return CommunicationState.AWAITING_RESPONSE
        
        elif current_state == CommunicationState.MEETING_REQUESTED:
            if classification == 'interested' or 'meeting' in classification:
                return CommunicationState.MEETING_SCHEDULED
            else:
                return CommunicationState.ESCALATED_TO_HUMAN
        
        elif current_state == CommunicationState.MEETING_SCHEDULED:
            return CommunicationState.CLOSED_SUCCESSFUL
        
        return current_state  # Остаемся в текущем состоянии
    
    async def _evaluate_escalation_rule(self, flow: CommunicationFlow, rule: EscalationRule) -> bool:
        """Оценка правила эскалации"""
        
        if rule.trigger == EscalationTrigger.TIMEOUT_NO_RESPONSE:
            timeout_days = rule.conditions.get('timeout_days', 7)
            last_activity = flow.state_history[-1][1] if flow.state_history else flow.created_at
            return (datetime.now() - last_activity).days >= timeout_days
        
        elif rule.trigger == EscalationTrigger.MEETING_REQUEST:
            classification = flow.metadata.get('last_classification', {}).get('classification', '')
            return classification == 'meeting_request'
        
        elif rule.trigger == EscalationTrigger.DOCUMENT_REQUEST:
            classification = flow.metadata.get('last_classification', {}).get('classification', '')
            return classification == 'request_more_info'
        
        elif rule.trigger == EscalationTrigger.REJECTION_DETECTED:
            classification = flow.metadata.get('last_classification', {}).get('classification', '')
            return classification == 'not_interested'
        
        elif rule.trigger == EscalationTrigger.URGENT_KEYWORDS:
            email_content = flow.metadata.get('last_email_content', '')
            keywords = rule.conditions.get('keywords', [])
            return any(keyword.lower() in email_content.lower() for keyword in keywords)
        
        elif rule.trigger == EscalationTrigger.LOW_CONFIDENCE_CLASSIFICATION:
            confidence = flow.metadata.get('last_classification', {}).get('confidence', 1.0)
            threshold = rule.conditions.get('confidence_threshold', 0.6)
            return confidence < threshold
        
        return False
    
    async def _escalate_communication(self, flow: CommunicationFlow, context: Dict[str, Any]):
        """Эскалация коммуникации к человеку"""
        try:
            # Переводим в состояние эскалации
            await self._transition_to_state(flow, CommunicationState.ESCALATED_TO_HUMAN, context)
            
            # Добавляем действие уведомления
            notification_action = CommunicationAction(
                action_type=ActionType.SEND_NOTIFICATION,
                communication_id=flow.communication_id,
                parameters={
                    'type': 'escalation',
                    'reason': context.get('reason', 'Manual escalation required'),
                    'communication_id': flow.communication_id,
                    'startup_id': flow.startup_id,
                    'vc_fund_id': flow.vc_fund_id
                },
                priority=1
            )
            
            flow.actions_queue.append(notification_action)
            
            # Обновляем статистику
            self.orchestration_stats['escalated_communications'] += 1
            
            logger.info(f"Communication {flow.communication_id} escalated to human")
            
        except Exception as e:
            logger.error(f"Error escalating communication {flow.communication_id}: {e}")
    
    async def _add_actions_for_state(self, flow: CommunicationFlow, state: CommunicationState, 
                                   context: Dict[str, Any]):
        """Добавление действий для нового состояния"""
        
        if state == CommunicationState.SENT_INITIAL_EMAIL:
            # Никаких дополнительных действий не требуется
            pass
        
        elif state == CommunicationState.FOLLOW_UP_SENT:
            # Планируем ожидание ответа
            await_action = CommunicationAction(
                action_type=ActionType.UPDATE_STATUS,
                communication_id=flow.communication_id,
                parameters={
                    'new_status': 'awaiting_response',
                    'timeout_hours': 168  # 7 дней
                },
                scheduled_at=datetime.now() + timedelta(hours=168),
                priority=3
            )
            flow.actions_queue.append(await_action)
        
        elif state == CommunicationState.MEETING_REQUESTED:
            # Планируем эскалацию через 3 дня
            escalate_action = CommunicationAction(
                action_type=ActionType.ESCALATE_TO_HUMAN,
                communication_id=flow.communication_id,
                parameters={
                    'reason': 'Meeting request timeout',
                    'timeout_days': 3
                },
                scheduled_at=datetime.now() + timedelta(days=3),
                priority=2
            )
            flow.actions_queue.append(escalate_action)
        
        elif state == CommunicationState.MEETING_SCHEDULED:
            # Создаем встречу
            meeting_action = CommunicationAction(
                action_type=ActionType.CREATE_MEETING,
                communication_id=flow.communication_id,
                parameters={
                    'meeting_type': 'video_call',
                    'duration_minutes': 45,
                    'context': context
                },
                priority=1
            )
            flow.actions_queue.append(meeting_action)
        
        elif state in [CommunicationState.CLOSED_REJECTED, CommunicationState.CLOSED_SUCCESSFUL]:
            # Архивируем коммуникацию
            archive_action = CommunicationAction(
                action_type=ActionType.ARCHIVE_COMMUNICATION,
                communication_id=flow.communication_id,
                parameters={
                    'final_status': state.value,
                    'context': context
                },
                priority=5
            )
            flow.actions_queue.append(archive_action)
    
    async def _check_timeout(self, flow: CommunicationFlow) -> bool:
        """Проверка таймаута для потока"""
        try:
            current_state = flow.current_state
            timeout_config = self.timeout_configs.get(current_state)
            
            if not timeout_config:
                return False
            
            last_activity = flow.state_history[-1][1] if flow.state_history else flow.created_at
            time_since_activity = datetime.now() - last_activity
            
            return time_since_activity >= timeout_config
            
        except Exception as e:
            logger.error(f"Error checking timeout for flow {flow.communication_id}: {e}")
            return False
    
    async def _classify_response(self, email_content: str) -> Dict[str, Any]:
        """Классификация ответа (симуляция AI)"""
        # В реальной реализации здесь будет вызов AI классификатора
        content_lower = email_content.lower()
        
        if any(word in content_lower for word in ['interested', 'exciting', 'schedule', 'meeting']):
            return {
                'classification': 'interested',
                'confidence': 0.85,
                'extracted_info': {'keywords': ['interested', 'meeting']}
            }
        elif any(word in content_lower for word in ['not interested', 'not align', 'decline']):
            return {
                'classification': 'not_interested',
                'confidence': 0.90,
                'extracted_info': {'keywords': ['not interested']}
            }
        elif any(word in content_lower for word in ['more information', 'documents', 'details']):
            return {
                'classification': 'request_more_info',
                'confidence': 0.80,
                'extracted_info': {'keywords': ['information', 'documents']}
            }
        elif any(word in content_lower for word in ['meeting', 'call', 'schedule']):
            return {
                'classification': 'meeting_request',
                'confidence': 0.75,
                'extracted_info': {'keywords': ['meeting', 'call']}
            }
        else:
            return {
                'classification': 'unclear',
                'confidence': 0.45,
                'extracted_info': {}
            }
    
    async def _create_communication(self, startup_id: int, vc_fund_id: int) -> int:
        """Создание записи коммуникации в базе данных"""
        try:
            db = next(get_db())
            
            communication = Communication(
                startup_id=startup_id,
                vc_fund_id=vc_fund_id,
                status='initialized',
                email_thread_id=f"thread_{uuid.uuid4()}",
                last_message_at=datetime.now(),
                escalated_to_human=False
            )
            
            db.add(communication)
            db.commit()
            db.refresh(communication)
            
            return communication.id
            
        except Exception as e:
            logger.error(f"Error creating communication: {e}")
            raise
    
    async def _update_communication_status(self, communication_id: int, status: str):
        """Обновление статуса коммуникации в базе данных"""
        try:
            db = next(get_db())
            communication = db.query(Communication).filter(Communication.id == communication_id).first()
            
            if communication:
                communication.status = status
                communication.updated_at = datetime.now()
                db.commit()
                
        except Exception as e:
            logger.error(f"Error updating communication status: {e}")
    
    async def _get_startup_data(self, startup_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных стартапа"""
        try:
            db = next(get_db())
            startup = db.query(Startup).filter(Startup.id == startup_id).first()
            
            if not startup:
                return None
            
            return {
                'id': startup.id,
                'name': startup.name,
                'industry': startup.industry,
                'stage': startup.stage,
                'email': startup.email,
                'contact_person': startup.contact_person,
                'description': startup.description
            }
            
        except Exception as e:
            logger.error(f"Error getting startup data: {e}")
            return None
    
    async def _get_fund_data(self, fund_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных фонда"""
        try:
            db = next(get_db())
            fund = db.query(VCFund).filter(VCFund.id == fund_id).first()
            
            if not fund:
                return None
            
            return {
                'id': fund.id,
                'name': fund.name,
                'focus_industries': fund.focus_industries,
                'investment_stages': fund.investment_stages,
                'email': fund.email,
                'contact_info': fund.contact_info
            }
            
        except Exception as e:
            logger.error(f"Error getting fund data: {e}")
            return None
    
    async def _get_fund_name(self, fund_id: int) -> str:
        """Получение имени фонда"""
        fund_data = await self._get_fund_data(fund_id)
        return fund_data.get('name', f'Fund {fund_id}') if fund_data else f'Fund {fund_id}'
    
    async def _get_active_communication(self, startup_id: int, vc_fund_id: int) -> Optional[Communication]:
        """Получение активной коммуникации"""
        try:
            db = next(get_db())
            communication = db.query(Communication).filter(
                Communication.startup_id == startup_id,
                Communication.vc_fund_id == vc_fund_id,
                Communication.status.notin_(['closed_rejected', 'closed_successful'])
            ).first()
            
            return communication
            
        except Exception as e:
            logger.error(f"Error getting active communication: {e}")
            return None
    
    async def _get_recent_activities(self, flows: List[CommunicationFlow]) -> List[Dict[str, Any]]:
        """Получение недавних активностей"""
        activities = []
        
        for flow in flows:
            if flow.state_history:
                last_state, last_time = flow.state_history[-1]
                activities.append({
                    'communication_id': flow.communication_id,
                    'state': last_state.value,
                    'timestamp': last_time.isoformat(),
                    'fund_name': await self._get_fund_name(flow.vc_fund_id)
                })
        
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    async def _get_pending_actions(self, flows: List[CommunicationFlow]) -> List[Dict[str, Any]]:
        """Получение ожидающих действий"""
        pending_actions = []
        
        for flow in flows:
            for action in flow.actions_queue:
                pending_actions.append({
                    'communication_id': flow.communication_id,
                    'action_type': action.action_type.value,
                    'priority': action.priority,
                    'scheduled_at': action.scheduled_at.isoformat() if action.scheduled_at else None,
                    'fund_name': await self._get_fund_name(flow.vc_fund_id)
                })
        
        return sorted(pending_actions, key=lambda x: (x['priority'], x['scheduled_at'] or ''))
    
    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Получение статистики оркестрации"""
        return self.orchestration_stats.copy()
    
    def add_escalation_rule(self, rule: EscalationRule):
        """Добавление пользовательского правила эскалации"""
        self.escalation_rules.append(rule)
        logger.info(f"Added escalation rule: {rule.trigger.value}")
    
    def get_active_flows(self) -> List[Dict[str, Any]]:
        """Получение активных потоков коммуникации"""
        flows_data = []
        
        for flow in self.active_flows.values():
            flows_data.append({
                'communication_id': flow.communication_id,
                'startup_id': flow.startup_id,
                'vc_fund_id': flow.vc_fund_id,
                'current_state': flow.current_state.value,
                'state_count': len(flow.state_history),
                'pending_actions': len(flow.actions_queue),
                'escalation_rules_applied': len(flow.escalation_rules_applied),
                'created_at': flow.created_at.isoformat(),
                'updated_at': flow.updated_at.isoformat()
            })
        
        return flows_data


# Глобальный экземпляр оркестратора
communication_orchestrator = CommunicationOrchestrator()
