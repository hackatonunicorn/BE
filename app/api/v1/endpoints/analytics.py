from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_metrics():
    """Get dashboard analytics"""
    return {
        "total_startups": 45,
        "total_vcs": 23,
        "total_communications": 127,
        "success_rate": 32.5,
        "this_month": {
            "new_startups": 8,
            "new_communications": 34,
            "meetings_scheduled": 12
        },
        "top_performing_sectors": [
            {"sector": "FinTech", "success_rate": 45.2},
            {"sector": "HealthTech", "success_rate": 38.7},
            {"sector": "CleanTech", "success_rate": 35.1}
        ]
    }

@router.get("/communications/stats", response_model=Dict[str, Any])
async def get_communication_stats():
    """Get communication statistics"""
    return {
        "total_sent": 127,
        "response_rate": 28.3,
        "average_response_time": "2.4 days",
        "by_type": {
            "initial_outreach": 67,
            "follow_up": 35,
            "pitch_deck": 18,
            "meeting_request": 7
        },
        "by_status": {
            "sent": 89,
            "opened": 76,
            "replied": 36,
            "meeting_scheduled": 12
        }
    }

@router.get("/matching/recommendations")
async def get_matching_recommendations():
    """Get AI-powered startup-VC matching recommendations"""
    return {
        "recommendations": [
            {
                "startup_id": 1,
                "vc_id": 1,
                "match_score": 8.7,
                "reasons": ["Stage alignment", "Sector focus", "Geographic proximity"],
                "recommended_approach": "initial_outreach"
            },
            {
                "startup_id": 2,
                "vc_id": 2,
                "match_score": 7.9,
                "reasons": ["Investment size fit", "Portfolio synergy"],
                "recommended_approach": "warm_introduction"
            }
        ]
    }

@router.get("/performance/{startup_id}")
async def get_startup_performance(startup_id: int):
    """Get performance metrics for a specific startup"""
    return {
        "startup_id": startup_id,
        "total_outreach": 15,
        "response_rate": 33.3,
        "meetings_scheduled": 5,
        "funding_progress": {
            "target": "2M",
            "committed": "800K",
            "pipeline": "1.5M"
        },
        "timeline": [
            {"date": "2024-01-01", "event": "Campaign started", "type": "milestone"},
            {"date": "2024-01-15", "event": "First VC meeting", "type": "meeting"},
            {"date": "2024-01-20", "event": "Term sheet received", "type": "achievement"}
        ]
    }
