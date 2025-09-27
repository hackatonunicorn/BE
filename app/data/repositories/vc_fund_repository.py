from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.data.models import VCFund
from app.data.repositories.base_repository import BaseRepository


class VCFundRepository(BaseRepository[VCFund, dict, dict]):
    """Repository for VCFund model with specific business logic"""

    def __init__(self):
        super().__init__(VCFund)

    def get_by_email(self, db: Session, email: str) -> Optional[VCFund]:
        """Get VC fund by email"""
        return db.query(VCFund).filter(VCFund.email == email).first()

    def get_by_geography(self, db: Session, geography: str, skip: int = 0, limit: int = 100) -> List[VCFund]:
        """Get VC funds by geography"""
        return (
            db.query(VCFund)
            .filter(VCFund.geography.ilike(f"%{geography}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_industry_focus(self, db: Session, industry: str, skip: int = 0, limit: int = 100) -> List[VCFund]:
        """Get VC funds that focus on specific industry"""
        return (
            db.query(VCFund)
            .filter(func.json_extract(VCFund.focus_industries, '$').like(f'%"{industry}"%'))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_investment_stage(self, db: Session, stage: str, skip: int = 0, limit: int = 100) -> List[VCFund]:
        """Get VC funds that invest in specific stage"""
        return (
            db.query(VCFund)
            .filter(func.json_extract(VCFund.investment_stages, '$').like(f'%"{stage}"%'))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_ticket_size_range(
        self,
        db: Session,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[VCFund]:
        """Get VC funds by ticket size range"""
        query = db.query(VCFund)
        
        if min_amount is not None:
            query = query.filter(
                or_(
                    VCFund.ticket_size_max >= min_amount,
                    VCFund.ticket_size_max.is_(None)
                )
            )
        
        if max_amount is not None:
            query = query.filter(
                or_(
                    VCFund.ticket_size_min <= max_amount,
                    VCFund.ticket_size_min.is_(None)
                )
            )
        
        return query.offset(skip).limit(limit).all()

    def find_matching_vcs(
        self,
        db: Session,
        startup_industry: str,
        startup_stage: str,
        funding_amount: Optional[float] = None,
        geography: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[VCFund]:
        """Find VCs that match startup criteria"""
        query = db.query(VCFund)
        
        # Match industry focus
        query = query.filter(
            func.json_extract(VCFund.focus_industries, '$').like(f'%"{startup_industry}"%')
        )
        
        # Match investment stage
        query = query.filter(
            func.json_extract(VCFund.investment_stages, '$').like(f'%"{startup_stage}"%')
        )
        
        # Match ticket size if provided
        if funding_amount:
            query = query.filter(
                and_(
                    or_(
                        VCFund.ticket_size_min <= funding_amount,
                        VCFund.ticket_size_min.is_(None)
                    ),
                    or_(
                        VCFund.ticket_size_max >= funding_amount,
                        VCFund.ticket_size_max.is_(None)
                    )
                )
            )
        
        # Match geography if provided
        if geography:
            query = query.filter(VCFund.geography.ilike(f"%{geography}%"))
        
        return query.offset(skip).limit(limit).all()

    def search_vc_funds(
        self,
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[VCFund]:
        """Search VC funds by name"""
        search_filter = VCFund.name.ilike(f"%{query}%")
        
        return (
            db.query(VCFund)
            .filter(search_filter)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_vcs_with_communications(self, db: Session, skip: int = 0, limit: int = 100) -> List[VCFund]:
        """Get VCs that have communications"""
        return (
            db.query(VCFund)
            .join(VCFund.communications)
            .distinct()
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_matching_criteria(
        self,
        db: Session,
        vc_fund_id: int,
        criteria: Dict[str, Any]
    ) -> Optional[VCFund]:
        """Update VC fund matching criteria"""
        vc_fund = self.get(db, vc_fund_id)
        if vc_fund:
            vc_fund.matching_criteria = criteria
            db.add(vc_fund)
            db.commit()
            db.refresh(vc_fund)
        return vc_fund

    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get VC fund statistics"""
        total_vcs = db.query(VCFund).count()
        
        # Average ticket sizes
        avg_min_ticket = db.query(func.avg(VCFund.ticket_size_min)).scalar() or 0
        avg_max_ticket = db.query(func.avg(VCFund.ticket_size_max)).scalar() or 0
        
        # Geography distribution
        geography_stats = (
            db.query(VCFund.geography, func.count(VCFund.id))
            .group_by(VCFund.geography)
            .all()
        )
        
        # VCs with communications
        with_communications = (
            db.query(VCFund)
            .join(VCFund.communications)
            .distinct()
            .count()
        )
        
        return {
            "total_vcs": total_vcs,
            "avg_min_ticket_size": round(avg_min_ticket, 2),
            "avg_max_ticket_size": round(avg_max_ticket, 2),
            "by_geography": dict(geography_stats),
            "with_communications": with_communications
        }


# Create instance for dependency injection
vc_fund_repository = VCFundRepository()
