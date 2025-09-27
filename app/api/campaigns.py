from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.data.models import User, Campaign, CampaignStatus
from app.data.repositories.campaign_repository import CampaignRepository
from app.api.campaign_schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignListResponse,
    CampaignStatusUpdate, CampaignStats, CampaignOptions, get_campaign_options,
    CompanyInfoStep, FundraisingGoalsStep, CampaignStepResponse
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.get("/options", response_model=CampaignOptions)
async def get_campaign_options_endpoint():
    """Get all available options for campaign creation (enums, etc.)"""
    return get_campaign_options()

@router.get("/", response_model=List[CampaignListResponse])
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[CampaignStatus] = Query(None),
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all campaigns for the current user"""
    repo = CampaignRepository(db)
    
    if search or status or industry:
        campaigns = repo.search_campaigns(
            user_id=current_user.id,
            search_term=search,
            status=status,
            industry=industry,
            skip=skip,
            limit=limit
        )
    else:
        campaigns = repo.get_by_user(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    
    return campaigns

@router.get("/stats", response_model=CampaignStats)
async def get_campaign_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get campaign statistics for the current user"""
    repo = CampaignRepository(db)
    stats = repo.get_campaign_stats(current_user.id)
    return CampaignStats(**stats)

@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new campaign"""
    repo = CampaignRepository(db)
    
    # Create campaign
    campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        description=campaign_data.description,
        company_name=campaign_data.company_name,
        company_website=campaign_data.company_website,
        industry=campaign_data.industry,
        current_funding_stage=campaign_data.current_funding_stage,
        team_size=campaign_data.team_size,
        location=campaign_data.location,
        pitch_deck_url=campaign_data.pitch_deck_url,
        target_raise_amount=campaign_data.target_raise_amount,
        fundraising_timeline=campaign_data.fundraising_timeline,
        use_of_funds=[item.value for item in campaign_data.use_of_funds],  # Convert to string list
        previous_funding=campaign_data.previous_funding,
        status=CampaignStatus.DRAFT
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return campaign

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific campaign by ID"""
    repo = CampaignRepository(db)
    campaign = repo.get_user_campaign_by_id(campaign_id, current_user.id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a campaign"""
    repo = CampaignRepository(db)
    campaign = repo.get_user_campaign_by_id(campaign_id, current_user.id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Update fields
    update_data = campaign_update.dict(exclude_unset=True)
    
    # Convert use_of_funds enum list to string list
    if 'use_of_funds' in update_data:
        update_data['use_of_funds'] = [item.value for item in update_data['use_of_funds']]
    
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)
    
    return campaign

@router.patch("/{campaign_id}/status", response_model=CampaignResponse)
async def update_campaign_status(
    campaign_id: int,
    status_update: CampaignStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update campaign status"""
    repo = CampaignRepository(db)
    campaign = repo.update_status(campaign_id, current_user.id, status_update.status)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign"""
    repo = CampaignRepository(db)
    success = repo.delete_user_campaign(campaign_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

@router.post("/bulk-status-update")
async def bulk_update_campaign_status(
    campaign_ids: List[int],
    status_update: CampaignStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk update campaign status"""
    repo = CampaignRepository(db)
    updated_count = repo.bulk_update_status(
        campaign_ids=campaign_ids,
        user_id=current_user.id,
        status=status_update.status
    )
    
    return {"updated_count": updated_count}

# Step-by-step campaign creation endpoints
@router.post("/create/step1", response_model=CampaignStepResponse)
async def create_campaign_step1(
    step_data: CompanyInfoStep,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create campaign step 1: Company Information"""
    # In a real implementation, you might store this in a temporary session or draft
    # For now, we'll create a draft campaign with step 1 data
    
    repo = CampaignRepository(db)
    
    # Create draft campaign with step 1 data
    campaign = Campaign(
        user_id=current_user.id,
        name=step_data.name or "New Campaign",
        description=step_data.description,
        company_name=step_data.company_name,
        company_website=step_data.company_website,
        industry=step_data.industry,
        current_funding_stage=step_data.current_funding_stage,
        team_size=step_data.team_size,
        location=step_data.location,
        pitch_deck_url=step_data.pitch_deck_url,
        # Default values for step 2 (will be updated in step 2)
        target_raise_amount=1000000.0,
        fundraising_timeline="6-12 months",
        use_of_funds=["product_development"],
        previous_funding="none",
        status=CampaignStatus.DRAFT
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return CampaignStepResponse(
        step="company_info",
        data={
            "campaign_id": campaign.id,
            "company_name": campaign.company_name,
            "industry": campaign.industry.value,
            "current_funding_stage": campaign.current_funding_stage.value,
            "team_size": campaign.team_size.value,
            "location": campaign.location,
            "company_website": campaign.company_website,
            "pitch_deck_url": campaign.pitch_deck_url
        },
        next_step="fundraising_goals",
        is_complete=False
    )

@router.put("/{campaign_id}/step2", response_model=CampaignStepResponse)
async def update_campaign_step2(
    campaign_id: int,
    step_data: FundraisingGoalsStep,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update campaign step 2: Fundraising Goals"""
    repo = CampaignRepository(db)
    campaign = repo.get_user_campaign_by_id(campaign_id, current_user.id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Update step 2 data
    campaign.target_raise_amount = step_data.target_raise_amount
    campaign.fundraising_timeline = step_data.fundraising_timeline
    campaign.use_of_funds = [item.value for item in step_data.use_of_funds]
    campaign.previous_funding = step_data.previous_funding
    
    db.commit()
    db.refresh(campaign)
    
    return CampaignStepResponse(
        step="fundraising_goals",
        data={
            "campaign_id": campaign.id,
            "target_raise_amount": campaign.target_raise_amount,
            "fundraising_timeline": campaign.fundraising_timeline.value,
            "use_of_funds": campaign.use_of_funds,
            "previous_funding": campaign.previous_funding.value
        },
        next_step=None,
        is_complete=True
    )

@router.post("/{campaign_id}/launch", response_model=CampaignResponse)
async def launch_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Launch a campaign (change status to active)"""
    repo = CampaignRepository(db)
    campaign = repo.update_status(campaign_id, current_user.id, CampaignStatus.ACTIVE)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign

@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Pause a campaign"""
    repo = CampaignRepository(db)
    campaign = repo.update_status(campaign_id, current_user.id, CampaignStatus.PAUSED)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign

@router.post("/{campaign_id}/complete", response_model=CampaignResponse)
async def complete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete a campaign"""
    repo = CampaignRepository(db)
    campaign = repo.update_status(campaign_id, current_user.id, CampaignStatus.COMPLETED)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign

# File upload endpoint (placeholder)
@router.post("/{campaign_id}/upload-pitch-deck")
async def upload_pitch_deck(
    campaign_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload pitch deck for a campaign"""
    # This is a placeholder implementation
    # In a real implementation, you would:
    # 1. Validate file type and size
    # 2. Upload to cloud storage (S3, etc.)
    # 3. Store the URL in the database
    
    repo = CampaignRepository(db)
    campaign = repo.get_user_campaign_by_id(campaign_id, current_user.id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # For now, just return a mock URL
    file_url = f"/uploads/pitch_decks/{campaign_id}_{file.filename}"
    
    campaign.pitch_deck_url = file_url
    db.commit()
    
    return {
        "file_url": file_url,
        "file_name": file.filename,
        "file_size": file.size
    }
