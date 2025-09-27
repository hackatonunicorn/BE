"""
Репозиторий для работы с Email моделью
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta

from app.data.models import Email
from app.data.repositories.base_repository import BaseRepository


class EmailRepository(BaseRepository[Email]):
    """Репозиторий для работы с Email"""
    
    def __init__(self, db: Session):
        super().__init__(Email, db)
    
    def get_emails_by_thread(self, email_thread_id: int, limit: int = 50) -> List[Email]:
        """Получает все emails в треде"""
        return self.db.query(Email).filter(
            Email.email_thread_id == email_thread_id
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def get_emails_by_message_id(self, message_id: str) -> Optional[Email]:
        """Получает email по message_id"""
        return self.db.query(Email).filter(
            Email.message_id == message_id
        ).first()
    
    def get_emails_by_status(self, status: str, limit: int = 100) -> List[Email]:
        """Получает emails по статусу"""
        return self.db.query(Email).filter(
            Email.status == status
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def get_emails_by_direction(self, direction: str, limit: int = 100) -> List[Email]:
        """Получает emails по направлению (inbound/outbound)"""
        return self.db.query(Email).filter(
            Email.direction == direction
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def get_recent_emails(self, hours: int = 24, limit: int = 100) -> List[Email]:
        """Получает недавние emails за указанное количество часов"""
        since_time = datetime.now() - timedelta(hours=hours)
        return self.db.query(Email).filter(
            Email.created_at >= since_time
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def get_emails_by_recipient(self, recipient_email: str, limit: int = 50) -> List[Email]:
        """Получает emails по email получателя"""
        return self.db.query(Email).filter(
            Email.recipient_email == recipient_email
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def get_emails_by_sender(self, sender_email: str, limit: int = 50) -> List[Email]:
        """Получает emails по email отправителя"""
        return self.db.query(Email).filter(
            Email.sender_email == sender_email
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def search_emails(self, query: str, limit: int = 50) -> List[Email]:
        """Ищет emails по содержимому"""
        search_filter = or_(
            Email.subject.ilike(f"%{query}%"),
            Email.body.ilike(f"%{query}%"),
            Email.sender_email.ilike(f"%{query}%"),
            Email.recipient_email.ilike(f"%{query}%")
        )
        
        return self.db.query(Email).filter(
            search_filter
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def update_email_status(self, email_id: int, status: str, 
                          delivery_status: Optional[Dict[str, Any]] = None) -> bool:
        """Обновляет статус email"""
        try:
            email = self.get_by_id(email_id)
            if not email:
                return False
            
            email.status = status
            email.updated_at = datetime.now()
            
            if delivery_status:
                email.delivery_status = delivery_status
            
            # Обновляем временные метки в зависимости от статуса
            if status == 'delivered':
                email.delivered_at = datetime.now()
            elif status == 'opened':
                email.opened_at = datetime.now()
            elif status == 'clicked':
                email.clicked_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_failed_emails(self, limit: int = 50) -> List[Email]:
        """Получает неудачно отправленные emails"""
        return self.db.query(Email).filter(
            Email.status.in_(['failed', 'bounced'])
        ).order_by(desc(Email.created_at)).limit(limit).all()
    
    def get_pending_emails(self, limit: int = 50) -> List[Email]:
        """Получает ожидающие отправки emails"""
        return self.db.query(Email).filter(
            Email.status == 'pending'
        ).order_by(asc(Email.scheduled_at)).limit(limit).all()
    
    def get_email_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Получает статистику по emails за указанное количество дней"""
        since_date = datetime.now() - timedelta(days=days)
        
        # Общее количество
        total_emails = self.db.query(Email).filter(
            Email.created_at >= since_date
        ).count()
        
        # По статусам
        status_stats = {}
        for status in ['sent', 'delivered', 'failed', 'bounced', 'pending']:
            count = self.db.query(Email).filter(
                and_(
                    Email.created_at >= since_date,
                    Email.status == status
                )
            ).count()
            status_stats[status] = count
        
        # По направлениям
        outbound_count = self.db.query(Email).filter(
            and_(
                Email.created_at >= since_date,
                Email.direction == 'outbound'
            )
        ).count()
        
        inbound_count = self.db.query(Email).filter(
            and_(
                Email.created_at >= since_date,
                Email.direction == 'inbound'
            )
        ).count()
        
        return {
            'total_emails': total_emails,
            'status_breakdown': status_stats,
            'direction_breakdown': {
                'outbound': outbound_count,
                'inbound': inbound_count
            },
            'period_days': days,
            'generated_at': datetime.now().isoformat()
        }


# Создаем экземпляр репозитория
def get_email_repository(db: Session) -> EmailRepository:
    return EmailRepository(db)
