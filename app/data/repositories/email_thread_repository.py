"""
Репозиторий для работы с EmailThread моделью
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta

from app.data.models import EmailThread, Email
from app.data.repositories.base_repository import BaseRepository


class EmailThreadRepository(BaseRepository[EmailThread]):
    """Репозиторий для работы с EmailThread"""
    
    def __init__(self, db: Session):
        super().__init__(EmailThread, db)
    
    def get_thread_by_thread_id(self, thread_id: str) -> Optional[EmailThread]:
        """Получает тред по внешнему thread_id"""
        return self.db.query(EmailThread).filter(
            EmailThread.thread_id == thread_id
        ).first()
    
    def get_threads_by_status(self, status: str, limit: int = 100) -> List[EmailThread]:
        """Получает треды по статусу"""
        return self.db.query(EmailThread).filter(
            EmailThread.status == status
        ).order_by(desc(EmailThread.last_email_at)).limit(limit).all()
    
    def get_active_threads(self, limit: int = 100) -> List[EmailThread]:
        """Получает активные треды"""
        return self.get_threads_by_status('active', limit)
    
    def get_closed_threads(self, limit: int = 100) -> List[EmailThread]:
        """Получает закрытые треды"""
        return self.get_threads_by_status('closed', limit)
    
    def get_threads_by_communication(self, communication_id: int) -> List[EmailThread]:
        """Получает треды по communication_id"""
        return self.db.query(EmailThread).filter(
            EmailThread.communication_id == communication_id
        ).order_by(desc(EmailThread.created_at)).all()
    
    def get_recent_threads(self, hours: int = 24, limit: int = 100) -> List[EmailThread]:
        """Получает недавние треды за указанное количество часов"""
        since_time = datetime.now() - timedelta(hours=hours)
        return self.db.query(EmailThread).filter(
            EmailThread.last_email_at >= since_time
        ).order_by(desc(EmailThread.last_email_at)).limit(limit).all()
    
    def search_threads(self, query: str, limit: int = 50) -> List[EmailThread]:
        """Ищет треды по теме или содержимому"""
        search_filter = or_(
            EmailThread.subject.ilike(f"%{query}%"),
            EmailThread.thread_id.ilike(f"%{query}%")
        )
        
        return self.db.query(EmailThread).filter(
            search_filter
        ).order_by(desc(EmailThread.last_email_at)).limit(limit).all()
    
    def update_thread_status(self, thread_id: str, status: str) -> bool:
        """Обновляет статус треда"""
        try:
            thread = self.get_thread_by_thread_id(thread_id)
            if not thread:
                return False
            
            thread.status = status
            thread.updated_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_thread_stats(self, thread_id: str) -> bool:
        """Обновляет статистику треда (количество писем, последнее письмо)"""
        try:
            thread = self.get_thread_by_thread_id(thread_id)
            if not thread:
                return False
            
            # Подсчитываем количество писем в треде
            email_count = self.db.query(Email).filter(
                Email.email_thread_id == thread.id
            ).count()
            
            # Получаем дату последнего письма
            last_email = self.db.query(Email).filter(
                Email.email_thread_id == thread.id
            ).order_by(desc(Email.created_at)).first()
            
            thread.total_emails = email_count
            thread.last_email_at = last_email.created_at if last_email else thread.created_at
            thread.updated_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_thread_with_emails(self, thread_id: str, email_limit: int = 50) -> Optional[Dict[str, Any]]:
        """Получает тред с его письмами"""
        thread = self.get_thread_by_thread_id(thread_id)
        if not thread:
            return None
        
        # Получаем письма треда
        emails = self.db.query(Email).filter(
            Email.email_thread_id == thread.id
        ).order_by(asc(Email.created_at)).limit(email_limit).all()
        
        # Конвертируем в словари
        emails_data = []
        for email in emails:
            emails_data.append({
                'id': email.id,
                'message_id': email.message_id,
                'sender_email': email.sender_email,
                'recipient_email': email.recipient_email,
                'subject': email.subject,
                'body': email.body,
                'direction': email.direction,
                'status': email.status,
                'created_at': email.created_at.isoformat(),
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'delivered_at': email.delivered_at.isoformat() if email.delivered_at else None
            })
        
        return {
            'thread': {
                'id': thread.id,
                'thread_id': thread.thread_id,
                'communication_id': thread.communication_id,
                'subject': thread.subject,
                'status': thread.status,
                'total_emails': thread.total_emails,
                'last_email_at': thread.last_email_at.isoformat() if thread.last_email_at else None,
                'created_at': thread.created_at.isoformat(),
                'updated_at': thread.updated_at.isoformat()
            },
            'emails': emails_data
        }
    
    def get_thread_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Получает статистику по тредам за указанное количество дней"""
        since_date = datetime.now() - timedelta(days=days)
        
        # Общее количество тредов
        total_threads = self.db.query(EmailThread).filter(
            EmailThread.created_at >= since_date
        ).count()
        
        # По статусам
        status_stats = {}
        for status in ['active', 'closed', 'bounced', 'error']:
            count = self.db.query(EmailThread).filter(
                and_(
                    EmailThread.created_at >= since_date,
                    EmailThread.status == status
                )
            ).count()
            status_stats[status] = count
        
        # Среднее количество писем в треде
        avg_emails_per_thread = self.db.query(EmailThread).filter(
            EmailThread.created_at >= since_date
        ).with_entities(EmailThread.total_emails).all()
        
        avg_emails = sum(row[0] for row in avg_emails_per_thread) / len(avg_emails_per_thread) if avg_emails_per_thread else 0
        
        # Самые активные треды
        most_active_threads = self.db.query(EmailThread).filter(
            EmailThread.created_at >= since_date
        ).order_by(desc(EmailThread.total_emails)).limit(10).all()
        
        active_threads_data = []
        for thread in most_active_threads:
            active_threads_data.append({
                'thread_id': thread.thread_id,
                'subject': thread.subject,
                'total_emails': thread.total_emails,
                'status': thread.status,
                'last_email_at': thread.last_email_at.isoformat() if thread.last_email_at else None
            })
        
        return {
            'total_threads': total_threads,
            'status_breakdown': status_stats,
            'average_emails_per_thread': round(avg_emails, 2),
            'most_active_threads': active_threads_data,
            'period_days': days,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_orphaned_threads(self, limit: int = 50) -> List[EmailThread]:
        """Получает треды без связи с коммуникацией"""
        return self.db.query(EmailThread).filter(
            EmailThread.communication_id.is_(None)
        ).order_by(desc(EmailThread.created_at)).limit(limit).all()
    
    def link_thread_to_communication(self, thread_id: str, communication_id: int) -> bool:
        """Связывает тред с коммуникацией"""
        try:
            thread = self.get_thread_by_thread_id(thread_id)
            if not thread:
                return False
            
            thread.communication_id = communication_id
            thread.updated_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e


# Создаем экземпляр репозитория
def get_email_thread_repository(db: Session) -> EmailThreadRepository:
    return EmailThreadRepository(db)
