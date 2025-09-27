from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from app.data.models import Meeting, Communication
from app.data.repositories.base_repository import BaseRepository


class MeetingRepository(BaseRepository[Meeting, dict, dict]):
    """Repository for Meeting model with specific business logic"""

    def __init__(self):
        super().__init__(Meeting)

    def get_by_communication_id(
        self,
        db: Session,
        communication_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get meetings for a specific communication"""
        return (
            db.query(Meeting)
            .filter(Meeting.communication_id == communication_id)
            .order_by(desc(Meeting.scheduled_at))
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
    ) -> List[Meeting]:
        """Get meetings by status"""
        return (
            db.query(Meeting)
            .filter(Meeting.status == status)
            .options(joinedload(Meeting.communication))
            .order_by(Meeting.scheduled_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_upcoming_meetings(
        self,
        db: Session,
        days_ahead: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get upcoming meetings within specified days"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)
        
        return (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.scheduled_at >= start_date,
                    Meeting.scheduled_at <= end_date,
                    Meeting.status == "scheduled"
                )
            )
            .options(joinedload(Meeting.communication))
            .order_by(Meeting.scheduled_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_past_meetings(
        self,
        db: Session,
        days_back: int = 30,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get past meetings within specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        return (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.scheduled_at <= datetime.utcnow(),
                    Meeting.scheduled_at >= cutoff_date
                )
            )
            .options(joinedload(Meeting.communication))
            .order_by(desc(Meeting.scheduled_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_meetings_for_startup(
        self,
        db: Session,
        startup_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get all meetings for a startup"""
        return (
            db.query(Meeting)
            .join(Communication)
            .filter(Communication.startup_id == startup_id)
            .options(joinedload(Meeting.communication))
            .order_by(desc(Meeting.scheduled_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_meetings_for_vc_fund(
        self,
        db: Session,
        vc_fund_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get all meetings for a VC fund"""
        return (
            db.query(Meeting)
            .join(Communication)
            .filter(Communication.vc_fund_id == vc_fund_id)
            .options(joinedload(Meeting.communication))
            .order_by(desc(Meeting.scheduled_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_overdue_meetings(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get meetings that are overdue (scheduled in past but still marked as 'scheduled')"""
        return (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.scheduled_at < datetime.utcnow(),
                    Meeting.status == "scheduled"
                )
            )
            .options(joinedload(Meeting.communication))
            .order_by(Meeting.scheduled_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_meeting_status(
        self,
        db: Session,
        meeting_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> Optional[Meeting]:
        """Update meeting status and optionally add notes"""
        meeting = self.get(db, meeting_id)
        if meeting:
            meeting.status = status
            if notes:
                meeting.notes = notes
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        return meeting

    def reschedule_meeting(
        self,
        db: Session,
        meeting_id: int,
        new_datetime: datetime,
        meeting_link: Optional[str] = None
    ) -> Optional[Meeting]:
        """Reschedule a meeting"""
        meeting = self.get(db, meeting_id)
        if meeting:
            meeting.scheduled_at = new_datetime
            meeting.status = "rescheduled"
            if meeting_link:
                meeting.meeting_link = meeting_link
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        return meeting

    def complete_meeting(
        self,
        db: Session,
        meeting_id: int,
        notes: str,
        outcome: Optional[str] = None
    ) -> Optional[Meeting]:
        """Mark meeting as completed with notes"""
        meeting = self.get(db, meeting_id)
        if meeting:
            meeting.status = "completed"
            meeting.notes = notes
            
            # Update the communication status if meeting was successful
            if outcome == "positive":
                communication = meeting.communication
                if communication:
                    communication.status = "meeting_scheduled"  # or "closed" depending on business logic
                    db.add(communication)
            
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
        return meeting

    def get_meeting_statistics(self, db: Session) -> Dict[str, Any]:
        """Get meeting statistics"""
        total_meetings = db.query(Meeting).count()
        
        # Status distribution
        status_stats = (
            db.query(Meeting.status, func.count(Meeting.id))
            .group_by(Meeting.status)
            .all()
        )
        
        # Upcoming meetings count
        upcoming_meetings = (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.scheduled_at >= datetime.utcnow(),
                    Meeting.status == "scheduled"
                )
            )
            .count()
        )
        
        # Completed meetings this month
        first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.status == "completed",
                    Meeting.scheduled_at >= first_day_of_month
                )
            )
            .count()
        )
        
        # Average meetings per communication
        avg_meetings_per_comm = (
            db.query(func.avg(func.count(Meeting.id)))
            .group_by(Meeting.communication_id)
            .scalar()
        ) or 0
        
        # Success rate (completed / total scheduled)
        total_scheduled = (
            db.query(Meeting)
            .filter(Meeting.status.in_(["scheduled", "completed", "cancelled"]))
            .count()
        )
        
        completed_meetings = (
            db.query(Meeting)
            .filter(Meeting.status == "completed")
            .count()
        )
        
        success_rate = (completed_meetings / total_scheduled * 100) if total_scheduled > 0 else 0
        
        return {
            "total_meetings": total_meetings,
            "by_status": dict(status_stats),
            "upcoming_meetings": upcoming_meetings,
            "completed_this_month": completed_this_month,
            "avg_meetings_per_communication": round(avg_meetings_per_comm, 2),
            "success_rate_percentage": round(success_rate, 2)
        }

    def get_meetings_in_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Meeting]:
        """Get meetings within a specific date range"""
        return (
            db.query(Meeting)
            .filter(
                and_(
                    Meeting.scheduled_at >= start_date,
                    Meeting.scheduled_at <= end_date
                )
            )
            .options(joinedload(Meeting.communication))
            .order_by(Meeting.scheduled_at)
            .offset(skip)
            .limit(limit)
            .all()
        )


# Create instance for dependency injection
meeting_repository = MeetingRepository()
