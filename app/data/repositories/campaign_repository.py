from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from app.data.models import Campaign, CampaignStatus, User
from app.data.repositories.base_repository import BaseRepository

class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self, db: Session):
        super().__init__(Campaign, db)
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Campaign]:
        """Get all campaigns for a specific user"""
        return (
            self.db.query(Campaign)
            .filter(Campaign.user_id == user_id)
            .order_by(desc(Campaign.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(self, user_id: int, status: CampaignStatus, skip: int = 0, limit: int = 100) -> List[Campaign]:
        """Get campaigns by status for a specific user"""
        return (
            self.db.query(Campaign)
            .filter(
                and_(
                    Campaign.user_id == user_id,
                    Campaign.status == status
                )
            )
            .order_by(desc(Campaign.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_user_campaign_by_id(self, campaign_id: int, user_id: int) -> Optional[Campaign]:
        """Get a specific campaign by ID that belongs to a user"""
        return (
            self.db.query(Campaign)
            .filter(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.user_id == user_id
                )
            )
            .first()
        )
    
    def update_status(self, campaign_id: int, user_id: int, status: CampaignStatus) -> Optional[Campaign]:
        """Update campaign status"""
        campaign = self.get_user_campaign_by_id(campaign_id, user_id)
        if campaign:
            campaign.status = status
            if status == CampaignStatus.ACTIVE and not campaign.launched_at:
                from datetime import datetime
                campaign.launched_at = datetime.utcnow()
            elif status == CampaignStatus.COMPLETED and not campaign.completed_at:
                from datetime import datetime
                campaign.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(campaign)
        return campaign
    
    def update_metrics(self, campaign_id: int, metrics: Dict[str, int]) -> Optional[Campaign]:
        """Update campaign metrics"""
        campaign = self.get_by_id(campaign_id)
        if campaign:
            if 'sent_count' in metrics:
                campaign.sent_count = metrics['sent_count']
            if 'replied_count' in metrics:
                campaign.replied_count = metrics['replied_count']
            if 'meetings_count' in metrics:
                campaign.meetings_count = metrics['meetings_count']
            
            # Calculate response rate
            if campaign.sent_count > 0:
                campaign.response_rate = (campaign.replied_count / campaign.sent_count) * 100
            else:
                campaign.response_rate = 0.0
            
            self.db.commit()
            self.db.refresh(campaign)
        return campaign
    
    def search_campaigns(
        self, 
        user_id: int, 
        search_term: Optional[str] = None,
        status: Optional[CampaignStatus] = None,
        industry: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Campaign]:
        """Search campaigns with filters"""
        query = self.db.query(Campaign).filter(Campaign.user_id == user_id)
        
        if search_term:
            query = query.filter(
                or_(
                    Campaign.name.ilike(f"%{search_term}%"),
                    Campaign.description.ilike(f"%{search_term}%"),
                    Campaign.company_name.ilike(f"%{search_term}%")
                )
            )
        
        if status:
            query = query.filter(Campaign.status == status)
        
        if industry:
            query = query.filter(Campaign.industry == industry)
        
        return (
            query
            .order_by(desc(Campaign.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_campaign_stats(self, user_id: int) -> Dict[str, Any]:
        """Get campaign statistics for a user"""
        campaigns = self.db.query(Campaign).filter(Campaign.user_id == user_id).all()
        
        stats = {
            'total_campaigns': len(campaigns),
            'active_campaigns': len([c for c in campaigns if c.status == CampaignStatus.ACTIVE]),
            'draft_campaigns': len([c for c in campaigns if c.status == CampaignStatus.DRAFT]),
            'paused_campaigns': len([c for c in campaigns if c.status == CampaignStatus.PAUSED]),
            'completed_campaigns': len([c for c in campaigns if c.status == CampaignStatus.COMPLETED]),
            'total_sent': sum(c.sent_count for c in campaigns),
            'total_replied': sum(c.replied_count for c in campaigns),
            'total_meetings': sum(c.meetings_count for c in campaigns),
            'average_response_rate': 0.0
        }
        
        # Calculate average response rate
        active_campaigns = [c for c in campaigns if c.sent_count > 0]
        if active_campaigns:
            total_response_rate = sum(c.response_rate for c in active_campaigns)
            stats['average_response_rate'] = total_response_rate / len(active_campaigns)
        
        return stats
    
    def get_recent_campaigns(self, user_id: int, limit: int = 5) -> List[Campaign]:
        """Get recent campaigns for a user"""
        return (
            self.db.query(Campaign)
            .filter(Campaign.user_id == user_id)
            .order_by(desc(Campaign.updated_at))
            .limit(limit)
            .all()
        )
    
    def bulk_update_status(self, campaign_ids: List[int], user_id: int, status: CampaignStatus) -> int:
        """Bulk update campaign status"""
        updated_count = (
            self.db.query(Campaign)
            .filter(
                and_(
                    Campaign.id.in_(campaign_ids),
                    Campaign.user_id == user_id
                )
            )
            .update(
                {'status': status},
                synchronize_session=False
            )
        )
        
        self.db.commit()
        return updated_count
    
    def delete_user_campaign(self, campaign_id: int, user_id: int) -> bool:
        """Delete a campaign that belongs to a user"""
        campaign = self.get_user_campaign_by_id(campaign_id, user_id)
        if campaign:
            self.db.delete(campaign)
            self.db.commit()
            return True
        return False
