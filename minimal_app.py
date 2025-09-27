#!/usr/bin/env python3
"""
Минимальная версия FastAPI приложения без сложных зависимостей
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn
import json
import os
import tempfile
import shutil

# Создаем приложение FastAPI
app = FastAPI(
    title="Startup-VC Communication Platform",
    version="1.0.0",
    description="Платформа автоматизации коммуникации стартапов с венчурными капиталистами"
)

# Тестовые данные
startups_data = [
    {
        "id": 1,
        "name": "TechStartup",
        "industry": "Technology",
        "stage": "Seed",
        "description": "AI-powered customer service automation platform",
        "email": "contact@techstartup.com",
        "contact_person": "John Smith",
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": 2,
        "name": "GreenTech Solutions",
        "industry": "CleanTech",
        "stage": "Series A",
        "description": "Sustainable energy management platform",
        "email": "info@greentech.com",
        "contact_person": "Sarah Johnson",
        "created_at": "2024-01-10T14:30:00Z"
    },
    {
        "id": 3,
        "name": "HealthTech Innovations",
        "industry": "HealthTech",
        "stage": "Seed",
        "description": "Telemedicine platform for underserved areas",
        "email": "team@healthtech.com",
        "contact_person": "Dr. Michael Chen",
        "created_at": "2024-01-20T09:15:00Z"
    }
]

vc_funds_data = [
    {
        "id": 1,
        "name": "Innovation Ventures",
        "focus_industries": ["Technology", "AI/ML", "SaaS"],
        "investment_stages": ["Seed", "Series A"],
        "geography": "Silicon Valley, CA",
        "ticket_size_min": 500000,
        "ticket_size_max": 5000000,
        "email": "investments@innovationvc.com",
        "created_at": "2024-01-01T00:00:00Z"
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
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 3,
        "name": "Digital Health Ventures",
        "focus_industries": ["HealthTech", "Biotech", "Digital Health"],
        "investment_stages": ["Seed", "Series A", "Series B"],
        "geography": "Boston, MA",
        "ticket_size_min": 1000000,
        "ticket_size_max": 20000000,
        "email": "investments@healthvc.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
]

communications_data = [
    {
        "id": 1,
        "startup_id": 1,
        "vc_fund_id": 1,
        "status": "in_progress",
        "email_thread_id": "thread_001",
        "created_at": "2024-01-16T10:00:00Z",
        "last_message_at": "2024-01-16T10:00:00Z"
    },
    {
        "id": 2,
        "startup_id": 2,
        "vc_fund_id": 2,
        "status": "meeting_scheduled",
        "email_thread_id": "thread_002",
        "created_at": "2024-01-17T14:30:00Z",
        "last_message_at": "2024-01-18T09:00:00Z"
    }
]

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "🚀 Startup-VC Communication Platform API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Startup management",
            "VC fund management", 
            "Communication tracking",
            "AI-powered matching",
            "Email generation"
        ],
        "endpoints": {
            "startups": "/api/v1/startups/",
            "vc_funds": "/api/v1/vc-funds/",
            "communications": "/api/v1/communications/",
            "dashboard": "/api/v1/analytics/dashboard",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "uptime": "running",
        "version": "1.0.0"
    }

# Startup endpoints
@app.get("/api/v1/startups/")
async def get_startups():
    """Получить список всех стартапов"""
    return {
        "startups": startups_data,
        "total": len(startups_data),
        "message": "Список стартапов успешно получен"
    }

@app.get("/api/v1/startups/{startup_id}")
async def get_startup(startup_id: int):
    """Получить стартап по ID"""
    startup = next((s for s in startups_data if s["id"] == startup_id), None)
    if not startup:
        return {"error": "Startup not found", "startup_id": startup_id}
    return {
        "startup": startup,
        "message": f"Стартап {startup['name']} найден"
    }

@app.post("/api/v1/startups/")
async def create_startup(startup_data: Dict[str, Any]):
    """Создать новый стартап"""
    new_startup = {
        "id": len(startups_data) + 1,
        **startup_data,
        "created_at": datetime.now().isoformat()
    }
    startups_data.append(new_startup)
    return {
        "startup": new_startup,
        "message": f"Стартап {new_startup['name']} успешно создан"
    }

# VC Fund endpoints
@app.get("/api/v1/vc-funds/")
async def get_vc_funds():
    """Получить список всех ВК фондов"""
    return {
        "vc_funds": vc_funds_data,
        "total": len(vc_funds_data),
        "message": "Список ВК фондов успешно получен"
    }

@app.get("/api/v1/vc-funds/{vc_fund_id}")
async def get_vc_fund(vc_fund_id: int):
    """Получить ВК фонд по ID"""
    vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
    if not vc_fund:
        return {"error": "VC Fund not found", "vc_fund_id": vc_fund_id}
    return {
        "vc_fund": vc_fund,
        "message": f"ВК фонд {vc_fund['name']} найден"
    }

@app.post("/api/v1/vc-funds/")
async def create_vc_fund(vc_fund_data: Dict[str, Any]):
    """Создать новый ВК фонд"""
    new_vc_fund = {
        "id": len(vc_funds_data) + 1,
        **vc_fund_data,
        "created_at": datetime.now().isoformat()
    }
    vc_funds_data.append(new_vc_fund)
    return {
        "vc_fund": new_vc_fund,
        "message": f"ВК фонд {new_vc_fund['name']} успешно создан"
    }

# Communication endpoints
@app.get("/api/v1/communications/")
async def get_communications():
    """Получить список всех коммуникаций"""
    # Обогащаем данные информацией о стартапах и ВК
    enriched_communications = []
    for comm in communications_data:
        startup = next((s for s in startups_data if s["id"] == comm["startup_id"]), None)
        vc_fund = next((vc for vc in vc_funds_data if vc["id"] == comm["vc_fund_id"]), None)
        
        enriched_comm = {
            **comm,
            "startup_name": startup["name"] if startup else "Unknown",
            "vc_fund_name": vc_fund["name"] if vc_fund else "Unknown"
        }
        enriched_communications.append(enriched_comm)
    
    return {
        "communications": enriched_communications,
        "total": len(communications_data),
        "message": "Список коммуникаций успешно получен"
    }

@app.post("/api/v1/communications/")
async def create_communication(communication_data: Dict[str, Any]):
    """Создать новую коммуникацию"""
    new_communication = {
        "id": len(communications_data) + 1,
        **communication_data,
        "created_at": datetime.now().isoformat(),
        "last_message_at": None
    }
    communications_data.append(new_communication)
    return {
        "communication": new_communication,
        "message": "Коммуникация успешно создана"
    }

@app.post("/api/v1/communications/generate")
async def generate_email(request_data: Dict[str, Any]):
    """Генерация AI письма (демо версия)"""
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    email_type = request_data.get("email_type", "initial_outreach")
    
    # Находим стартап и ВК
    startup = next((s for s in startups_data if s["id"] == startup_id), None)
    vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
    
    if not startup or not vc_fund:
        return {
            "error": "Startup or VC Fund not found",
            "startup_id": startup_id,
            "vc_fund_id": vc_fund_id
        }
    
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
- Email: {startup['email']}

Investment Range: ${vc_fund['ticket_size_min']:,} - ${vc_fund['ticket_size_max']:,}

I would love the opportunity to discuss how we can create value together. Would you be available for a brief call in the coming weeks?

Best regards,
{startup['name']} Team
{startup['email']}""",
        "email_type": email_type,
        "generated_at": datetime.now().isoformat(),
        "confidence_score": 8.5,
        "startup": startup['name'],
        "vc_fund": vc_fund['name']
    }
    
    return {
        "message": "Email generated successfully",
        "generated_email": generated_email,
        "ai_analysis": {
            "industry_match": startup['industry'] in vc_fund['focus_industries'],
            "stage_match": startup['stage'] in vc_fund['investment_stages'],
            "recommended_follow_up": "3-5 business days"
        }
    }

