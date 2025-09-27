from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from app.data.models import (
    CampaignStatus, Industry, FundingStage, TeamSize, 
    FundraisingTimeline, PreviousFunding, UseOfFunds
)

# Base schemas
class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None

class CompanyInfoBase(BaseModel):
    company_name: str
    company_website: Optional[str] = None
    industry: Industry
    current_funding_stage: FundingStage
    team_size: TeamSize
    location: str
    pitch_deck_url: Optional[str] = None

class FundraisingGoalsBase(BaseModel):
    target_raise_amount: float
    fundraising_timeline: FundraisingTimeline
    use_of_funds: List[UseOfFunds]
    previous_funding: PreviousFunding

# Create schemas
class CampaignCreate(CampaignBase, CompanyInfoBase, FundraisingGoalsBase):
    @validator('target_raise_amount')
    def validate_raise_amount(cls, v):
        if v < 30000 or v > 10000000:
            raise ValueError('Target raise amount must be between $30K and $10M')
        return v
    
    @validator('use_of_funds')
    def validate_use_of_funds(cls, v):
        if not v:
            raise ValueError('At least one use of funds must be selected')
        return v

# Update schemas
class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    industry: Optional[Industry] = None
    current_funding_stage: Optional[FundingStage] = None
    team_size: Optional[TeamSize] = None
    location: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    target_raise_amount: Optional[float] = None
    fundraising_timeline: Optional[FundraisingTimeline] = None
    use_of_funds: Optional[List[UseOfFunds]] = None
    previous_funding: Optional[PreviousFunding] = None
    status: Optional[CampaignStatus] = None

# Response schemas
class CampaignResponse(CampaignBase):
    id: int
    user_id: int
    startup_id: Optional[int] = None
    status: CampaignStatus
    
    # Company Information
    company_name: str
    company_website: Optional[str] = None
    industry: Industry
    current_funding_stage: FundingStage
    team_size: TeamSize
    location: str
    pitch_deck_url: Optional[str] = None
    
    # Fundraising Goals
    target_raise_amount: float
    fundraising_timeline: FundraisingTimeline
    use_of_funds: List[UseOfFunds]
    previous_funding: PreviousFunding
    
    # Campaign metrics
    sent_count: int
    replied_count: int
    meetings_count: int
    response_rate: float
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    launched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CampaignListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: CampaignStatus
    sent_count: int
    replied_count: int
    meetings_count: int
    response_rate: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Step-by-step creation schemas
class CompanyInfoStep(CampaignBase, CompanyInfoBase):
    pass

class FundraisingGoalsStep(FundraisingGoalsBase):
    pass

class CampaignStepResponse(BaseModel):
    step: str
    data: dict
    next_step: Optional[str] = None
    is_complete: bool = False

# Status update schema
class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus

# File upload schema
class PitchDeckUpload(BaseModel):
    file_url: str
    file_name: str
    file_size: int

# Campaign statistics
class CampaignStats(BaseModel):
    total_campaigns: int
    active_campaigns: int
    draft_campaigns: int
    paused_campaigns: int
    completed_campaigns: int
    total_sent: int
    total_replied: int
    total_meetings: int
    average_response_rate: float

# Enum value schemas for frontend
class EnumOption(BaseModel):
    value: str
    label: str

class CampaignOptions(BaseModel):
    industries: List[EnumOption]
    funding_stages: List[EnumOption]
    team_sizes: List[EnumOption]
    timelines: List[EnumOption]
    previous_funding: List[EnumOption]
    use_of_funds: List[EnumOption]
    statuses: List[EnumOption]

# Helper function to get enum options
def get_campaign_options() -> CampaignOptions:
    return CampaignOptions(
        industries=[
            EnumOption(value=item.value, label=item.value.replace('_', ' ').title())
            for item in Industry
        ],
        funding_stages=[
            EnumOption(value=item.value, label=item.value.replace('_', ' ').title())
            for item in FundingStage
        ],
        team_sizes=[
            EnumOption(value=item.value, label=f"{item.value} employees")
            for item in TeamSize
        ],
        timelines=[
            EnumOption(value=item.value, label=item.value)
            for item in FundraisingTimeline
        ],
        previous_funding=[
            EnumOption(value=item.value, label=item.value.replace('_', ' ').title())
            for item in PreviousFunding
        ],
        use_of_funds=[
            EnumOption(value=item.value, label=item.value.replace('_', ' ').title())
            for item in UseOfFunds
        ],
        statuses=[
            EnumOption(value=item.value, label=item.value.title())
            for item in CampaignStatus
        ]
    )
