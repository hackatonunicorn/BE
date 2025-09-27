from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from app.data.models import Communication, Startup, VCFund
from app.data.repositories.base_repository import BaseRepository


class CommunicationRepository(BaseRepository[Communication, dict, dict]):
    """Repository for Communication model with specific business logic"""

    def __init__(self):
        super().__init__(Communication)

    def get_by_startup_id(
        self,
        db: Session,
        startup_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Communication]:
        """Get communications for a specific startup"""
        return (
            db.query(Communication)
            .filter(Communication.startup_id == startup_id)
            .options(joinedload(Communication.vc_fund))
            .order_by(desc(Communication.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_vc_fund_id(
        self,
        db: Session,
        vc_fund_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Communication]:
        """Get communications for a specific VC fund"""
        return (
            db.query(Communication)
            .filter(Communication.vc_fund_id == vc_fund_id)
            .options(joinedload(Communication.startup))
            .order_by(desc(Communication.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Communication]:
        """Get communications by status"""
        return (
            db.query(Communication)
            .filter(Communication.status == status)
            .options(joinedload(Communication.startup), joinedload(Communication.vc_fund))
            .order_by(desc(Communication.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_email_thread_id(self, db: Session, email_thread_id: str) -> Optional[Communication]:
        """Get communication by email thread ID"""
        return (
            db.query(Communication)
            .filter(Communication.email_thread_id == email_thread_id)
            .options(joinedload(Communication.startup), joinedload(Communication.vc_fund))
            .first()
        )

    def get_escalated_communications(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Communication]:
        """Get communications escalated to human"""
        return (
            db.query(Communication)
            .filter(Communication.escalated_to_human == True)
            .options(joinedload(Communication.startup), joinedload(Communication.vc_fund))
            .order_by(desc(Communication.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_communications_needing_followup(
        self,
        db: Session,
        days_threshold: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Communication]:
        """Get communications that need follow-up (no response after threshold days)"""
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        return (
            db.query(Communication)
            .filter(
                and_(
                    Communication.status == "in_progress",
                    Communication.last_message_at < threshold_date,
                    Communication.escalated_to_human == False
                )
            )
            .options(joinedload(Communication.startup), joinedload(Communication.vc_fund))
            .order_by(Communication.last_message_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        db: Session,
        communication_id: int,
        status: str,
        last_message_at: Optional[datetime] = None
    ) -> Optional[Communication]:
        """Update communication status and last message time"""
        communication = self.get(db, communication_id)
        if communication:
            communication.status = status
            if last_message_at:
                communication.last_message_at = last_message_at
            db.add(communication)
            db.commit()
            db.refresh(communication)
        return communication

    def add_generated_email(
        self,
        db: Session,
        communication_id: int,
        email_data: Dict[str, Any]
    ) -> Optional[Communication]:
        """Add generated email to communication"""
        communication = self.get(db, communication_id)
        if communication:
            if communication.generated_emails is None:
                communication.generated_emails = []
            
            # Add timestamp to email data
            email_data["generated_at"] = datetime.utcnow().isoformat()
            communication.generated_emails.append(email_data)
            
            db.add(communication)
            db.commit()
            db.refresh(communication)
        return communication

    def escalate_to_human(
        self,
        db: Session,
        communication_id: int,
        reason: str = "Automatic escalation"
    ) -> Optional[Communication]:
        """Escalate communication to human"""
        communication = self.get(db, communication_id)
        if communication:
            communication.escalated_to_human = True
            
            # Add escalation info to generated_emails
            escalation_info = {
                "type": "escalation",
                "reason": reason,
                "escalated_at": datetime.utcnow().isoformat()
            }
            
            if communication.generated_emails is None:
                communication.generated_emails = []
            communication.generated_emails.append(escalation_info)
            
            db.add(communication)
            db.commit()
            db.refresh(communication)
        return communication

    def get_communication_statistics(self, db: Session) -> Dict[str, Any]:
        """Get communication statistics"""
        total_communications = db.query(Communication).count()
        
        # Status distribution
        status_stats = (
            db.query(Communication.status, func.count(Communication.id))
            .group_by(Communication.status)
            .all()
        )
        
        # Escalated count
        escalated_count = (
            db.query(Communication)
            .filter(Communication.escalated_to_human == True)
            .count()
        )
        
        # Communications with meetings
        with_meetings = (
            db.query(Communication)
            .join(Communication.meetings)
            .distinct()
            .count()
        )
        
        # Recent communications (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_communications = (
            db.query(Communication)
            .filter(Communication.created_at >= thirty_days_ago)
            .count()
        )
        
        # Average response time (days between creation and first meeting)
        avg_response_time = (
            db.query(func.avg(
                func.julianday(func.min(Communication.last_message_at)) - 
                func.julianday(Communication.created_at)
            ))
            .filter(Communication.last_message_at.isnot(None))
            .scalar()
        ) or 0
        
        return {
            "total_communications": total_communications,
            "by_status": dict(status_stats),
            "escalated_count": escalated_count,
            "with_meetings": with_meetings,
            "recent_communications": recent_communications,
            "avg_response_time_days": round(avg_response_time, 2)
        }

    def get_startup_vc_communication(
        self,
        db: Session,
        startup_id: int,
        vc_fund_id: int
    ) -> Optional[Communication]:
        """Get existing communication between startup and VC"""
        return (
            db.query(Communication)
            .filter(
                and_(
                    Communication.startup_id == startup_id,
                    Communication.vc_fund_id == vc_fund_id
                )
            )
            .order_by(desc(Communication.created_at))
            .first()
        )


# Create instance for dependency injection
communication_repository = CommunicationRepository()
