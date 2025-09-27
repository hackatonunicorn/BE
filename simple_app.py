#!/usr/bin/env python3
"""
Упрощенная версия приложения для демонстрации без базы данных
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uvicorn

# Создаем приложение FastAPI
app = FastAPI(
    title="Startup-VC Communication Platform",
    version="1.0.0",
    description="Платформа автоматизации коммуникации стартапов с венчурными капиталистами",
    openapi_url="/api/v1/openapi.json"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшн нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic модели для API
class StartupBase(BaseModel):
    name: str
    industry: str
    stage: str
    description: Optional[str] = None
    email: str  # Упрощенно, без EmailStr в старой версии pydantic
    contact_person: str

class Startup(StartupBase):
    id: int
    created_at: datetime

class VCFundBase(BaseModel):
    name: str
    focus_industries: List[str]
    investment_stages: List[str]
    geography: str
    ticket_size_min: Optional[float] = None
    ticket_size_max: Optional[float] = None
    email: str

class VCFund(VCFundBase):
    id: int
    created_at: datetime

class CommunicationBase(BaseModel):
    startup_id: int
    vc_fund_id: int
    status: str = "initiated"
    email_thread_id: Optional[str] = None

class Communication(CommunicationBase):
    id: int
    created_at: datetime
    last_message_at: Optional[datetime] = None

# Тестовые данные в памяти
mock_startups = [
    {
        "id": 1,
        "name": "TechStartup",
        "industry": "Technology",
        "stage": "Seed",
        "description": "AI-powered customer service automation platform",
        "email": "contact@techstartup.com",
        "contact_person": "John Smith",
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "name": "GreenTech Solutions",
        "industry": "CleanTech",
        "stage": "Series A",
        "description": "Sustainable energy management platform",
        "email": "info@greentech.com",
        "contact_person": "Sarah Johnson",
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "name": "HealthTech Innovations",
        "industry": "HealthTech",
        "stage": "Seed",
        "description": "Telemedicine platform for underserved areas",
        "email": "team@healthtech.com",
        "contact_person": "Dr. Michael Chen",
        "created_at": datetime.now()
    }
]

mock_vc_funds = [
    {
        "id": 1,
        "name": "Innovation Ventures",
        "focus_industries": ["Technology", "AI/ML", "SaaS"],
        "investment_stages": ["Seed", "Series A"],
        "geography": "Silicon Valley, CA",
        "ticket_size_min": 500000,
        "ticket_size_max": 5000000,
        "email": "investments@innovationvc.com",
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "name": "Green Capital Partners",
        "focus_industries": ["CleanTech", "Sustainability", "Energy"],
        "investment_stages": ["Series A", "Series B"],
        "geography": "San Francisco, CA",
        "ticket_size_min": 2000000,
        "ticket_size_max": 15000000,
        "email": "deals@greencapital.com",
        "created_at": datetime.now()
    }
]

mock_communications = [
    {
        "id": 1,
        "startup_id": 1,
        "vc_fund_id": 1,
        "status": "in_progress",
        "email_thread_id": "thread_001",
        "created_at": datetime.now(),
        "last_message_at": datetime.now()
    },
    {
        "id": 2,
        "startup_id": 2,
        "vc_fund_id": 2,
        "status": "meeting_scheduled",
        "email_thread_id": "thread_002",
        "created_at": datetime.now(),
        "last_message_at": datetime.now()
    }
]

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "🚀 Startup-VC Communication Platform API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Startup management",
            "VC fund management", 
            "Communication tracking",
            "AI-powered matching",
            "Email generation"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Startup endpoints
@app.get("/api/v1/startups/", response_model=List[Startup])
async def get_startups():
    """Получить список всех стартапов"""
    return mock_startups

@app.get("/api/v1/startups/{startup_id}", response_model=Startup)
async def get_startup(startup_id: int):
    """Получить стартап по ID"""
    startup = next((s for s in mock_startups if s["id"] == startup_id), None)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@app.post("/api/v1/startups/", response_model=Startup)
async def create_startup(startup_data: StartupBase):
    """Создать новый стартап"""
    new_startup = {
        "id": len(mock_startups) + 1,
        **startup_data.dict(),
        "created_at": datetime.now()
    }
    mock_startups.append(new_startup)
    return new_startup

# VC Fund endpoints
@app.get("/api/v1/vc-funds/", response_model=List[VCFund])
async def get_vc_funds():
    """Получить список всех ВК фондов"""
    return mock_vc_funds

@app.get("/api/v1/vc-funds/{vc_fund_id}", response_model=VCFund)
async def get_vc_fund(vc_fund_id: int):
    """Получить ВК фонд по ID"""
    vc_fund = next((vc for vc in mock_vc_funds if vc["id"] == vc_fund_id), None)
    if not vc_fund:
        raise HTTPException(status_code=404, detail="VC Fund not found")
    return vc_fund

@app.post("/api/v1/vc-funds/", response_model=VCFund)
async def create_vc_fund(vc_fund_data: VCFundBase):
    """Создать новый ВК фонд"""
    new_vc_fund = {
        "id": len(mock_vc_funds) + 1,
        **vc_fund_data.dict(),
        "created_at": datetime.now()
    }
    mock_vc_funds.append(new_vc_fund)
    return new_vc_fund

# Communication endpoints
@app.get("/api/v1/communications/", response_model=List[Communication])
async def get_communications():
    """Получить список всех коммуникаций"""
    return mock_communications

@app.post("/api/v1/communications/", response_model=Communication)
async def create_communication(communication_data: CommunicationBase):
    """Создать новую коммуникацию"""
    new_communication = {
        "id": len(mock_communications) + 1,
        **communication_data.dict(),
        "created_at": datetime.now(),
        "last_message_at": None
    }
    mock_communications.append(new_communication)
    return new_communication

@app.post("/api/v1/communications/generate")
async def generate_email(request_data: Dict[str, Any]):
    """Генерация AI письма (демо версия)"""
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    email_type = request_data.get("email_type", "initial_outreach")
    
    # Находим стартап и ВК
    startup = next((s for s in mock_startups if s["id"] == startup_id), None)
    vc_fund = next((vc for vc in mock_vc_funds if vc["id"] == vc_fund_id), None)
    
    if not startup or not vc_fund:
        raise HTTPException(status_code=404, detail="Startup or VC Fund not found")
    
    # Генерируем демо письмо
    generated_email = {
        "subject": f"Partnership Opportunity - {startup['name']}",
        "content": f"""Dear {vc_fund['name']} Team,

