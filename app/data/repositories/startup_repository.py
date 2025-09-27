from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.data.models import Startup
from app.data.repositories.base_repository import BaseRepository


class StartupRepository(BaseRepository[Startup, dict, dict]):
    """Repository for Startup model with specific business logic"""

    def __init__(self):
        super().__init__(Startup)

    def get_by_email(self, db: Session, email: str) -> Optional[Startup]:
        """Get startup by email"""
        return db.query(Startup).filter(Startup.email == email).first()

    def get_by_industry(self, db: Session, industry: str, skip: int = 0, limit: int = 100) -> List[Startup]:
        """Get startups by industry"""
        return (
            db.query(Startup)
            .filter(Startup.industry == industry)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_stage(self, db: Session, stage: str, skip: int = 0, limit: int = 100) -> List[Startup]:
        """Get startups by funding stage"""
        return (
            db.query(Startup)
            .filter(Startup.stage == stage)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_startups(
        self,
        db: Session,
        query: str,
        industry: Optional[str] = None,
        stage: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Startup]:
        """Search startups by name or description with optional filters"""
        search_filter = or_(
            Startup.name.ilike(f"%{query}%"),
            Startup.description.ilike(f"%{query}%")
        )
        
        db_query = db.query(Startup).filter(search_filter)
        
        if industry:
            db_query = db_query.filter(Startup.industry == industry)
        
        if stage:
            db_query = db_query.filter(Startup.stage == stage)
        
        return db_query.offset(skip).limit(limit).all()

    def get_startups_with_communications(self, db: Session, skip: int = 0, limit: int = 100) -> List[Startup]:
        """Get startups that have communications"""
        return (
            db.query(Startup)
            .join(Startup.communications)
            .distinct()
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_startups_without_pitch_analysis(self, db: Session, skip: int = 0, limit: int = 100) -> List[Startup]:
        """Get startups that need pitch deck analysis"""
        return (
            db.query(Startup)
            .filter(
                and_(
                    Startup.pitch_deck_path.isnot(None),
                    Startup.pitch_analysis_result.is_(None)
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_pitch_analysis(self, db: Session, startup_id: int, analysis_result: Dict[str, Any]) -> Optional[Startup]:
        """Update pitch deck analysis result"""
        startup = self.get(db, startup_id)
        if startup:
            startup.pitch_analysis_result = analysis_result
            db.add(startup)
            db.commit()
            db.refresh(startup)
        return startup

    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get startup statistics"""
        total_startups = db.query(Startup).count()
        
        # Count by stage
        stage_stats = (
            db.query(Startup.stage, func.count(Startup.id))
            .group_by(Startup.stage)
            .all()
        )
        
        # Count by industry
        industry_stats = (
            db.query(Startup.industry, func.count(Startup.id))
            .group_by(Startup.industry)
            .all()
        )
        
        # Count with pitch decks
        with_pitch_deck = (
            db.query(Startup)
            .filter(Startup.pitch_deck_path.isnot(None))
            .count()
        )
        
        # Count with analysis
        with_analysis = (
            db.query(Startup)
            .filter(Startup.pitch_analysis_result.isnot(None))
            .count()
        )
        
        return {
            "total_startups": total_startups,
            "by_stage": dict(stage_stats),
            "by_industry": dict(industry_stats),
            "with_pitch_deck": with_pitch_deck,
            "with_analysis": with_analysis
        }


# Create instance for dependency injection
startup_repository = StartupRepository()