# Analytics endpoints
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard():
    """Получить данные дашборда"""
    # Подсчитываем статистику
    industries = {}
    stages = {}
    for startup in startups_data:
        industries[startup['industry']] = industries.get(startup['industry'], 0) + 1
        stages[startup['stage']] = stages.get(startup['stage'], 0) + 1
    
    communication_statuses = {}
    for comm in communications_data:
        communication_statuses[comm['status']] = communication_statuses.get(comm['status'], 0) + 1
    
    return {
        "overview": {
            "total_startups": len(startups_data),
            "total_vc_funds": len(vc_funds_data),
            "total_communications": len(communications_data),
            "active_communications": len([c for c in communications_data if c["status"] == "in_progress"]),
            "meetings_scheduled": len([c for c in communications_data if c["status"] == "meeting_scheduled"]),
        },
        "statistics": {
            "startups_by_industry": industries,
            "startups_by_stage": stages,
            "communications_by_status": communication_statuses,
        },
        "metrics": {
            "success_rate": 65.5,
            "avg_response_time_days": 3.2,
            "conversion_rate": 22.8
        },
        "recent_activity": [
            {
                "type": "communication_created",
                "timestamp": datetime.now().isoformat(),
                "description": f"New communication between {startups_data[0]['name']} and {vc_funds_data[0]['name']}"
            },
            {
                "type": "meeting_scheduled",
                "timestamp": datetime.now().isoformat(),
                "description": f"Meeting scheduled: {startups_data[1]['name']} with {vc_funds_data[1]['name']}"
            }
        ],
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/v1/analytics/matching/recommendations")
async def get_matching_recommendations():
    """Получить рекомендации по матчингу"""
    recommendations = []
    
    for startup in startups_data:
        for vc_fund in vc_funds_data:
            # Простой алгоритм матчинга
            score = 5.0
            reasons = []
            
            # Проверяем совпадение индустрии
            if startup["industry"] in vc_fund["focus_industries"]:
                score += 3.0
                reasons.append("Industry alignment")
            
            # Проверяем совпадение стадии
            if startup["stage"] in vc_fund["investment_stages"]:
                score += 2.0
                reasons.append("Stage preference match")
            
            # Добавляем базовые причины
            reasons.append("Geographic considerations")
            
            if score >= 7.0:
                recommendations.append({
                    "startup": {
                        "id": startup["id"],
                        "name": startup["name"],
                        "industry": startup["industry"],
                        "stage": startup["stage"]
                    },
                    "vc_fund": {
                        "id": vc_fund["id"],
                        "name": vc_fund["name"],
                        "geography": vc_fund["geography"]
                    },
                    "match_score": round(score, 1),
                    "reasons": reasons,
                    "recommended_approach": "initial_outreach",
                    "confidence": "high" if score >= 8.0 else "medium"
                })
    
    return {
        "recommendations": recommendations[:10],  # Топ 10
        "total_analyzed": len(startups_data) * len(vc_funds_data),
        "high_confidence_matches": len([r for r in recommendations if r.get("confidence") == "high"]),
        "generated_at": datetime.now().isoformat()
    }

# AI Analysis endpoints
@app.post("/api/v1/ai/analyze-text")
async def analyze_pitch_text(request_data: Dict[str, Any]):
    """Анализ питч-дека из текста (демо версия)"""
    text = request_data.get("text", "")
    
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short for analysis")
    
    # Симуляция AI анализа
    mock_analysis = {
        "industry": "Technology",
        "stage": "Seed",
        "funding_amount": 2000000,
        "market_size": "$50B",
        "key_metrics": {
            "revenue": 500000,
            "users": 10000,
            "growth_rate": 150,
            "other_metrics": {"retention_rate": 85}
        },
        "team_info": {
            "team_size": 8,
            "founders": ["John Smith (CEO)", "Jane Doe (CTO)"],
            "key_backgrounds": ["Ex-Google", "Stanford CS", "10+ years experience"]
        },
        "business_model": "SaaS subscription model with freemium tier",
        "competitive_advantages": [
            "Proprietary AI algorithm",
            "First to market",
            "Strong network effects",
            "Patent pending technology"
        ],
        "problem_solution": {
            "problem": "Manual processes are time-consuming and error-prone",
            "solution": "AI-powered automation platform that reduces manual work by 80%"
        },
        "financial_projections": {
            "revenue_projection": "$10M ARR by Year 3",
            "break_even": "18 months post-funding"
        },
        "use_of_funds": "70% product development, 20% hiring, 10% marketing",
        "confidence_score": 0.85,
        "analysis_method": "demo_simulation",
        "analyzed_at": datetime.now().isoformat(),
        "extracted_text_length": len(text)
    }
    
    return {
        "message": "Pitch deck analysis completed",
        "analysis": mock_analysis,
        "processing_time": "2.3s",
        "features_detected": [
            "Financial projections",
            "Team information", 
            "Market analysis",
            "Competitive landscape",
            "Business model"
        ]
    }

@app.post("/api/v1/ai/analyze-file")
async def analyze_pitch_file(file: UploadFile = File(...)):
    """Анализ питч-дека из файла (демо версия)"""
    
    # Проверяем тип файла
    allowed_extensions = ['.pdf', '.pptx', '.docx', '.txt']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Проверяем размер файла (максимум 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    
    try:
        # Сохраняем файл временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # Симуляция извлечения текста
        if file_extension == '.txt':
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
        else:
            # Для других форматов симулируем извлечение
            extracted_text = f"Extracted content from {file.filename}\n\nThis is a demo simulation of text extraction from {file_extension} file.\n\nThe file contains typical pitch deck information including market analysis, financial projections, team information, and business model description."
        
        # Удаляем временный файл
        os.unlink(temp_file_path)
        
        # Симуляция AI анализа
        mock_analysis = {
            "industry": "HealthTech",
            "stage": "Series A", 
            "funding_amount": 5000000,
            "market_size": "$120B",
            "key_metrics": {
                "revenue": 1200000,
                "users": 50000,
                "growth_rate": 200,
                "other_metrics": {
                    "customer_acquisition_cost": 150,
                    "lifetime_value": 2400,
                    "churn_rate": 5
                }
            },
            "team_info": {
                "team_size": 15,
                "founders": ["Dr. Sarah Johnson (CEO)", "Michael Chen (CTO)", "Lisa Wong (COO)"],
                "key_backgrounds": ["Harvard Medical", "Ex-Apple", "McKinsey & Company"]
            },
            "business_model": "B2B SaaS with usage-based pricing and enterprise contracts",
            "competitive_advantages": [
                "Proprietary medical algorithms",
                "FDA approved technology",
                "Exclusive partnerships with hospitals",
                "10 patents pending"
            ],
            "problem_solution": {
                "problem": "Medical diagnosis takes too long and is prone to human error",
                "solution": "AI-powered diagnostic platform that reduces diagnosis time by 60% and improves accuracy by 25%"
            },
            "financial_projections": {
                "revenue_projection": "$25M ARR by Year 3",
                "break_even": "12 months post-funding"
            },
            "use_of_funds": "50% R&D, 25% sales & marketing, 15% hiring, 10% regulatory compliance",
            "confidence_score": 0.92,
            "analysis_method": "file_processing_demo",
            "analyzed_at": datetime.now().isoformat(),
            "source_file": file.filename,
            "extracted_text_length": len(extracted_text)
        }
        
        return {
            "message": f"Successfully analyzed {file.filename}",
            "file_info": {
                "filename": file.filename,
                "file_type": file_extension,
                "file_size": file.size or 0,
                "content_type": file.content_type
            },
            "analysis": mock_analysis,
            "processing_time": "4.7s",
            "extraction_quality": "high"
        }
        
    except Exception as e:
        # Убираем временный файл в случае ошибки
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/v1/ai/capabilities")
async def get_ai_capabilities():
    """Получить информацию о возможностях AI анализа"""
    return {
        "supported_formats": [
            {
                "extension": ".pdf",
                "description": "PDF documents",
                "max_size": "10MB"
            },
            {
                "extension": ".pptx", 
                "description": "PowerPoint presentations",
                "max_size": "10MB"
            },
            {
                "extension": ".docx",
                "description": "Word documents", 
                "max_size": "10MB"
            },
            {
                "extension": ".txt",
                "description": "Plain text files",
                "max_size": "10MB"
            }
        ],
        "analysis_features": [
            "Industry classification",
            "Development stage detection",
            "Funding amount extraction",
            "Market size analysis",
            "Key metrics identification",
            "Team information extraction",
            "Business model analysis",
            "Competitive advantages",
            "Financial projections",
            "Use of funds breakdown"
        ],
        "ai_models": [
            {
                "name": "Claude API",
                "status": "available",
                "description": "Advanced text analysis and content understanding"
            },
            {
                "name": "Rule-based extraction",
                "status": "available",
                "description": "Pattern matching and keyword extraction"
            }
        ],
        "confidence_scoring": {
            "range": "0.0 - 1.0",
            "description": "Higher scores indicate more reliable analysis"
        },
        "processing_time": {
            "text_analysis": "1-3 seconds",
            "file_analysis": "3-10 seconds depending on file size"
        }
    }

# Enhanced Email Generation endpoints with EmailGenerator
@app.post("/api/v1/emails/generate-initial")
async def generate_initial_email(request_data: Dict[str, Any]):
    """Генерация персонализированного первичного письма"""
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    
    # Находим стартап и ВК
    startup = next((s for s in startups_data if s["id"] == startup_id), None)
    vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
    
    if not startup or not vc_fund:
        raise HTTPException(status_code=404, detail="Startup or VC Fund not found")
    
    # Симуляция работы EmailGenerator
    mock_email = {
        "subject": f"Strategic Partnership Opportunity - {startup['name']}",
        "body": f"""Dear {vc_fund.get('contact_info', {}).get('partner_name', vc_fund['name'] + ' Team')},

I hope this email finds you well. I'm {startup.get('contact_person', 'the founder')}, CEO of {startup['name']}.

{startup['name']} is a {startup['stage']} {startup['industry']} company that {startup['description']}.

Given {vc_fund['name']}'s focus on {', '.join(vc_fund['focus_industries'])} and investments in {', '.join(vc_fund['investment_stages'])} companies, I believe there's a compelling strategic fit.

Key highlights:
• {startup['industry']} expertise with proven market traction
• {startup['stage']} stage aligns with your investment criteria
• Strong leadership team with domain experience
• Clear path to scale within your ${vc_fund.get('ticket_size_min', 1000000):,} - ${vc_fund.get('ticket_size_max', 10000000):,} investment range

I'd welcome the opportunity to discuss how {startup['name']} could be a valuable addition to your portfolio. Would you have 20 minutes for a brief call this week?

Best regards,
{startup.get('contact_person', 'Founder')}
CEO, {startup['name']}
{startup.get('email', 'founder@company.com')}""",
        "generated_by": "enhanced_email_generator",
        "generated_at": datetime.now().isoformat(),
        "personalization_score": 9.2,
        "alignment_factors": [
            f"Industry focus: {startup['industry']} matches VC portfolio",
            f"Stage alignment: {startup['stage']} fits investment criteria",
            f"Geographic fit: {vc_fund.get('geography', 'Global')} presence",
            f"Ticket size: Within ${vc_fund.get('ticket_size_min', 0):,} - ${vc_fund.get('ticket_size_max', 0):,} range"
        ]
    }
    
    return {
        "message": "Personalized initial email generated successfully",
        "email": mock_email,
        "startup": {"id": startup_id, "name": startup["name"]},
        "vc_fund": {"id": vc_fund_id, "name": vc_fund["name"]},
        "processing_time": "2.1s"
    }

@app.post("/api/v1/emails/generate-follow-up")
async def generate_follow_up_email(request_data: Dict[str, Any]):
    """Генерация follow-up письма"""
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    previous_context = request_data.get("previous_context", "")
    vc_response = request_data.get("vc_response", "")
    intent = request_data.get("intent", "follow_up")
    
    startup = next((s for s in startups_data if s["id"] == startup_id), None)
    vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
    
    if not startup or not vc_fund:
        raise HTTPException(status_code=404, detail="Startup or VC Fund not found")
    
    # Симуляция follow-up письма
    follow_up_intents = {
        "no_response": "gentle reminder with additional value",
        "interested": "provide more detailed information",
        "concerns": "address specific concerns raised",
        "meeting_request": "propose specific meeting times"
    }
    
    mock_email = {
        "subject": f"Re: {startup['name']} - {follow_up_intents.get(intent, 'Follow-up')}",
        "body": f"""Dear {vc_fund.get('contact_info', {}).get('partner_name', vc_fund['name'] + ' Team')},

I wanted to follow up on my previous email regarding {startup['name']}.

{f"Thank you for your response. {vc_response}" if vc_response else "I hope you had a chance to review our initial introduction."}

Since our last communication, we've made significant progress:
• Signed 3 new enterprise customers, bringing MRR to $45K
• Achieved 40% month-over-month growth in user acquisition
• Secured strategic partnership with industry leader
• Expanded team with senior VP of Sales from leading competitor

Given {vc_fund['name']}'s portfolio companies in {startup['industry']}, I believe {startup['name']} presents a compelling opportunity for synergies and cross-portfolio value creation.

{f"Based on your {intent}, " if intent != "no_response" else ""}I'd love to schedule a 20-minute call to discuss how we might work together. I'm available most afternoons this week and next.

Thank you for your time and consideration.

Best regards,
{startup.get('contact_person', 'Founder')}
CEO, {startup['name']}
{startup.get('email', 'founder@company.com')}""",
        "generated_by": "follow_up_generator",
        "generated_at": datetime.now().isoformat(),
        "context_analysis": {
            "previous_interaction": bool(previous_context),
            "vc_response_received": bool(vc_response),
            "follow_up_intent": intent,
            "timing": "optimal - 7 days after initial contact"
        }
    }
    
    return {
        "message": "Follow-up email generated successfully",
        "email": mock_email,
        "context": {
            "previous_context": previous_context or "Initial outreach sent",
            "vc_response": vc_response or "No response received",
            "intent": intent
        }
    }

@app.post("/api/v1/emails/generate-meeting-request")
async def generate_meeting_request_email(request_data: Dict[str, Any]):
    """Генерация письма с запросом встречи"""
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    meeting_purpose = request_data.get("purpose", "pitch presentation")
    proposed_duration = request_data.get("duration", "30 minutes")
    
    startup = next((s for s in startups_data if s["id"] == startup_id), None)
    vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
    
    if not startup or not vc_fund:
        raise HTTPException(status_code=404, detail="Startup or VC Fund not found")
    
    mock_email = {
        "subject": f"Meeting Request - {startup['name']} Presentation",
        "body": f"""Dear {vc_fund.get('contact_info', {}).get('partner_name', vc_fund['name'] + ' Team')},

Thank you for your interest in {startup['name']}. I'd like to schedule a meeting to present our business opportunity in detail.

Proposed Meeting Details:
• Purpose: {meeting_purpose}
• Duration: {proposed_duration}
• Format: In-person or video call (your preference)
• Materials: Live demo + investor presentation

Agenda Overview:
1. Company overview and market opportunity (10 min)
2. Product demonstration and key features (10 min)
3. Business model and financial projections (5 min)
4. Q&A and next steps discussion (5 min)

I'm available for the meeting:
• This week: Tuesday 2-5 PM, Wednesday 10 AM-12 PM, Friday 9-11 AM
• Next week: Monday-Wednesday, flexible timing

Location options:
• Your office: {vc_fund.get('geography', 'Your location')}
• Video call: Zoom/Google Meet/Teams
• Neutral location: Coffee meeting or co-working space

Please let me know what works best for your schedule. I'm happy to accommodate your preferred time and format.

Looking forward to the opportunity to present {startup['name']} to your team.

Best regards,
{startup.get('contact_person', 'Founder')}
CEO, {startup['name']}
{startup.get('email', 'founder@company.com')}
Mobile: +1 (555) 123-4567""",
        "generated_by": "meeting_request_generator",
        "generated_at": datetime.now().isoformat(),
        "meeting_metadata": {
            "purpose": meeting_purpose,
            "duration": proposed_duration,
            "agenda_included": True,
            "multiple_time_options": True,
            "flexible_format": True
        }
    }
    
    return {
        "message": "Meeting request email generated successfully",
        "email": mock_email,
        "meeting_details": {
            "purpose": meeting_purpose,
            "duration": proposed_duration,
            "format_options": ["in-person", "video_call", "phone_call"]
        }
    }

@app.get("/api/v1/emails/templates")
async def get_email_templates():
    """Получить список доступных шаблонов писем"""
    return {
        "templates": [
            {
                "type": "initial_outreach",
                "name": "Initial Outreach",
                "description": "First contact email to introduce startup to VC",
                "use_case": "Cold outreach to new VC prospects",
                "personalization_level": "high"
            },
            {
                "type": "follow_up",
                "name": "Follow-up Email",
                "description": "Follow-up after initial contact or previous interaction",
                "use_case": "Re-engage VCs who haven't responded or continue conversation",
                "personalization_level": "medium"
            },
            {
                "type": "meeting_request",
                "name": "Meeting Request",
                "description": "Request for in-person or video meeting",
                "use_case": "Schedule pitch presentation or discussion",
                "personalization_level": "medium"
            },
            {
                "type": "pitch_deck_sharing",
                "name": "Pitch Deck Sharing",
                "description": "Email for sharing investor materials",
                "use_case": "Send pitch deck after initial interest shown",
                "personalization_level": "low"
            },
            {
                "type": "update_email",
                "name": "Company Update",
                "description": "Regular updates on company progress",
                "use_case": "Maintain investor interest with progress updates",
                "personalization_level": "low"
            }
        ],
        "personalization_features": [
            "VC name and title personalization",
            "Industry and stage alignment",
            "Portfolio company synergies",
            "Investment criteria matching",
            "Geographic relevance",
            "Ticket size alignment"
        ],
        "ai_capabilities": {
            "claude_api": "Advanced content generation and personalization",
            "template_based": "Rule-based generation with placeholders",
            "hybrid_approach": "Combines AI with template structure for reliability"
        }
    }

@app.post("/api/v1/emails/preview")
async def preview_email_generation(request_data: Dict[str, Any]):
    """Предварительный просмотр генерации письма без финального создания"""
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    email_type = request_data.get("email_type", "initial_outreach")
    
    startup = next((s for s in startups_data if s["id"] == startup_id), None)
    vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
    
    if not startup or not vc_fund:
        raise HTTPException(status_code=404, detail="Startup or VC Fund not found")
    
    # Анализ совместимости для предварительного просмотра
    alignment_analysis = {
        "industry_match": startup['industry'] in vc_fund['focus_industries'],
        "stage_match": startup['stage'] in vc_fund['investment_stages'],
        "geographic_relevance": "Global" in vc_fund.get('geography', '') or "compatible",
        "ticket_size_fit": True,  # Упрощено для демо
        "overall_score": 8.5
    }
    
    preview = {
        "email_type": email_type,
        "personalization_elements": {
            "recipient": vc_fund.get('contact_info', {}).get('partner_name', 'Investment Team'),
            "fund_name": vc_fund['name'],
            "startup_name": startup['name'],
            "industry_focus": startup['industry'],
            "stage_alignment": startup['stage']
        },
        "content_strategy": {
            "opening": f"Personal greeting to {vc_fund.get('contact_info', {}).get('partner_name', 'team')}",
            "value_proposition": f"{startup['industry']} solution addressing market gap",
            "alignment_factors": [
                f"Industry match: {startup['industry']} in VC focus areas",
                f"Stage fit: {startup['stage']} investment criteria",
                f"Portfolio synergy: Potential with existing investments"
            ],
            "call_to_action": "Meeting request with specific time options"
        },
        "expected_response_rate": f"{alignment_analysis['overall_score'] * 4:.1f}%",
        "estimated_generation_time": "2-4 seconds",
        "alignment_analysis": alignment_analysis
    }
    
    return {
        "message": "Email generation preview prepared",
        "preview": preview,
        "recommendation": "High potential for positive response based on alignment factors"
    }

    # Email Management endpoints
    @app.post("/api/v1/emails/send")
    async def send_email(request_data: Dict[str, Any]):
        """Отправка email от имени стартапа"""
        to_email = request_data.get("to_email")
        subject = request_data.get("subject")
        body = request_data.get("body")
        startup_id = request_data.get("startup_id")
        vc_fund_id = request_data.get("vc_fund_id")
        html_body = request_data.get("html_body")
        thread_id = request_data.get("thread_id")
        
        if not all([to_email, subject, body, startup_id]):
            raise HTTPException(status_code=400, detail="Missing required fields: to_email, subject, body, startup_id")
        
        # Находим стартап
        startup = next((s for s in startups_data if s["id"] == startup_id), None)
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")
        
        # Генерируем прокси-email
        proxy_email = f"{startup['name'].lower().replace(' ', '')}.{startup_id}@startup-connect.com"
        
        # Симуляция отправки email
        message_id = f"<{uuid.uuid4()}@startup-connect.com>"
        
        mock_result = {
            "status": "sent",
            "message_id": message_id,
            "proxy_email": proxy_email,
            "thread_id": thread_id or message_id,
            "to_email": to_email,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "delivery_status": "accepted",
            "provider": "demo_smtp"
        }
        
        return {
            "message": "Email sent successfully",
            "result": mock_result,
            "startup": {"id": startup_id, "name": startup["name"]},
            "processing_time": "1.2s"
        }
    
    @app.get("/api/v1/emails/receive")
    async def receive_emails():
        """Получение новых входящих emails"""
        # Симуляция получения emails
        mock_emails = [
            {
                "message_id": f"<reply-{uuid.uuid4()}@example.com>",
                "sender_email": "partner@innovationvc.com",
                "sender_name": "Sarah Johnson",
                "subject": "Re: TechStartup Partnership Opportunity",
                "body": "Thank you for reaching out. We're interested in learning more about TechStartup. Could you please send us your pitch deck and schedule a call for next week?",
                "date": datetime.now().isoformat(),
                "thread_id": "<original-message-id@startup-connect.com>",
                "direction": "inbound",
                "classification": {
                    "type": "interested",
                    "confidence": 0.92,
                    "suggested_action": "Send pitch deck and propose meeting times"
                }
            },
            {
                "message_id": f"<reply-{uuid.uuid4()}@example.com>",
                "sender_email": "info@growthcapital.com",
                "sender_name": "Growth Capital Team",
                "subject": "Re: AI Customer Service Platform",
                "body": "Thank you for your email. While your product sounds interesting, it's not currently a fit for our investment focus. We wish you the best of luck.",
                "date": datetime.now().isoformat(),
                "thread_id": "<original-message-id2@startup-connect.com>",
                "direction": "inbound",
                "classification": {
                    "type": "not_interested",
                    "confidence": 0.89,
                    "suggested_action": "Update CRM status and focus on other prospects"
                }
            }
        ]
        
        return {
            "message": f"Retrieved {len(mock_emails)} new emails",
            "emails": mock_emails,
            "processing_time": "2.1s"
        }
    
    @app.post("/api/v1/emails/parse")
    async def parse_email_content(request_data: Dict[str, Any]):
        """Парсинг содержимого email"""
        raw_email = request_data.get("raw_email", {})
        
        if not raw_email:
            raise HTTPException(status_code=400, detail="Raw email data is required")
        
        # Симуляция парсинга
        parsed_data = {
            "message_id": raw_email.get("message_id", f"<{uuid.uuid4()}@example.com>"),
            "sender_email": raw_email.get("sender_email", ""),
            "sender_name": raw_email.get("sender_name", ""),
            "recipient_email": raw_email.get("recipient_email", ""),
            "subject": raw_email.get("subject", ""),
            "body": raw_email.get("body", ""),
            "html_body": raw_email.get("html_body"),
            "direction": "inbound",
            "thread_info": {
                "message_id": raw_email.get("message_id", f"<{uuid.uuid4()}@example.com>"),
                "in_reply_to": raw_email.get("in_reply_to"),
                "references": raw_email.get("references"),
                "is_reply": bool(raw_email.get("in_reply_to")),
                "conversation_id": f"conv-{uuid.uuid4()}"
            },
            "contact_info": {
                "sender_email": raw_email.get("sender_email", ""),
                "sender_name": raw_email.get("sender_name", ""),
                "phones": [],
                "calendar_links": [],
                "social_links": []
            },
            "auto_reply_detected": False,
            "bounce_detected": False,
            "classification": {
                "type": "interested",
                "confidence": 0.85,
                "suggested_action": "Send requested materials"
            },
            "extracted_entities": {
                "dates": ["next week"],
                "money": [],
                "companies": [],
                "people": [],
                "locations": [],
                "urls": [],
                "emails": []
            },
            "clean_body": raw_email.get("body", ""),
            "quoted_text": "",
            "signature": ""
        }
        
        return {
            "message": "Email content parsed successfully",
            "parsed_data": parsed_data,
            "processing_time": "0.8s"
        }
    
    @app.put("/api/v1/emails/threads/{thread_id}/status")
    async def update_thread_status(thread_id: str, request_data: Dict[str, Any]):
        """Обновление статуса email треда"""
        status = request_data.get("status")
        notes = request_data.get("notes")
        
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        valid_statuses = ["active", "closed", "bounced", "error"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Симуляция обновления статуса
        result = {
            "thread_id": thread_id,
            "status": status,
            "notes": notes,
            "updated_at": datetime.now().isoformat(),
            "success": True
        }
        
        return {
            "message": f"Thread {thread_id} status updated to {status}",
            "result": result
        }
    
    @app.get("/api/v1/emails/threads/{thread_id}")
    async def get_thread_emails(thread_id: str):
        """Получение всех emails в треде"""
        # Симуляция получения emails треда
        mock_thread_emails = [
            {
                "id": 1,
                "message_id": f"<{thread_id}>",
                "sender_email": "techstartup.1@startup-connect.com",
                "recipient_email": "partner@innovationvc.com",
                "subject": "Partnership Opportunity - TechStartup",
                "body": "Dear Partner,\n\nWe would like to introduce TechStartup to your investment portfolio...",
                "direction": "outbound",
                "status": "delivered",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "sent_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "delivered_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "id": 2,
                "message_id": f"<reply-{uuid.uuid4()}@example.com>",
                "sender_email": "partner@innovationvc.com",
                "recipient_email": "techstartup.1@startup-connect.com",
                "subject": "Re: Partnership Opportunity - TechStartup",
                "body": "Thank you for reaching out. We're interested in learning more...",
                "direction": "inbound",
                "status": "received",
                "created_at": datetime.now().isoformat(),
                "sent_at": None,
                "delivered_at": None
            }
        ]
        
        return {
            "thread_id": thread_id,
            "emails": mock_thread_emails,
            "total_emails": len(mock_thread_emails),
            "last_email_at": mock_thread_emails[-1]["created_at"]
        }
    
    @app.get("/api/v1/emails/statistics")
    async def get_email_statistics():
        """Получение статистики по emails"""
        # Симуляция статистики
        stats = {
            "total_emails": 156,
            "status_breakdown": {
                "sent": 45,
                "delivered": 42,
                "failed": 2,
                "bounced": 1,
                "pending": 0
            },
            "direction_breakdown": {
                "outbound": 78,
                "inbound": 78
            },
            "thread_statistics": {
                "total_threads": 34,
                "active_threads": 28,
                "closed_threads": 6,
                "average_emails_per_thread": 4.6
            },
            "period_days": 30,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "message": "Email statistics retrieved",
            "statistics": stats
        }
    
    @app.post("/api/v1/emails/webhook/{provider}")
    async def handle_email_webhook(provider: str, request_data: Dict[str, Any]):
        """Обработка webhook от email провайдера"""
        # Симуляция обработки webhook
        webhook_data = {
            "provider": provider,
            "event_type": request_data.get("event_type", "delivered"),
            "message_id": request_data.get("message_id", f"<{uuid.uuid4()}@example.com>"),
            "status": request_data.get("status", "delivered"),
            "timestamp": datetime.now().isoformat(),
            "raw_data": request_data
        }
        
        # Симуляция обновления статуса
        result = {
            "message_id": webhook_data["message_id"],
            "status": webhook_data["status"],
            "updated_at": webhook_data["timestamp"],
            "provider": provider
        }
        
        return {
            "message": f"Webhook from {provider} processed successfully",
            "result": result
        }

    # Email Pipeline endpoints
    @app.get("/api/v1/pipeline/status")
    async def get_pipeline_status():
        """Получение статуса email pipeline"""
        # Симуляция статуса pipeline
        mock_status = {
            "pipeline_enabled": True,
            "auto_response_enabled": True,
            "escalation_enabled": True,
            "statistics": {
                "total_processed": 156,
                "successful_responses": 89,
                "escalated_cases": 12,
                "failed_operations": 8,
                "last_run": datetime.now().isoformat(),
                "average_processing_time": 2.3
            },
            "scheduler_status": {
                "scheduler_running": True,
                "jobs": [
                    {
                        "id": "email_processing",
                        "name": "Process Incoming Emails",
                        "next_run_time": (datetime.now() + timedelta(minutes=5)).isoformat(),
                        "trigger": "interval[0:05:00]"
                    },
                    {
                        "id": "retry_processing",
                        "name": "Retry Failed Email Processing",
                        "next_run_time": (datetime.now() + timedelta(minutes=10)).isoformat(),
                        "trigger": "interval[0:10:00]"
                    }
                ]
            },
            "queue_status": {
                "pending_queue_size": 3,
                "processing_queue_size": 2,
                "completed_queue_size": 145,
                "failed_queue_size": 6,
                "specialized_queues": {
                    "email_processing": 2,
                    "response_generation": 1,
                    "notification": 0,
                    "retry": 3
                }
            },
            "health_status": "healthy"
        }
        
        return {
            "message": "Pipeline status retrieved successfully",
            "status": mock_status
        }
    
    @app.post("/api/v1/pipeline/trigger")
    async def trigger_pipeline_processing():
        """Ручной запуск обработки pipeline"""
        # Симуляция ручного запуска
        mock_result = {
            "message": "Email processing triggered manually",
            "task_id": f"manual-{uuid.uuid4()}",
            "timestamp": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(minutes=2)).isoformat()
        }
        
        return {
            "message": "Pipeline processing triggered successfully",
            "result": mock_result
        }
    
    @app.post("/api/v1/pipeline/retry")
    async def retry_failed_operations():
        """Повторная обработка неудачных операций"""
        # Симуляция повторной обработки
        mock_result = {
            "message": "Retried 5 failed operations",
            "retry_task_ids": [
                f"retry-{uuid.uuid4()}",
                f"retry-{uuid.uuid4()}",
                f"retry-{uuid.uuid4()}"
            ],
            "failed_tasks_count": 5,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "message": "Failed operations retry initiated",
            "result": mock_result
        }
    
    @app.get("/api/v1/pipeline/statistics")
    async def get_pipeline_statistics():
        """Получение детальной статистики pipeline"""
        # Симуляция статистики
        stats = {
            "processing_statistics": {
                "total_emails_processed": 1247,
                "successful_classifications": 1189,
                "failed_classifications": 58,
                "classification_accuracy": 95.3,
                "average_processing_time": 1.8,
                "peak_processing_time": 4.2
            },
            "response_statistics": {
                "auto_responses_generated": 234,
                "auto_responses_sent": 221,
                "response_generation_failures": 13,
                "average_response_time": 2.1,
                "response_types": {
                    "follow_up": 89,
                    "document_request": 67,
                    "meeting_request": 45,
                    "rejection_handling": 20
                }
            },
            "escalation_statistics": {
                "total_escalations": 89,
                "escalation_reasons": {
                    "meeting_request": 34,
                    "document_request": 28,
                    "rejection": 15,
                    "urgent_keywords": 8,
                    "low_confidence": 4
                },
                "escalation_resolution_time": 4.5
            },
            "queue_statistics": {
                "total_tasks_processed": 1567,
                "pending_tasks": 3,
                "processing_tasks": 2,
                "completed_tasks": 1456,
                "failed_tasks": 106,
                "success_rate": 93.2,
                "average_queue_wait_time": 0.8
            },
            "performance_metrics": {
                "uptime_percentage": 99.8,
                "error_rate": 1.2,
                "throughput_per_hour": 156,
                "peak_throughput": 234,
                "memory_usage_mb": 245.6,
                "cpu_usage_percentage": 12.3
            },
            "period": {
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return {
            "message": "Pipeline statistics retrieved successfully",
            "statistics": stats
        }
    
    @app.post("/api/v1/pipeline/jobs/{job_id}/trigger")
    async def trigger_specific_job(job_id: str):
        """Ручной запуск конкретной задачи"""
        valid_jobs = ["email_processing", "retry_processing", "cleanup", "monitoring"]
        
        if job_id not in valid_jobs:
            raise HTTPException(status_code=400, detail=f"Invalid job ID. Valid jobs: {valid_jobs}")
        
        # Симуляция запуска задачи
        mock_result = {
            "job_id": job_id,
            "status": "triggered",
            "next_run_time": datetime.now().isoformat(),
            "estimated_duration": "2-5 minutes",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "message": f"Job {job_id} triggered successfully",
            "result": mock_result
        }
    
    @app.post("/api/v1/pipeline/jobs/{job_id}/pause")
    async def pause_job(job_id: str):
        """Приостановка задачи"""
        valid_jobs = ["email_processing", "retry_processing", "cleanup", "monitoring"]
        
        if job_id not in valid_jobs:
            raise HTTPException(status_code=400, detail=f"Invalid job ID. Valid jobs: {valid_jobs}")
        
        # Симуляция приостановки
        mock_result = {
            "job_id": job_id,
            "status": "paused",
            "paused_at": datetime.now().isoformat(),
            "message": f"Job {job_id} has been paused"
        }
        
        return {
            "message": f"Job {job_id} paused successfully",
            "result": mock_result
        }
    
    @app.post("/api/v1/pipeline/jobs/{job_id}/resume")
    async def resume_job(job_id: str):
        """Возобновление задачи"""
        valid_jobs = ["email_processing", "retry_processing", "cleanup", "monitoring"]
        
        if job_id not in valid_jobs:
            raise HTTPException(status_code=400, detail=f"Invalid job ID. Valid jobs: {valid_jobs}")
        
        # Симуляция возобновления
        mock_result = {
            "job_id": job_id,
            "status": "resumed",
            "resumed_at": datetime.now().isoformat(),
            "next_run_time": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "message": f"Job {job_id} has been resumed"
        }
        
        return {
            "message": f"Job {job_id} resumed successfully",
            "result": mock_result
        }
    
    @app.get("/api/v1/pipeline/health")
    async def get_pipeline_health():
        """Проверка здоровья pipeline"""
        # Симуляция проверки здоровья
        health_status = {
            "overall_status": "healthy",
            "components": {
                "scheduler": {
                    "status": "running",
                    "last_check": datetime.now().isoformat(),
                    "uptime": "99.8%"
                },
                "queue_manager": {
                    "status": "operational",
                    "queue_sizes": {
                        "pending": 3,
                        "processing": 2,
                        "completed": 1456
                    },
                    "memory_usage": "45MB"
                },
                "email_processor": {
                    "status": "active",
                    "processing_rate": "156 emails/hour",
                    "error_rate": "1.2%"
                },
                "database": {
                    "status": "connected",
                    "response_time": "12ms",
                    "connection_pool": "8/10"
                }
            },
            "alerts": [],
            "recommendations": [
                "System is operating normally",
                "Consider increasing queue capacity if processing volume increases"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "message": "Pipeline health check completed",
            "health": health_status
        }

    # Email Templates endpoints
    @app.get("/api/v1/templates/types")
    async def get_template_types():
        """Получение доступных типов шаблонов"""
        template_types = [
            {
                "type": "initial_outreach",
                "name": "Initial Outreach",
                "description": "Первичное обращение к венчурному фонду",
                "use_case": "First contact with potential investors"
            },
            {
                "type": "follow_up_interested",
                "name": "Follow-up (Interested)",
                "description": "Последующее письмо при проявлении интереса",
                "use_case": "Follow-up when VC shows interest"
            },
            {
                "type": "follow_up_more_info",
                "name": "Follow-up (More Info)",
                "description": "Отправка запрошенной информации",
                "use_case": "Providing requested documents and information"
            },
            {
                "type": "meeting_confirmation",
                "name": "Meeting Confirmation",
                "description": "Подтверждение встречи",
                "use_case": "Confirming scheduled meeting details"
            },
            {
                "type": "thank_you_meeting",
                "name": "Thank You (Meeting)",
                "description": "Благодарность после встречи",
                "use_case": "Follow-up after successful meeting"
            }
        ]
        
        return {
            "message": "Template types retrieved successfully",
            "template_types": template_types
        }
    
    @app.post("/api/v1/templates/render")
    async def render_template(request_data: Dict[str, Any]):
        """Рендеринг email шаблона с персонализацией"""
        template_type = request_data.get("template_type")
        vc_fund_data = request_data.get("vc_fund_data", {})
        startup_data = request_data.get("startup_data", {})
        format_type = request_data.get("format_type", "both")
        variant_id = request_data.get("variant_id")
        ab_test_id = request_data.get("ab_test_id")
        
        if not template_type:
            raise HTTPException(status_code=400, detail="template_type is required")
        
        # Симуляция рендеринга шаблона
        mock_result = {
            "template_type": template_type,
            "variant_id": variant_id or f"default-{uuid.uuid4()}",
            "format": format_type,
            "subject": f"Partnership Opportunity - {startup_data.get('name', 'Our Company')}",
            "html_content": f"""<!DOCTYPE html>
<html>
<head><title>Partnership Opportunity</title></head>
<body>
    <h1>Dear {vc_fund_data.get('name', 'Investment Partner')},</h1>
    <p>I hope this email finds you well. I'm {startup_data.get('contact_person', 'The Team')}, CEO of <strong>{startup_data.get('name', 'Our Company')}</strong>.</p>
    <p>{startup_data.get('name', 'Our Company')} is a {startup_data.get('stage', 'Seed')} {startup_data.get('industry', 'Technology')} company that is revolutionizing the industry.</p>
    <p>Best regards,<br>{startup_data.get('contact_person', 'The Team')}</p>
</body>
</html>""",
            "text_content": f"""Dear {vc_fund_data.get('name', 'Investment Partner')},

I hope this email finds you well. I'm {startup_data.get('contact_person', 'The Team')}, CEO of {startup_data.get('name', 'Our Company')}.

{startup_data.get('name', 'Our Company')} is a {startup_data.get('stage', 'Seed')} {startup_data.get('industry', 'Technology')} company that is revolutionizing the industry.

Best regards,
{startup_data.get('contact_person', 'The Team')}""",
            "personalization_score": 0.85,
            "ab_test_id": ab_test_id,
            "rendered_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Template {template_type} rendered successfully",
            "result": mock_result
        }
    
    @app.get("/api/v1/templates/preview/{template_type}")
    async def preview_template(template_type: str, format_type: str = "both"):
        """Предварительный просмотр шаблона"""
        # Симуляция данных для предварительного просмотра
        mock_data = {
            "vc_fund_data": {
                "name": "Innovation Ventures",
                "focus_industries": ["Technology", "Fintech"],
                "recent_investments": ["TechStartup", "FinanceApp"],
                "ticket_size_min": 500000,
                "ticket_size_max": 5000000
            },
            "startup_data": {
                "name": "Demo Startup",
                "industry": "Technology",
                "stage": "Seed",
                "contact_person": "John Smith",
                "email": "john@demostartup.com",
                "description": "AI-powered customer service platform"
            }
        }
        
        # Симуляция рендеринга
        mock_result = {
            "template_type": template_type,
            "format": format_type,
            "subject": f"Partnership Opportunity - {mock_data['startup_data']['name']}",
            "html_content": f"""<h1>Preview of {template_type} Template</h1>
<p>Dear {mock_data['vc_fund_data']['name']},</p>
<p>This is a preview of the {template_type} template.</p>""",
            "text_content": f"Preview of {template_type} Template\nDear {mock_data['vc_fund_data']['name']},\nThis is a preview of the {template_type} template.",
            "preview_data": mock_data
        }
        
        return {
            "message": f"Template {template_type} preview generated",
            "preview": mock_result
        }
    
    @app.get("/api/v1/templates/statistics")
    async def get_template_statistics():
        """Получение статистики использования шаблонов"""
        stats = {
            "total_renders": 1247,
            "templates_usage": {
                "initial_outreach": {
                    "renders": 456,
                    "avg_personalization_score": 0.82,
                    "success_rate": 0.78
                },
                "follow_up_interested": {
                    "renders": 234,
                    "avg_personalization_score": 0.89,
                    "success_rate": 0.85
                },
                "follow_up_more_info": {
                    "renders": 189,
                    "avg_personalization_score": 0.91,
                    "success_rate": 0.88
                },
                "meeting_confirmation": {
                    "renders": 156,
                    "avg_personalization_score": 0.94,
                    "success_rate": 0.92
                },
                "thank_you_meeting": {
                    "renders": 212,
                    "avg_personalization_score": 0.87,
                    "success_rate": 0.83
                }
            },
            "personalization_metrics": {
                "avg_personalization_score": 0.87,
                "high_personalization_rate": 0.73,
                "low_personalization_rate": 0.12
            },
            "performance_metrics": {
                "avg_render_time": 0.8,
                "cache_hit_rate": 0.85,
                "error_rate": 0.02
            },
            "period": {
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return {
            "message": "Template statistics retrieved successfully",
            "statistics": stats
        }
    
    @app.post("/api/v1/templates/ab-tests")
    async def create_ab_test(request_data: Dict[str, Any]):
        """Создание A/B теста для шаблонов"""
        name = request_data.get("name")
        description = request_data.get("description")
        template_types = request_data.get("template_types", [])
        variants = request_data.get("variants", [])
        primary_metric = request_data.get("primary_metric", "reply_rate")
        
        if not name or not variants:
            raise HTTPException(status_code=400, detail="name and variants are required")
        
        # Симуляция создания A/B теста
        test_id = f"test-{uuid.uuid4()}"
        mock_result = {
            "test_id": test_id,
            "name": name,
            "description": description,
            "template_types": template_types,
            "variants": variants,
            "primary_metric": primary_metric,
            "status": "draft",
            "traffic_allocation": {
                variant.get("id", f"variant-{i}"): 1.0 / len(variants)
                for i, variant in enumerate(variants)
            },
            "created_at": datetime.now().isoformat(),
            "estimated_duration": "14 days",
            "min_sample_size": 100
        }
        
        return {
            "message": f"A/B test '{name}' created successfully",
            "test": mock_result
        }
    
    @app.get("/api/v1/templates/ab-tests/{test_id}/results")
    async def get_ab_test_results(test_id: str):
        """Получение результатов A/B теста"""
        # Симуляция результатов A/B теста
        mock_results = {
            "test_info": {
                "id": test_id,
                "name": "Subject Line A/B Test",
                "description": "Testing different subject lines for initial outreach",
                "status": "active",
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "primary_metric": "reply_rate"
            },
            "variants": [
                {
                    "id": "variant-a",
                    "name": "Control",
                    "description": "Original subject line",
                    "traffic_allocation": 0.5
                },
                {
                    "id": "variant-b", 
                    "name": "Test",
                    "description": "New subject line with personalization",
                    "traffic_allocation": 0.5
                }
            ],
            "results": {
                "variant-a": {
                    "name": "Control",
                    "description": "Original subject line",
                    "metrics": {
                        "reply_rate": {
                            "value": 0.12,
                            "sample_size": 150,
                            "confidence_interval": [0.08, 0.16]
                        },
                        "open_rate": {
                            "value": 0.45,
                            "sample_size": 150,
                            "confidence_interval": [0.38, 0.52]
                        }
                    },
                    "total_metrics": 2
                },
                "variant-b": {
                    "name": "Test",
                    "description": "New subject line with personalization",
                    "metrics": {
                        "reply_rate": {
                            "value": 0.18,
                            "sample_size": 148,
                            "confidence_interval": [0.13, 0.23]
                        },
                        "open_rate": {
                            "value": 0.52,
                            "sample_size": 148,
                            "confidence_interval": [0.45, 0.59]
                        }
                    },
                    "total_metrics": 2
                }
            },
            "statistical_significance": {
                "variant-a": {
                    "p_value": 0.85,
                    "is_significant": False,
                    "confidence_level": 0.95
                },
                "variant-b": {
                    "p_value": 0.03,
                    "is_significant": True,
                    "confidence_level": 0.95
                }
            },
            "recommendation": "Variant B (Test) shows 50% improvement in reply rate with statistical significance. Recommend implementing the new subject line."
        }
        
        return {
            "message": f"A/B test {test_id} results retrieved",
            "results": mock_results
        }
    
    @app.post("/api/v1/templates/ab-tests/{test_id}/start")
    async def start_ab_test(test_id: str):
        """Запуск A/B теста"""
        mock_result = {
            "test_id": test_id,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "estimated_end_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "traffic_allocation": {
                "variant-a": 0.5,
                "variant-b": 0.5
            }
        }
        
        return {
            "message": f"A/B test {test_id} started successfully",
            "result": mock_result
        }
    
    @app.post("/api/v1/templates/ab-tests/{test_id}/complete")
    async def complete_ab_test(test_id: str):
        """Завершение A/B теста"""
        mock_result = {
            "test_id": test_id,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "winner": "variant-b",
            "improvement": "50% increase in reply rate",
            "statistical_significance": "95% confidence level",
            "recommendation": "Implement winning variant across all templates"
        }
        
        return {
            "message": f"A/B test {test_id} completed successfully",
            "result": mock_result
        }

    # Intelligent Matching endpoints
    @app.get("/api/v1/matching/startup/{startup_id}/funds")
    async def find_matching_funds(startup_id: int, limit: int = 10, exclude_recent: bool = True):
        """Поиск подходящих венчурных фондов для стартапа"""
        # Симуляция поиска подходящих фондов
        mock_results = [
            {
                "fund_id": 1,
                "fund_name": "Innovation Ventures",
                "match_score": {
                    "total_score": 0.92,
                    "industry_score": 1.0,
                    "stage_score": 0.85,
                    "geography_score": 1.0,
                    "ticket_size_score": 0.8,
                    "quality": "excellent",
                    "weighted_criteria": {
                        "industry": 0.4,
                        "stage": 0.255,
                        "geography": 0.2,
                        "ticket_size": 0.08
                    },
                    "bonus_points": 0.1,
                    "penalty_points": 0.0
                },
                "explanation": {
                    "startup_profile": {
                        "name": "TechStartup",
                        "industry": "Technology",
                        "stage": "Seed",
                        "geography": "North America",
                        "funding_needed": 2000000
                    },
                    "fund_profile": {
                        "name": "Innovation Ventures",
                        "focus_industries": ["Technology", "SaaS"],
                        "investment_stages": ["Seed", "Series A"],
                        "geography": "North America",
                        "ticket_size_range": "1,000,000 - 5,000,000"
                    },
                    "match_analysis": {
                        "industry_match": {
                            "startup_industry": "Technology",
                            "fund_industries": ["Technology", "SaaS"],
                            "match_type": "exact_match",
                            "confidence": 1.0
                        },
                        "stage_match": {
                            "startup_stage": "Seed",
                            "fund_stages": ["Seed", "Series A"],
                            "match_type": "exact_match",
                            "confidence": 1.0
                        },
                        "geography_match": {
                            "startup_geography": "North America",
                            "fund_geography": "North America",
                            "match_type": "exact_match",
                            "confidence": 1.0
                        },
                        "ticket_size_match": {
                            "startup_funding_needed": 2000000,
                            "fund_min_ticket": 1000000,
                            "fund_max_ticket": 5000000,
                            "match_type": "exact_match",
                            "confidence": 1.0
                        }
                    },
                    "recommendation": "Perfect industry alignment. Ideal investment stage match. Excellent geographic fit.",
                    "next_steps": [
                        "Highlight industry expertise and market knowledge",
                        "Prepare personalized pitch deck",
                        "Research fund's portfolio companies",
                        "Identify mutual connections",
                        "Schedule initial meeting"
                    ]
                },
                "exclusion_reasons": [],
                "is_eligible": True,
                "last_pitch_date": None
            },
            {
                "fund_id": 2,
                "fund_name": "Growth Capital Partners",
                "match_score": {
                    "total_score": 0.78,
                    "industry_score": 0.8,
                    "stage_score": 0.6,
                    "geography_score": 1.0,
                    "ticket_size_score": 0.8,
                    "quality": "good",
                    "weighted_criteria": {
                        "industry": 0.32,
                        "stage": 0.18,
                        "geography": 0.2,
                        "ticket_size": 0.08
                    },
                    "bonus_points": 0.05,
                    "penalty_points": 0.0
                },
                "explanation": {
                    "startup_profile": {
                        "name": "TechStartup",
                        "industry": "Technology",
                        "stage": "Seed",
                        "geography": "North America",
                        "funding_needed": 2000000
                    },
                    "fund_profile": {
                        "name": "Growth Capital Partners",
                        "focus_industries": ["Technology", "Fintech"],
                        "investment_stages": ["Series A", "Series B"],
                        "geography": "North America",
                        "ticket_size_range": "2,000,000 - 10,000,000"
                    },
                    "match_analysis": {
                        "industry_match": {
                            "startup_industry": "Technology",
                            "fund_industries": ["Technology", "Fintech"],
                            "match_type": "exact_match",
                            "confidence": 1.0
                        },
                        "stage_match": {
                            "startup_stage": "Seed",
                            "fund_stages": ["Series A", "Series B"],
                            "match_type": "adjacent_match",
                            "confidence": 0.8
                        },
                        "geography_match": {
                            "startup_geography": "North America",
                            "fund_geography": "North America",
                            "match_type": "exact_match",
                            "confidence": 1.0
                        },
                        "ticket_size_match": {
                            "startup_funding_needed": 2000000,
                            "fund_min_ticket": 2000000,
                            "fund_max_ticket": 10000000,
                            "match_type": "exact_match",
                            "confidence": 1.0
                        }
                    },
                    "recommendation": "Perfect industry alignment. Good stage compatibility. Excellent geographic fit.",
                    "next_steps": [
                        "Prepare personalized pitch deck",
                        "Research fund's portfolio companies",
                        "Identify mutual connections",
                        "Schedule initial meeting"
                    ]
                },
                "exclusion_reasons": [],
                "is_eligible": True,
                "last_pitch_date": None
            }
        ]
        
        return {
            "message": f"Found {len(mock_results)} matching funds for startup {startup_id}",
            "startup_id": startup_id,
            "results": mock_results[:limit],
            "total_matches": len(mock_results),
            "criteria_weights": {
                "industry": 0.40,
                "stage": 0.30,
                "geography": 0.20,
                "ticket_size": 0.10
            },
            "exclusion_settings": {
                "exclude_recent": exclude_recent,
                "exclusion_window_days": 90
            }
        }
    
    @app.post("/api/v1/matching/calculate-score")
    async def calculate_match_score(request_data: Dict[str, Any]):
        """Вычисление оценки сопоставления между стартапом и фондом"""
        startup_data = request_data.get("startup_data", {})
        fund_data = request_data.get("fund_data", {})
        
        if not startup_data or not fund_data:
            raise HTTPException(status_code=400, detail="startup_data and fund_data are required")
        
        # Симуляция вычисления оценки
        industry_score = 0.9 if startup_data.get("industry") in fund_data.get("focus_industries", []) else 0.3
        stage_score = 0.8 if startup_data.get("stage") in fund_data.get("investment_stages", []) else 0.4
        geography_score = 1.0 if startup_data.get("geography") == fund_data.get("geography") else 0.5
        ticket_size_score = 0.9 if (fund_data.get("ticket_size_min", 0) <= startup_data.get("funding_needed", 0) <= fund_data.get("ticket_size_max", float('inf'))) else 0.6
        
        total_score = (
            industry_score * 0.40 +
            stage_score * 0.30 +
            geography_score * 0.20 +
            ticket_size_score * 0.10
        )
        
        # Определяем качество
        quality = "excellent" if total_score >= 0.9 else "very_good" if total_score >= 0.8 else "good" if total_score >= 0.7 else "fair" if total_score >= 0.6 else "poor"
        
        mock_result = {
            "total_score": round(total_score, 3),
            "industry_score": round(industry_score, 3),
            "stage_score": round(stage_score, 3),
            "geography_score": round(geography_score, 3),
            "ticket_size_score": round(ticket_size_score, 3),
            "quality": quality,
            "weighted_criteria": {
                "industry": round(industry_score * 0.40, 3),
                "stage": round(stage_score * 0.30, 3),
                "geography": round(geography_score * 0.20, 3),
                "ticket_size": round(ticket_size_score * 0.10, 3)
            },
            "bonus_points": 0.05,
            "penalty_points": 0.0,
            "explanation": {
                "industry_match": f"{startup_data.get('industry', 'Unknown')} vs {fund_data.get('focus_industries', [])}",
                "stage_match": f"{startup_data.get('stage', 'Unknown')} vs {fund_data.get('investment_stages', [])}",
                "geography_match": f"{startup_data.get('geography', 'Unknown')} vs {fund_data.get('geography', 'Unknown')}",
                "ticket_size_match": f"${startup_data.get('funding_needed', 0):,} vs ${fund_data.get('ticket_size_min', 0):,} - ${fund_data.get('ticket_size_max', 0):,}"
            }
        }
        
        return {
            "message": "Match score calculated successfully",
            "result": mock_result
        }
    
    @app.post("/api/v1/matching/batch-process")
    async def batch_process_startups(request_data: Dict[str, Any]):
        """Пакетная обработка нескольких стартапов"""
        startup_ids = request_data.get("startup_ids", [])
        limit_per_startup = request_data.get("limit_per_startup", 10)
        
        if not startup_ids:
            raise HTTPException(status_code=400, detail="startup_ids is required")
        
        # Симуляция пакетной обработки
        mock_results = {}
        for startup_id in startup_ids:
            mock_results[startup_id] = [
                {
                    "fund_id": i + 1,
                    "fund_name": f"Fund {i + 1}",
                    "match_score": {
                        "total_score": round(0.9 - i * 0.1, 2),
                        "quality": "excellent" if i == 0 else "very_good" if i == 1 else "good"
                    },
                    "is_eligible": True
                }
                for i in range(min(limit_per_startup, 5))
            ]
        
        return {
            "message": f"Batch processed {len(startup_ids)} startups",
            "results": mock_results,
            "processing_summary": {
                "total_startups": len(startup_ids),
                "total_matches": sum(len(matches) for matches in mock_results.values()),
                "average_matches_per_startup": sum(len(matches) for matches in mock_results.values()) / len(startup_ids),
                "processing_time": "2.3 seconds"
            }
        }
    
    @app.get("/api/v1/matching/startup/{startup_id}/fund/{fund_id}/explanation")
    async def get_matching_explanation(startup_id: int, fund_id: int):
        """Получение детального объяснения сопоставления"""
        # Симуляция детального объяснения
        mock_explanation = {
            "startup_profile": {
                "name": f"Startup {startup_id}",
                "industry": "Technology",
                "stage": "Seed",
                "geography": "North America",
                "funding_needed": 2000000,
                "description": "AI-powered customer service platform"
            },
            "fund_profile": {
                "name": f"Fund {fund_id}",
                "focus_industries": ["Technology", "SaaS", "AI"],
                "investment_stages": ["Seed", "Series A"],
                "geography": "North America",
                "ticket_size_range": "1,000,000 - 5,000,000",
                "portfolio_size": 25,
                "avg_investment": 3000000
            },
            "match_analysis": {
                "industry_match": {
                    "startup_industry": "Technology",
                    "fund_industries": ["Technology", "SaaS", "AI"],
                    "match_type": "exact_match",
                    "confidence": 1.0,
                    "reasoning": "Perfect alignment - startup is in Technology, which is a core focus area for the fund"
                },
                "stage_match": {
                    "startup_stage": "Seed",
                    "fund_stages": ["Seed", "Series A"],
                    "match_type": "exact_match",
                    "confidence": 1.0,
                    "reasoning": "Ideal stage match - fund actively invests in Seed stage companies"
                },
                "geography_match": {
                    "startup_geography": "North America",
                    "fund_geography": "North America",
                    "match_type": "exact_match",
                    "confidence": 1.0,
                    "reasoning": "Geographic alignment - both operate in North American market"
                },
                "ticket_size_match": {
                    "startup_funding_needed": 2000000,
                    "fund_min_ticket": 1000000,
                    "fund_max_ticket": 5000000,
                    "match_type": "exact_match",
                    "confidence": 1.0,
                    "reasoning": "Perfect fit - funding need falls within fund's investment range"
                }
            },
            "synergy_analysis": {
                "portfolio_companies": [
                    {
                        "name": "TechCorp",
                        "industry": "Technology",
                        "stage": "Series A",
                        "synergy_potential": "High - similar market focus"
                    },
                    {
                        "name": "AI Solutions",
                        "industry": "AI",
                        "stage": "Seed",
                        "synergy_potential": "Medium - complementary technology"
                    }
                ],
                "potential_collaborations": [
                    "Joint go-to-market strategies",
                    "Technology partnerships",
                    "Customer referrals",
                    "Market intelligence sharing"
                ]
            },
            "recommendation": "Excellent match - Strong recommendation to proceed with outreach. All key criteria align perfectly.",
            "next_steps": [
                "Prepare personalized pitch deck highlighting industry expertise",
                "Research fund's recent investments and portfolio companies",
                "Identify mutual connections through LinkedIn and industry networks",
                "Schedule initial meeting with fund partners",
                "Prepare detailed financial projections and market analysis"
            ],
            "risk_factors": [],
            "success_probability": 0.85
        }
        
        return {
            "message": f"Matching explanation for startup {startup_id} and fund {fund_id}",
            "explanation": mock_explanation
        }
    
    @app.get("/api/v1/matching/statistics")
    async def get_matching_statistics():
        """Получение статистики системы сопоставления"""
        stats = {
            "total_matches": 1247,
            "successful_matches": 1089,
            "excluded_funds": 158,
            "average_score": 0.78,
            "match_quality_distribution": {
                "excellent": 234,
                "very_good": 456,
                "good": 345,
                "fair": 123,
                "poor": 89
            },
            "criteria_performance": {
                "industry_match": {
                    "average_score": 0.82,
                    "success_rate": 0.85
                },
                "stage_match": {
                    "average_score": 0.76,
                    "success_rate": 0.78
                },
                "geography_match": {
                    "average_score": 0.89,
                    "success_rate": 0.92
                },
                "ticket_size_match": {
                    "average_score": 0.71,
                    "success_rate": 0.74
                }
            },
            "top_performing_funds": [
                {
                    "fund_id": 1,
                    "fund_name": "Innovation Ventures",
                    "total_matches": 89,
                    "success_rate": 0.94,
                    "average_score": 0.91
                },
                {
                    "fund_id": 2,
                    "fund_name": "Growth Capital Partners",
                    "total_matches": 76,
                    "success_rate": 0.89,
                    "average_score": 0.87
                },
                {
                    "fund_id": 3,
                    "fund_name": "Tech Ventures Fund",
                    "total_matches": 67,
                    "success_rate": 0.85,
                    "average_score": 0.83
                }
            ],
            "most_matched_industries": [
                {"industry": "Technology", "match_count": 456, "success_rate": 0.87},
                {"industry": "Fintech", "match_count": 234, "success_rate": 0.82},
                {"industry": "Healthcare", "match_count": 189, "success_rate": 0.79},
                {"industry": "E-commerce", "match_count": 156, "success_rate": 0.85}
            ],
            "period": {
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return {
            "message": "Matching statistics retrieved successfully",
            "statistics": stats
        }
    
    @app.post("/api/v1/matching/custom-rules")
    async def add_custom_rule(request_data: Dict[str, Any]):
        """Добавление пользовательского правила сопоставления"""
        fund_id = request_data.get("fund_id")
        rule_type = request_data.get("rule_type")
        rule_data = request_data.get("rule_data", {})
        
        if not fund_id or not rule_type:
            raise HTTPException(status_code=400, detail="fund_id and rule_type are required")
        
        # Симуляция добавления правила
        mock_result = {
            "rule_id": f"rule-{uuid.uuid4()}",
            "fund_id": fund_id,
            "rule_type": rule_type,
            "rule_data": rule_data,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "applied_count": 0
        }
        
        return {
            "message": f"Custom rule added successfully for fund {fund_id}",
            "rule": mock_result
        }

    # Communication Orchestrator endpoints
    @app.post("/api/v1/orchestrator/initiate-communication")
    async def initiate_communication(request_data: Dict[str, Any]):
        """Инициация коммуникации между стартапом и фондами"""
        startup_id = request_data.get("startup_id")
        fund_ids = request_data.get("fund_ids", [])
        
        if not startup_id or not fund_ids:
            raise HTTPException(status_code=400, detail="startup_id and fund_ids are required")
        
        # Симуляция инициации коммуникации
        mock_communication_ids = []
        for i, fund_id in enumerate(fund_ids[:5]):  # Ограничиваем до 5 фондов
            mock_communication_ids.append(f"comm-{uuid.uuid4()}")
        
        mock_result = {
            "startup_id": startup_id,
            "fund_ids": fund_ids,
            "communication_ids": mock_communication_ids,
            "status": "initiated",
            "flows_created": len(mock_communication_ids),
            "initial_actions": [
                {
                    "action_type": "send_email",
                    "template_type": "initial_outreach",
                    "priority": 1,
                    "scheduled_at": datetime.now().isoformat()
                }
            ],
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Communication initiated for startup {startup_id} with {len(fund_ids)} funds",
            "result": mock_result
        }
    
    @app.post("/api/v1/orchestrator/process-response")
    async def process_fund_response(request_data: Dict[str, Any]):
        """Обработка ответа от венчурного фонда"""
        communication_id = request_data.get("communication_id")
        email_content = request_data.get("email_content", "")
        sender_email = request_data.get("sender_email", "")
        
        if not communication_id:
            raise HTTPException(status_code=400, detail="communication_id is required")
        
        # Симуляция обработки ответа
        mock_classification = {
            "classification": "interested",
            "confidence": 0.85,
            "extracted_info": {
                "keywords": ["interested", "meeting"],
                "urgency": "normal"
            },
            "suggested_action": "schedule_follow_up"
        }
        
        # Определяем следующее состояние
        next_state = "follow_up_sent"
        if "meeting" in email_content.lower():
            next_state = "meeting_requested"
        elif "not interested" in email_content.lower():
            next_state = "closed_rejected"
        
        mock_result = {
            "communication_id": communication_id,
            "sender_email": sender_email,
            "classification_result": mock_classification,
            "previous_state": "awaiting_response",
            "new_state": next_state,
            "actions_triggered": [
                {
                    "action_type": "send_email",
                    "template_type": "follow_up_interested" if next_state == "follow_up_sent" else "meeting_confirmation",
                    "priority": 2
                }
            ],
            "escalation_required": False,
            "processed_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Fund response processed for communication {communication_id}",
            "result": mock_result
        }
    
    @app.get("/api/v1/orchestrator/check-escalation/{communication_id}")
    async def check_escalation_triggers(communication_id: str):
        """Проверка триггеров эскалации для коммуникации"""
        # Симуляция проверки эскалации
        mock_escalation_result = {
            "communication_id": communication_id,
            "escalation_required": False,
            "triggers_checked": [
                {
                    "trigger": "timeout_no_response",
                    "condition": "7 days without response",
                    "status": "not_triggered",
                    "days_since_last_activity": 3
                },
                {
                    "trigger": "meeting_request",
                    "condition": "meeting request detected",
                    "status": "not_triggered",
                    "classification": "interested"
                },
                {
                    "trigger": "low_confidence_classification",
                    "condition": "confidence < 0.6",
                    "status": "not_triggered",
                    "confidence": 0.85
                }
            ],
            "next_check": (datetime.now() + timedelta(hours=24)).isoformat(),
            "checked_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Escalation check completed for communication {communication_id}",
            "result": mock_escalation_result
        }
    
    @app.post("/api/v1/orchestrator/schedule-follow-ups")
    async def schedule_follow_ups():
        """Планирование follow-up действий для всех активных коммуникаций"""
        # Симуляция планирования follow-ups
        mock_follow_ups = [
            {
                "communication_id": f"comm-{uuid.uuid4()}",
                "startup_id": 1,
                "fund_id": 2,
                "current_state": "awaiting_response",
                "timeout_days": 7,
                "days_since_last_activity": 8,
                "action": {
                    "type": "schedule_follow_up",
                    "template_type": "follow_up_interested",
                    "scheduled_at": datetime.now().isoformat(),
                    "priority": 2
                }
            },
            {
                "communication_id": f"comm-{uuid.uuid4()}",
                "startup_id": 3,
                "fund_id": 4,
                "current_state": "follow_up_sent",
                "timeout_days": 5,
                "days_since_last_activity": 6,
                "action": {
                    "type": "escalate_to_human",
                    "reason": "timeout_no_response",
                    "scheduled_at": datetime.now().isoformat(),
                    "priority": 1
                }
            }
        ]
        
        mock_result = {
            "total_communications_checked": 45,
            "follow_ups_scheduled": len(mock_follow_ups),
            "escalations_triggered": 1,
            "follow_ups": mock_follow_ups,
            "scheduled_at": datetime.now().isoformat(),
            "next_schedule_check": (datetime.now() + timedelta(hours=6)).isoformat()
        }
        
        return {
            "message": f"Scheduled {len(mock_follow_ups)} follow-up actions",
            "result": mock_result
        }
    
    @app.get("/api/v1/orchestrator/status-report/{startup_id}")
    async def generate_status_report(startup_id: int):
        """Генерация отчета о статусе коммуникаций стартапа"""
        # Симуляция отчета о статусе
        mock_report = {
            "startup_id": startup_id,
            "startup_name": "TechStartup",
            "total_communications": 8,
            "state_distribution": {
                "awaiting_response": 3,
                "follow_up_sent": 2,
                "meeting_requested": 1,
                "meeting_scheduled": 1,
                "escalated_to_human": 1
            },
            "escalation_count": 1,
            "escalation_rate": 0.125,
            "average_duration_days": 12.5,
            "most_active_funds": [
                {
                    "fund_id": 1,
                    "fund_name": "Innovation Ventures",
                    "action_count": 15,
                    "last_activity": (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    "fund_id": 2,
                    "fund_name": "Growth Capital Partners",
                    "action_count": 12,
                    "last_activity": (datetime.now() - timedelta(hours=5)).isoformat()
                }
            ],
            "recent_activities": [
                {
                    "communication_id": f"comm-{uuid.uuid4()}",
                    "state": "meeting_scheduled",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "fund_name": "Innovation Ventures"
                },
                {
                    "communication_id": f"comm-{uuid.uuid4()}",
                    "state": "follow_up_sent",
                    "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                    "fund_name": "Growth Capital Partners"
                }
            ],
            "next_actions": [
                {
                    "communication_id": f"comm-{uuid.uuid4()}",
                    "action_type": "send_email",
                    "priority": 1,
                    "scheduled_at": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "fund_name": "Tech Ventures Fund"
                },
                {
                    "communication_id": f"comm-{uuid.uuid4()}",
                    "action_type": "escalate_to_human",
                    "priority": 1,
                    "scheduled_at": (datetime.now() + timedelta(hours=6)).isoformat(),
                    "fund_name": "Capital Partners"
                }
            ],
            "performance_metrics": {
                "response_rate": 0.75,
                "meeting_conversion_rate": 0.25,
                "escalation_rate": 0.125,
                "average_response_time_hours": 48
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Status report generated for startup {startup_id}",
            "report": mock_report
        }
    
    @app.get("/api/v1/orchestrator/active-flows")
    async def get_active_flows():
        """Получение активных потоков коммуникации"""
        # Симуляция активных потоков
        mock_flows = [
            {
                "communication_id": f"comm-{uuid.uuid4()}",
                "startup_id": 1,
                "vc_fund_id": 2,
                "current_state": "awaiting_response",
                "state_count": 3,
                "pending_actions": 1,
                "escalation_rules_applied": 0,
                "startup_name": "TechStartup",
                "fund_name": "Innovation Ventures",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "updated_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "last_activity": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "communication_id": f"comm-{uuid.uuid4()}",
                "startup_id": 3,
                "vc_fund_id": 4,
                "current_state": "meeting_requested",
                "state_count": 4,
                "pending_actions": 2,
                "escalation_rules_applied": 0,
                "startup_name": "AI Solutions",
                "fund_name": "Growth Capital Partners",
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "updated_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
        ]
        
        return {
            "message": f"Retrieved {len(mock_flows)} active communication flows",
            "flows": mock_flows,
            "total_active_flows": len(mock_flows),
            "retrieved_at": datetime.now().isoformat()
        }
    
    @app.get("/api/v1/orchestrator/statistics")
    async def get_orchestrator_statistics():
        """Получение статистики оркестратора"""
        stats = {
            "total_communications": 156,
            "successful_communications": 89,
            "escalated_communications": 12,
            "rejected_communications": 23,
            "average_flow_duration": 18.5,
            "actions_processed": 1247,
            "state_distribution": {
                "initialized": 5,
                "sent_initial_email": 8,
                "awaiting_response": 23,
                "follow_up_sent": 15,
                "meeting_requested": 12,
                "meeting_scheduled": 8,
                "escalated_to_human": 12,
                "closed_rejected": 23,
                "closed_successful": 89
            },
            "escalation_triggers": {
                "timeout_no_response": 45,
                "meeting_request": 23,
                "document_request": 18,
                "rejection_detected": 15,
                "urgent_keywords": 8,
                "low_confidence_classification": 12
            },
            "performance_metrics": {
                "average_response_time_hours": 36,
                "escalation_rate": 0.08,
                "success_rate": 0.57,
                "meeting_conversion_rate": 0.23,
                "follow_up_effectiveness": 0.45
            },
            "recent_activity": {
                "communications_initiated_today": 12,
                "responses_processed_today": 8,
                "follow_ups_scheduled_today": 15,
                "escalations_triggered_today": 2
            },
            "period": {
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return {
            "message": "Orchestrator statistics retrieved successfully",
            "statistics": stats
        }
    
    @app.post("/api/v1/orchestrator/escalation-rules")
    async def add_escalation_rule(request_data: Dict[str, Any]):
        """Добавление пользовательского правила эскалации"""
        trigger = request_data.get("trigger")
        conditions = request_data.get("conditions", {})
        action = request_data.get("action")
        parameters = request_data.get("parameters", {})
        
        if not trigger or not action:
            raise HTTPException(status_code=400, detail="trigger and action are required")
        
        # Симуляция добавления правила
        mock_rule = {
            "rule_id": f"rule-{uuid.uuid4()}",
            "trigger": trigger,
            "conditions": conditions,
            "action": action,
            "parameters": parameters,
            "priority": 2,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "applied_count": 0
        }
        
        return {
            "message": f"Escalation rule added successfully: {trigger}",
            "rule": mock_rule
        }

    # Notification System endpoints
    @app.post("/api/v1/notifications/send")
    async def send_notification(request_data: Dict[str, Any]):
        """Отправка уведомления пользователю"""
        user_id = request_data.get("user_id")
        notification_type = request_data.get("notification_type")
        data = request_data.get("data", {})
        channels = request_data.get("channels", ["email"])
        
        if not user_id or not notification_type:
            raise HTTPException(status_code=400, detail="user_id and notification_type are required")
        
        # Симуляция отправки уведомления
        mock_result = {
            "user_id": user_id,
            "notification_type": notification_type,
            "channels": channels,
            "data": data,
            "notification_id": f"notif-{uuid.uuid4()}",
            "status": "sent",
            "delivery_status": {
                "email": "delivered" if "email" in channels else "not_attempted",
                "telegram": "delivered" if "telegram" in channels else "not_attempted",
                "webhook": "delivered" if "webhook" in channels else "not_attempted"
            },
            "sent_at": datetime.now().isoformat(),
            "delivered_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Notification sent to user {user_id}",
            "result": mock_result
        }
    
    @app.post("/api/v1/notifications/schedule-reports")
    async def schedule_periodic_reports():
        """Планирование периодических отчетов"""
        # Симуляция планирования отчетов
        mock_scheduled = [
            {
                "user_id": 1,
                "report_type": "weekly_progress_report",
                "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
                "frequency": "weekly",
                "template": "weekly_progress_email"
            },
            {
                "user_id": 2,
                "report_type": "weekly_progress_report", 
                "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat(),
                "frequency": "weekly",
                "template": "weekly_progress_email"
            }
        ]
        
        mock_result = {
            "total_scheduled": len(mock_scheduled),
            "reports": mock_scheduled,
            "scheduled_at": datetime.now().isoformat(),
            "next_batch": (datetime.now() + timedelta(hours=6)).isoformat()
        }
        
        return {
            "message": f"Scheduled {len(mock_scheduled)} periodic reports",
            "result": mock_result
        }
    
    @app.put("/api/v1/notifications/preferences/{user_id}")
    async def update_notification_preferences(user_id: int, request_data: Dict[str, Any]):
        """Обновление пользовательских настроек уведомлений"""
        # Симуляция обновления настроек
        mock_preferences = {
            "user_id": user_id,
            "channels": {
                "email": request_data.get("channels", {}).get("email", True),
                "telegram": request_data.get("channels", {}).get("telegram", True),
                "webhook": request_data.get("channels", {}).get("webhook", False)
            },
            "types": {
                "new_fund_response": request_data.get("types", {}).get("new_fund_response", True),
                "meeting_scheduled": request_data.get("types", {}).get("meeting_scheduled", True),
                "communication_escalated": request_data.get("types", {}).get("communication_escalated", True),
                "weekly_progress_report": request_data.get("types", {}).get("weekly_progress_report", True),
                "system_error": request_data.get("types", {}).get("system_error", True)
            },
            "frequency": {
                "new_fund_response": request_data.get("frequency", {}).get("new_fund_response", "immediate"),
                "meeting_scheduled": request_data.get("frequency", {}).get("meeting_scheduled", "immediate"),
                "communication_escalated": request_data.get("frequency", {}).get("communication_escalated", "immediate"),
                "weekly_progress_report": request_data.get("frequency", {}).get("weekly_progress_report", "weekly"),
                "system_error": request_data.get("frequency", {}).get("system_error", "immediate")
            },
            "quiet_hours": {
                "start_time": request_data.get("quiet_hours", {}).get("start_time", "22:00"),
                "end_time": request_data.get("quiet_hours", {}).get("end_time", "08:00")
            },
            "batch_enabled": request_data.get("batch_enabled", True),
            "max_notifications_per_hour": request_data.get("max_notifications_per_hour", 10),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Notification preferences updated for user {user_id}",
            "preferences": mock_preferences
        }
    
    @app.get("/api/v1/notifications/history/{user_id}")
    async def get_notification_history(user_id: int, limit: int = 50, notification_type: Optional[str] = None):
        """Получение истории уведомлений пользователя"""
        # Симуляция истории уведомлений
        mock_history = [
            {
                "notification_id": f"notif-{uuid.uuid4()}",
                "notification_type": "new_fund_response",
                "channel": "email",
                "subject": "Новый ответ от Innovation Ventures",
                "status": "delivered",
                "sent_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "delivered_at": (datetime.now() - timedelta(hours=1)).isoformat()
            },
            {
                "notification_id": f"notif-{uuid.uuid4()}",
                "notification_type": "meeting_scheduled",
                "channel": "telegram",
                "subject": "Встреча запланирована с Growth Capital Partners",
                "status": "delivered",
                "sent_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                "delivered_at": (datetime.now() - timedelta(hours=4)).isoformat()
            },
            {
                "notification_id": f"notif-{uuid.uuid4()}",
                "notification_type": "weekly_progress_report",
                "channel": "email",
                "subject": "Еженедельный отчет по коммуникациям",
                "status": "delivered",
                "sent_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "delivered_at": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]
        
        # Фильтруем по типу если указан
        if notification_type:
            mock_history = [n for n in mock_history if n['notification_type'] == notification_type]
        
        return {
            "message": f"Notification history for user {user_id}",
            "user_id": user_id,
            "total_count": len(mock_history),
            "notifications": mock_history[:limit],
            "retrieved_at": datetime.now().isoformat()
        }
    
    @app.get("/api/v1/notifications/statistics")
    async def get_notification_statistics():
        """Получение статистики системы уведомлений"""
        stats = {
            "delivery_stats": {
                "total_sent": 1247,
                "successful_deliveries": 1189,
                "failed_deliveries": 58,
                "retry_attempts": 89,
                "channel_stats": {
                    "email": 892,
                    "telegram": 245,
                    "webhook": 110
                },
                "type_stats": {
                    "new_fund_response": 456,
                    "meeting_scheduled": 234,
                    "communication_escalated": 89,
                    "weekly_progress_report": 345,
                    "system_error": 23
                }
            },
            "templates_count": 8,
            "cached_preferences": 45,
            "batch_queue_size": 12,
            "active_channels": ["email", "telegram", "webhook"],
            "active_notification_types": [
                "new_fund_response", "meeting_scheduled", "communication_escalated",
                "weekly_progress_report", "system_error"
            ],
            "performance_metrics": {
                "average_delivery_time_seconds": 2.3,
                "success_rate": 0.954,
                "retry_rate": 0.071,
                "batch_processing_efficiency": 0.89
            },
            "user_engagement": {
                "users_with_notifications_enabled": 45,
                "most_active_notification_type": "new_fund_response",
                "preferred_channel": "email",
                "average_notifications_per_user_per_week": 8.5
            },
            "period": {
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return {
            "message": "Notification statistics retrieved successfully",
            "statistics": stats
        }
    
    @app.post("/api/v1/notifications/test")
    async def test_notification_delivery(request_data: Dict[str, Any]):
        """Тестирование доставки уведомлений"""
        user_id = request_data.get("user_id")
        channel = request_data.get("channel", "email")
        notification_type = request_data.get("notification_type", "system_error")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Симуляция тестового уведомления
        mock_test_result = {
            "user_id": user_id,
            "channel": channel,
            "notification_type": notification_type,
            "test_notification_id": f"test-{uuid.uuid4()}",
            "status": "delivered",
            "delivery_time_seconds": 1.5,
            "test_data": {
                "subject": "🧪 Тестовое уведомление",
                "content": "Это тестовое уведомление для проверки доставки.",
                "timestamp": datetime.now().isoformat()
            },
            "sent_at": datetime.now().isoformat(),
            "delivered_at": datetime.now().isoformat()
        }
        
        return {
            "message": f"Test notification sent to user {user_id} via {channel}",
            "result": mock_test_result
        }

    # Response Classification endpoints
    @app.post("/api/v1/responses/classify")
    async def classify_vc_response(request_data: Dict[str, Any]):
    """Классификация ответа венчурного фонда"""
    email_text = request_data.get("email_text", "")
    startup_id = request_data.get("startup_id")
    vc_fund_id = request_data.get("vc_fund_id")
    
    if not email_text or len(email_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Email text is too short or empty")
    
    # Находим контекст если предоставлены ID
    context = {}
    if startup_id and vc_fund_id:
        startup = next((s for s in startups_data if s["id"] == startup_id), None)
        vc_fund = next((vc for vc in vc_funds_data if vc["id"] == vc_fund_id), None)
        
        if startup and vc_fund:
            context = {
                "startup_name": startup["name"],
                "vc_name": vc_fund["name"],
                "startup_industry": startup["industry"],
                "startup_stage": startup["stage"]
            }
    
    # Симуляция классификации ответа
    sample_responses = {
        "interested": {
            "classification": "interested",
            "confidence": 0.92,
            "reasoning": "Response shows clear interest with request for meeting and positive language",
            "key_indicators": ["sounds interesting", "would like to learn more", "schedule a call"],
            "extracted_info": {
                "meeting_details": {
                    "dates": ["next week", "tuesday"],
                    "times": ["2pm", "afternoon"],
                    "types": ["video call"]
                },
                "contact_info": {
                    "emails": ["partner@innovationvc.com"],
                    "phones": [],
                    "calendar_links": ["calendly.com/partner-innovation"]
                },
                "requirements": ["pitch deck", "financial projections"],
                "concerns": [],
                "sentiment": "positive",
                "urgency": "medium"
            },
            "suggested_action": "Send pitch deck and propose meeting times",
            "requires_human_review": False
        },
        "not_interested": {
            "classification": "not_interested",
            "confidence": 0.89,
            "reasoning": "Clear rejection with explanation of misalignment",
            "key_indicators": ["not a fit", "outside our focus", "pass on this opportunity"],
            "extracted_info": {
                "meeting_details": {"dates": [], "times": [], "types": []},
                "contact_info": {"emails": [], "phones": [], "calendar_links": []},
                "requirements": [],
                "concerns": ["stage too early", "market size"],
                "sentiment": "negative",
                "urgency": "low"
            },
            "suggested_action": "Update CRM status and focus on other prospects",
            "requires_human_review": False
        },
        "request_more_info": {
            "classification": "request_more_info",
            "confidence": 0.85,
            "reasoning": "Specific requests for additional materials and information",
            "key_indicators": ["send us your deck", "more information", "financial data"],
            "extracted_info": {
                "meeting_details": {"dates": [], "times": [], "types": []},
                "contact_info": {"emails": ["analysis@growthcapital.com"], "phones": [], "calendar_links": []},
                "requirements": ["pitch deck", "financial statements", "customer references", "unit economics"],
                "concerns": [],
                "sentiment": "neutral",
                "urgency": "medium"
            },
            "suggested_action": "Prepare and send requested materials",
            "requires_human_review": False
        },
        "meeting_request": {
            "classification": "meeting_request",
            "confidence": 0.94,
            "reasoning": "Explicit meeting request with specific scheduling details",
            "key_indicators": ["schedule a meeting", "available for a call", "coffee chat"],
            "extracted_info": {
                "meeting_details": {
                    "dates": ["this week", "friday"],
                    "times": ["10am", "morning"],
                    "types": ["in-person", "coffee meeting"]
                },
                "contact_info": {
                    "emails": ["meetings@techventures.com"],
                    "phones": ["+1-555-123-4567"],
                    "calendar_links": ["cal.com/techventures-partner"]
                },
                "requirements": ["bring demo"],
                "concerns": [],
                "sentiment": "positive",
                "urgency": "high"
            },
            "suggested_action": "Confirm meeting details and send calendar invite",
            "requires_human_review": False
        },
        "out_of_office": {
            "classification": "out_of_office",
            "confidence": 0.98,
            "reasoning": "Automatic out-of-office reply detected",
            "key_indicators": ["out of office", "automatic reply", "will respond when I return"],
            "extracted_info": {
                "meeting_details": {"dates": ["returning monday"], "times": [], "types": []},
                "contact_info": {"emails": [], "phones": [], "calendar_links": []},
                "requirements": [],
                "concerns": [],
                "sentiment": "neutral",
                "urgency": "low"
            },
            "suggested_action": "Schedule follow-up after return date",
            "requires_human_review": False
        },
        "unclear": {
            "classification": "unclear",
            "confidence": 0.45,
            "reasoning": "Response lacks clear intent or action items",
            "key_indicators": ["interesting", "will review", "noted"],
            "extracted_info": {
                "meeting_details": {"dates": [], "times": [], "types": []},
                "contact_info": {"emails": [], "phones": [], "calendar_links": []},
                "requirements": [],
                "concerns": [],
                "sentiment": "neutral", 
                "urgency": "low"
            },
            "suggested_action": "Send clarifying follow-up email",
            "requires_human_review": True
        }
    }
    
    # Определяем тип ответа на основе ключевых слов в тексте
    text_lower = email_text.lower()
    
    if any(word in text_lower for word in ["interested", "schedule", "call", "meeting", "discuss"]):
        if any(word in text_lower for word in ["schedule", "meeting", "call", "available"]):
            classification_result = sample_responses["meeting_request"]
        else:
            classification_result = sample_responses["interested"]
    elif any(word in text_lower for word in ["not a fit", "pass", "outside", "decline"]):
        classification_result = sample_responses["not_interested"]
    elif any(word in text_lower for word in ["send", "deck", "more info", "materials", "provide"]):
        classification_result = sample_responses["request_more_info"]
    elif any(word in text_lower for word in ["out of office", "away", "vacation", "automatic"]):
        classification_result = sample_responses["out_of_office"]
    else:
        classification_result = sample_responses["unclear"]
    
    # Добавляем метаданные
    result = {
        **classification_result,
        "analysis_method": "enhanced_demo_classifier",
        "analyzed_at": datetime.now().isoformat(),
        "original_text_length": len(email_text),
        "context": context if context else None
    }
    
    return {
        "message": "VC response classified successfully",
        "classification_result": result,
        "processing_time": "1.8s",
        "confidence_threshold_met": result["confidence"] > 0.7
    }

@app.post("/api/v1/responses/analyze-batch")
async def analyze_responses_batch(request_data: Dict[str, Any]):
    """Пакетный анализ нескольких ответов"""
    responses = request_data.get("responses", [])
    
    if not responses or len(responses) == 0:
        raise HTTPException(status_code=400, detail="No responses provided")
    
    if len(responses) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 responses per batch")
    
    results = []
    summary = {
        "total_responses": len(responses),
        "classifications": {},
        "high_confidence_count": 0,
        "requires_review_count": 0,
        "positive_responses": 0,
        "processing_time": f"{len(responses) * 1.5:.1f}s"
    }
    
    for i, response_item in enumerate(responses):
        email_text = response_item.get("email_text", "")
        
        if not email_text:
            continue
        
        # Симуляция классификации каждого ответа
        text_lower = email_text.lower()
        
        if "interested" in text_lower or "meeting" in text_lower:
            classification = "interested"
            confidence = 0.88
            sentiment = "positive"
            summary["positive_responses"] += 1
        elif "not" in text_lower and ("fit" in text_lower or "interested" in text_lower):
            classification = "not_interested"
            confidence = 0.91
            sentiment = "negative"
        elif "send" in text_lower or "more" in text_lower:
            classification = "request_more_info"
            confidence = 0.82
            sentiment = "neutral"
        elif "office" in text_lower:
            classification = "out_of_office"
            confidence = 0.96
            sentiment = "neutral"
        else:
            classification = "unclear"
            confidence = 0.42
            sentiment = "neutral"
        
        result = {
            "id": response_item.get("id", f"response_{i+1}"),
            "classification": classification,
            "confidence": confidence,
            "sentiment": sentiment,
            "requires_human_review": confidence < 0.7,
            "suggested_action": {
                "interested": "Send pitch deck and schedule meeting",
                "not_interested": "Update CRM and move to other prospects",
                "request_more_info": "Compile and send requested materials",
                "out_of_office": "Schedule follow-up after return",
                "unclear": "Send clarifying follow-up email"
            }.get(classification, "Manual review required")
        }
        
        results.append(result)
        
        # Обновляем сводку
        summary["classifications"][classification] = summary["classifications"].get(classification, 0) + 1
        if confidence > 0.7:
            summary["high_confidence_count"] += 1
        if result["requires_human_review"]:
            summary["requires_review_count"] += 1
    
    return {
        "message": f"Analyzed {len(results)} responses successfully",
        "results": results,
        "summary": summary,
        "recommendations": {
            "immediate_action_needed": summary["positive_responses"],
            "follow_up_required": summary["requires_review_count"],
            "automated_responses": summary["high_confidence_count"] - summary["requires_review_count"]
        }
    }

@app.get("/api/v1/responses/classification-types")
async def get_classification_types():
    """Получить доступные типы классификации и их описания"""
    return {
        "classification_types": [
            {
                "type": "interested",
                "name": "Interested",
                "description": "VC shows genuine interest in the opportunity",
                "indicators": ["sounds interesting", "would like to learn more", "fits our thesis"],
                "suggested_actions": ["Send pitch deck", "Propose meeting", "Share additional materials"],
                "typical_confidence": "0.8 - 0.95"
            },
            {
                "type": "not_interested", 
                "name": "Not Interested",
                "description": "VC clearly declines the opportunity",
                "indicators": ["not a fit", "outside our focus", "pass on this"],
                "suggested_actions": ["Update CRM status", "Focus on other prospects", "Ask for referrals"],
                "typical_confidence": "0.85 - 0.95"
            },
            {
                "type": "request_more_info",
                "name": "Request More Information",
                "description": "VC asks for additional materials or clarification",
                "indicators": ["send us your deck", "more information", "financial data"],
                "suggested_actions": ["Prepare requested materials", "Send comprehensive deck", "Schedule demo"],
                "typical_confidence": "0.75 - 0.90"
            },
            {
                "type": "meeting_request",
                "name": "Meeting Request",
                "description": "VC specifically requests or suggests a meeting",
                "indicators": ["schedule a meeting", "available for a call", "coffee chat"],
                "suggested_actions": ["Confirm meeting details", "Send calendar invite", "Prepare presentation"],
                "typical_confidence": "0.90 - 0.98"
            },
            {
                "type": "out_of_office",
                "name": "Out of Office",
                "description": "Automatic out-of-office reply",
                "indicators": ["out of office", "automatic reply", "will respond when I return"],
                "suggested_actions": ["Schedule follow-up", "Note return date", "Wait for response"],
                "typical_confidence": "0.95 - 0.99"
            },
            {
                "type": "unclear",
                "name": "Unclear",
                "description": "Response lacks clear intent or is ambiguous",
                "indicators": ["interesting", "will review", "noted", "thanks"],
                "suggested_actions": ["Send clarifying follow-up", "Human review required", "Ask specific questions"],
                "typical_confidence": "0.3 - 0.70"
            }
        ],
        "confidence_levels": {
            "high": {"range": "0.80 - 1.00", "description": "Very reliable classification"},
            "medium": {"range": "0.60 - 0.79", "description": "Generally reliable, minor review recommended"},
            "low": {"range": "0.00 - 0.59", "description": "Uncertain classification, human review required"}
        },
        "extraction_capabilities": {
            "meeting_details": "Dates, times, meeting types (video, in-person, etc.)",
            "contact_info": "Email addresses, phone numbers, calendar links",
            "requirements": "Specific requests for information or materials",
            "concerns": "Objections or hesitations mentioned",
            "sentiment": "Overall tone (positive, negative, neutral)",
            "urgency": "Response timeline expectations (high, medium, low)"
        },
        "api_usage": {
            "single_classification": "POST /api/v1/responses/classify",
            "batch_analysis": "POST /api/v1/responses/analyze-batch",
            "max_batch_size": 10,
            "typical_processing_time": "1-3 seconds per response"
        }
    }

@app.post("/api/v1/responses/suggest-next-action")
async def suggest_next_action(request_data: Dict[str, Any]):
    """Предложить следующие действия на основе классификации ответа"""
    classification = request_data.get("classification", "")
    confidence = request_data.get("confidence", 0.0)
    extracted_info = request_data.get("extracted_info", {})
    context = request_data.get("context", {})
    
    if not classification:
        raise HTTPException(status_code=400, detail="Classification is required")
    
    # Детальные рекомендации для каждого типа классификации
    action_plans = {
        "interested": {
            "immediate_actions": [
                "Send pitch deck within 24 hours",
                "Propose 2-3 meeting time options",
                "Prepare company one-pager"
            ],
            "follow_up_timeline": "2-3 days if no response to meeting request",
            "materials_to_prepare": [
                "Investor pitch deck (10-12 slides)",
                "Financial projections",
                "Product demo (if applicable)",
                "Team bios and backgrounds"
            ],
            "success_probability": "70-85%",
            "priority": "high"
        },
        "not_interested": {
            "immediate_actions": [
                "Update CRM with rejection reason",
                "Ask for referrals to other relevant VCs",
                "Thank for their time and transparency"
            ],
            "follow_up_timeline": "6-12 months for company updates",
            "materials_to_prepare": [],
            "success_probability": "5-10% (future reconsideration)",
            "priority": "low"
        },
        "request_more_info": {
            "immediate_actions": [
                "Compile all requested materials",
                "Send comprehensive information package",
                "Offer to schedule call for Q&A"
            ],
            "follow_up_timeline": "5-7 days after sending materials",
            "materials_to_prepare": [
                "Detailed financial statements",
                "Market research and analysis",
                "Customer testimonials",
                "Competitive landscape overview"
            ],
            "success_probability": "40-60%",
            "priority": "medium-high"
        },
        "meeting_request": {
            "immediate_actions": [
                "Respond within 4 hours with availability",
                "Send calendar invite immediately after confirmation",
                "Prepare customized presentation"
            ],
            "follow_up_timeline": "Same day response expected",
            "materials_to_prepare": [
                "Customized pitch presentation",
                "Live product demo",
                "Q&A preparation",
                "Term sheet framework (if Series A+)"
            ],
            "success_probability": "60-80%",
            "priority": "urgent"
        },
        "out_of_office": {
            "immediate_actions": [
                "Note return date in CRM",
                "Schedule automatic follow-up",
                "Continue outreach to other team members if urgent"
            ],
            "follow_up_timeline": "1-2 days after return date",
            "materials_to_prepare": [],
            "success_probability": "Unknown until return",
            "priority": "low"
        },
        "unclear": {
            "immediate_actions": [
                "Send clarifying follow-up email",
                "Ask specific yes/no questions",
                "Offer brief 15-minute call"
            ],
            "follow_up_timeline": "3-5 days for clarification",
            "materials_to_prepare": [
                "Concise company summary",
                "Specific questions to address ambiguity"
            ],
            "success_probability": "20-40%",
            "priority": "medium"
        }
    }
    
    base_plan = action_plans.get(classification, action_plans["unclear"])
    
    # Корректируем рекомендации на основе уверенности
    if confidence < 0.7:
        base_plan["immediate_actions"].insert(0, "Human review recommended due to low confidence")
        base_plan["priority"] = "review-required"
    
    # Добавляем специфичные рекомендации на основе извлеченной информации
    specific_recommendations = []
    
    meeting_details = extracted_info.get("meeting_details", {})
    if meeting_details.get("dates") or meeting_details.get("times"):
        specific_recommendations.append(f"Respond to specific meeting request: {', '.join(meeting_details.get('dates', []) + meeting_details.get('times', []))}")
    
    requirements = extracted_info.get("requirements", [])
    if requirements:
        specific_recommendations.append(f"Address specific requests: {', '.join(requirements[:3])}")
    
    concerns = extracted_info.get("concerns", [])
    if concerns:
        specific_recommendations.append(f"Address concerns: {', '.join(concerns[:2])}")
    
    urgency = extracted_info.get("urgency", "low")
    if urgency == "high":
        base_plan["follow_up_timeline"] = "Within 24 hours"
        base_plan["priority"] = "urgent"
    
    return {
        "classification": classification,
        "confidence": confidence,
        "action_plan": base_plan,
        "specific_recommendations": specific_recommendations,
        "estimated_effort": {
            "time_required": "30-60 minutes" if classification in ["interested", "meeting_request"] else "15-30 minutes",
            "complexity": "high" if classification == "meeting_request" else "medium",
            "resources_needed": base_plan["materials_to_prepare"]
        },
        "success_metrics": {
            "target_response_time": base_plan["follow_up_timeline"],
            "success_probability": base_plan["success_probability"],
            "priority_level": base_plan["priority"]
        },
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("Startup-VC Communication Platform starting...")
    print("API documentation: http://localhost:8000/docs")
    print("Alternative documentation: http://localhost:8000/redoc")
    print("Demo page: open demo.html in browser")
    
    uvicorn.run(
        "minimal_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
