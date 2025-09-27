from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    STARTUP = "startup"
    VC_FUND = "vc_fund"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    company_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STARTUP, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    startups = relationship("Startup", back_populates="owner")
    communications_as_startup = relationship("Communication", foreign_keys="Communication.startup_id", back_populates="startup")
    communications_as_vc = relationship("Communication", foreign_keys="Communication.vc_fund_id", back_populates="vc_fund")

class Startup(Base):
    __tablename__ = "startups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    industry = Column(String(50))
    stage = Column(String(20))  # seed, series-a, etc.
    website = Column(String(200))
    email = Column(String(100))
    contact_person = Column(String(100))
    phone = Column(String(20))
    location = Column(String(100))
    funding_goal = Column(Float)
    current_funding = Column(Float, default=0)
    pitch_deck_url = Column(String(500))
    logo_url = Column(String(500))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="startups")
    communications = relationship("Communication", back_populates="startup")
    meetings = relationship("Meeting", back_populates="startup")

class VCFund(Base):
    __tablename__ = "vc_funds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    website = Column(String(200))
    email = Column(String(100))
    contact_person = Column(String(100))
    phone = Column(String(20))
    location = Column(String(100))
    investment_stages = Column(JSON)  # ["seed", "series-a", "series-b"]
    investment_range = Column(JSON)  # {"min": 100000, "max": 5000000}
    industries = Column(JSON)  # ["technology", "healthcare", "fintech"]
    portfolio_companies = Column(JSON)
    recent_investments = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    communications = relationship("Communication", back_populates="vc_fund")
    meetings = relationship("Meeting", back_populates="vc_fund")


class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    communication_id = Column(Integer, ForeignKey("communications.id"), nullable=False)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=False)
    vc_fund_id = Column(Integer, ForeignKey("vc_funds.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    meeting_type = Column(String(20), default="video")  # video, phone, in-person
    meeting_link = Column(String(500))
    location = Column(String(200))
    status = Column(String(20), default="scheduled")  # scheduled, confirmed, completed, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    communication = relationship("Communication", back_populates="meetings")
    startup = relationship("Startup", back_populates="meetings")
    vc_fund = relationship("VCFund", back_populates="meetings")

class EmailThread(Base):
    __tablename__ = "email_threads"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(100), unique=True, nullable=False)
    communication_id = Column(Integer, ForeignKey("communications.id"))
    subject = Column(String(200))
    participants = Column(JSON)  # List of email addresses
    status = Column(String(20), default="active")  # active, closed, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    communication = relationship("Communication")
    emails = relationship("Email", back_populates="thread")

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=False)
    communication_id = Column(Integer, ForeignKey("communications.id"))
    message_id = Column(String(200), unique=True)
    from_email = Column(String(100), nullable=False)
    to_email = Column(String(100), nullable=False)
    cc_emails = Column(JSON)
    bcc_emails = Column(JSON)
    subject = Column(String(200))
    body_text = Column(Text)
    body_html = Column(Text)
    attachments = Column(JSON)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    status = Column(String(20), default="sent")  # sent, delivered, read, failed
    error_message = Column(Text)
    sent_at = Column(DateTime, nullable=False)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    thread = relationship("EmailThread", back_populates="emails")
    communication = relationship("Communication", back_populates="emails")

# Campaign related models
class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class Industry(str, enum.Enum):
    SAAS = "saas"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    AI_ML = "ai_ml"
    BLOCKCHAIN = "blockchain"
    GAMING = "gaming"
    MEDIA = "media"
    REAL_ESTATE = "real_estate"
    TRANSPORTATION = "transportation"
    ENERGY = "energy"
    MANUFACTURING = "manufacturing"
    AGRICULTURE = "agriculture"
    SECURITY = "security"

class FundingStage(str, enum.Enum):
    PRESEED = "preseed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"

class TeamSize(str, enum.Enum):
    SIZE_1_5 = "1-5"
    SIZE_6_20 = "6-20"
    SIZE_21_50 = "21-50"
    SIZE_51_100 = "51-100"
    SIZE_100_PLUS = "100+"

class FundraisingTimeline(str, enum.Enum):
    MONTHS_3_6 = "3-6 months"
    MONTHS_6_12 = "6-12 months"
    MONTHS_12_PLUS = "12+ months"

class PreviousFunding(str, enum.Enum):
    NONE = "none"
    FRIENDS_FAMILY = "friends_family"
    ANGEL_INVESTORS = "angel_investors"
    SEED_ROUND = "seed_round"
    SERIES_A = "series_a"
    SERIES_B_PLUS = "series_b_plus"

class UseOfFunds(str, enum.Enum):
    PRODUCT_DEVELOPMENT = "product_development"
    TEAM_EXPANSION = "team_expansion"
    MARKETING_SALES = "marketing_sales"
    OPERATIONS = "operations"
    TECHNOLOGY_INFRASTRUCTURE = "technology_infrastructure"
    MARKET_EXPANSION = "market_expansion"
    RESEARCH_DEVELOPMENT = "research_development"
    WORKING_CAPITAL = "working_capital"

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=True)
    
    # Campaign basic info
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    
    # Company Information (Step 1)
    company_name = Column(String(200), nullable=False)
    company_website = Column(String(500))
    industry = Column(Enum(Industry), nullable=False)
    current_funding_stage = Column(Enum(FundingStage), nullable=False)
    team_size = Column(Enum(TeamSize), nullable=False)
    location = Column(String(200), nullable=False)
    pitch_deck_url = Column(String(500))  # URL to uploaded file
    
    # Fundraising Goals (Step 2)
    target_raise_amount = Column(Float, nullable=False)  # in USD
    fundraising_timeline = Column(Enum(FundraisingTimeline), nullable=False)
    use_of_funds = Column(JSON, nullable=False)  # Array of UseOfFunds enum values
    previous_funding = Column(Enum(PreviousFunding), nullable=False)
    
    # Campaign metrics
    sent_count = Column(Integer, default=0, nullable=False)
    replied_count = Column(Integer, default=0, nullable=False)
    meetings_count = Column(Integer, default=0, nullable=False)
    response_rate = Column(Float, default=0.0, nullable=False)  # Percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    launched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    startup = relationship("Startup")
    communications = relationship("Communication", back_populates="campaign")

# Update Communication model to include campaign relationship
class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=False)
    vc_fund_id = Column(Integer, ForeignKey("vc_funds.id"), nullable=False)
    status = Column(String(20), default="initialized")  # initialized, sent, responded, closed
    subject = Column(String(200))
    last_message = Column(Text)
    thread_id = Column(String(100), unique=True)
    priority = Column(String(10), default="medium")  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="communications")
    startup = relationship("Startup", back_populates="communications")
    vc_fund = relationship("VCFund", back_populates="communications")
    emails = relationship("Email", back_populates="communication")
    meetings = relationship("Meeting", back_populates="communication")