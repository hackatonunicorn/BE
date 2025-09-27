from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Startup schemas
class StartupBase(BaseSchema):
    name: str
    industry: str
    stage: str
    description: Optional[str] = None
    email: EmailStr
    contact_person: str
    pitch_deck_path: Optional[str] = None


class StartupCreate(StartupBase):
    pass


class StartupUpdate(BaseSchema):
    name: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = None
    pitch_deck_path: Optional[str] = None
    pitch_analysis_result: Optional[Dict[str, Any]] = None


class Startup(StartupBase):
    id: int
    pitch_analysis_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# VC Fund schemas
class VCFundBase(BaseSchema):
    name: str
    focus_industries: List[str]
    investment_stages: List[str]
    geography: str
    ticket_size_min: Optional[float] = None
    ticket_size_max: Optional[float] = None
    email: EmailStr
    contact_info: Optional[Dict[str, Any]] = None
    matching_criteria: Optional[Dict[str, Any]] = None


class VCFundCreate(VCFundBase):
    pass


class VCFundUpdate(BaseSchema):
    name: Optional[str] = None
    focus_industries: Optional[List[str]] = None
    investment_stages: Optional[List[str]] = None
    geography: Optional[str] = None
    ticket_size_min: Optional[float] = None
    ticket_size_max: Optional[float] = None
    email: Optional[EmailStr] = None
    contact_info: Optional[Dict[str, Any]] = None
    matching_criteria: Optional[Dict[str, Any]] = None


class VCFund(VCFundBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Communication schemas
class CommunicationBase(BaseSchema):
    startup_id: int
    vc_fund_id: int
    status: str = "initiated"
    email_thread_id: Optional[str] = None
    escalated_to_human: bool = False


class CommunicationCreate(CommunicationBase):
    pass


class CommunicationUpdate(BaseSchema):
    status: Optional[str] = None
    email_thread_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    generated_emails: Optional[List[Dict[str, Any]]] = None
    escalated_to_human: Optional[bool] = None


class Communication(CommunicationBase):
    id: int
    last_message_at: Optional[datetime] = None
    generated_emails: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relationships
    startup: Optional[Startup] = None
    vc_fund: Optional[VCFund] = None


# Meeting schemas
class MeetingBase(BaseSchema):
    communication_id: int
    scheduled_at: datetime
    meeting_link: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseSchema):
    scheduled_at: Optional[datetime] = None
    meeting_link: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class Meeting(MeetingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relationships
    communication: Optional[Communication] = None


# Response schemas for API
class StartupListResponse(BaseSchema):
    startups: List[Startup]
    total: int
    skip: int
    limit: int


class VCFundListResponse(BaseSchema):
    vc_funds: List[VCFund]
    total: int
    skip: int
    limit: int


class CommunicationListResponse(BaseSchema):
    communications: List[Communication]
    total: int
    skip: int
    limit: int


class MeetingListResponse(BaseSchema):
    meetings: List[Meeting]
    total: int
    skip: int
    limit: int


# Statistics schemas
class StartupStatistics(BaseSchema):
    total_startups: int
    by_stage: Dict[str, int]
    by_industry: Dict[str, int]
    with_pitch_deck: int
    with_analysis: int


class VCFundStatistics(BaseSchema):
    total_vcs: int
    avg_min_ticket_size: float
    avg_max_ticket_size: float
    by_geography: Dict[str, int]
    with_communications: int


class CommunicationStatistics(BaseSchema):
    total_communications: int
    by_status: Dict[str, int]
    escalated_count: int
    with_meetings: int
    recent_communications: int
    avg_response_time_days: float


class MeetingStatistics(BaseSchema):
    total_meetings: int
    by_status: Dict[str, int]
    upcoming_meetings: int
    completed_this_month: int
    avg_meetings_per_communication: float
    success_rate_percentage: float


# Matching and AI schemas
class MatchingRequest(BaseSchema):
    startup_id: int
    max_results: Optional[int] = 10
    min_score: Optional[float] = 5.0


class MatchingResult(BaseSchema):
    vc_fund: VCFund
    score: float
    reasons: List[str]
    recommended_approach: str


class MatchingResponse(BaseSchema):
    startup: Startup
    matches: List[MatchingResult]
    total_matches: int


class EmailGenerationRequest(BaseSchema):
    startup_id: int
    vc_fund_id: int
    email_type: str  # initial_outreach, follow_up, pitch_deck, meeting_request
    custom_context: Optional[str] = None


class EmailGenerationResponse(BaseSchema):
    subject: str
    content: str
    email_type: str
    generated_at: datetime
    confidence_score: Optional[float] = None


class PitchAnalysisResult(BaseSchema):
    market_size: Optional[str] = None
    competitive_advantages: Optional[List[str]] = None
    funding_needs: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    business_model: Optional[str] = None
    traction_metrics: Optional[Dict[str, Any]] = None
    team_strength: Optional[str] = None
    overall_score: Optional[float] = None
    recommendations: Optional[List[str]] = None