I hope this email finds you well. I'm writing to introduce {startup['name']}, a {startup['stage']}-stage company in the {startup['industry']} sector.

{startup['description']}

Given your focus on {', '.join(vc_fund['focus_industries'])}, I believe there could be a strong strategic fit between our vision and your investment thesis.

Key highlights:
- Industry: {startup['industry']}
- Stage: {startup['stage']}
- Contact: {startup['contact_person']}

I would love the opportunity to discuss how we can create value together. Would you be available for a brief call in the coming weeks?

Best regards,
{startup['name']} Team
{startup['email']}""",
        "email_type": email_type,
        "generated_at": datetime.now(),
        "confidence_score": 8.5
    }
    
    return {"message": "Email generated successfully", "generated_email": generated_email}

# Analytics endpoints
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard():
    """Получить данные дашборда"""
    return {
        "total_startups": len(mock_startups),
        "total_vc_funds": len(mock_vc_funds),
        "total_communications": len(mock_communications),
        "active_communications": len([c for c in mock_communications if c["status"] == "in_progress"]),
        "meetings_scheduled": len([c for c in mock_communications if c["status"] == "meeting_scheduled"]),
        "success_rate": 65.5,
        "top_industries": ["Technology", "CleanTech", "HealthTech"],
        "recent_activity": [
            {"type": "communication_created", "timestamp": datetime.now(), "description": "New communication with Innovation Ventures"},
            {"type": "meeting_scheduled", "timestamp": datetime.now(), "description": "Meeting scheduled with Green Capital"}
        ]
    }

@app.get("/api/v1/analytics/matching/recommendations")
async def get_matching_recommendations():
    """Получить рекомендации по матчингу"""
    recommendations = []
    
    for startup in mock_startups:
        for vc_fund in mock_vc_funds:
            # Простой алгоритм матчинга
            score = 5.0
            
            # Проверяем совпадение индустрии
            if startup["industry"] in vc_fund["focus_industries"]:
                score += 3.0
            
            # Проверяем совпадение стадии
            if startup["stage"] in vc_fund["investment_stages"]:
                score += 2.0
            
            if score >= 7.0:
                recommendations.append({
                    "startup": startup,
                    "vc_fund": vc_fund,
                    "match_score": score,
                    "reasons": [
                        "Industry alignment" if startup["industry"] in vc_fund["focus_industries"] else None,
                        "Stage preference match" if startup["stage"] in vc_fund["investment_stages"] else None,
                        "Geographic proximity"
                    ],
                    "recommended_approach": "initial_outreach"
                })
    
    return {"recommendations": recommendations[:10]}  # Топ 10

if __name__ == "__main__":
    print("🚀 Запуск Startup-VC Communication Platform...")
    print("📋 API документация: http://localhost:8000/docs")
    print("🔍 Альтернативная документация: http://localhost:8000/redoc")
    
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
