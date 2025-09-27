from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

# Mock data for demonstration
mock_startups = [
    {"id": 1, "name": "TechStartup", "industry": "Technology", "stage": "Seed", "description": "AI-powered solution"},
    {"id": 2, "name": "GreenTech", "industry": "CleanTech", "stage": "Series A", "description": "Sustainable energy platform"},
]

@router.get("/", response_model=List[Dict[str, Any]])
async def get_startups():
    """Get all startups in the platform"""
    return mock_startups

@router.get("/{startup_id}", response_model=Dict[str, Any])
async def get_startup(startup_id: int):
    """Get specific startup by ID"""
    startup = next((s for s in mock_startups if s["id"] == startup_id), None)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@router.post("/", response_model=Dict[str, Any])
async def create_startup(startup_data: Dict[str, Any]):
    """Create a new startup profile"""
    new_startup = {
        "id": len(mock_startups) + 1,
        **startup_data
    }
    mock_startups.append(new_startup)
    return new_startup

@router.put("/{startup_id}", response_model=Dict[str, Any])
async def update_startup(startup_id: int, startup_data: Dict[str, Any]):
    """Update startup information"""
    startup = next((s for s in mock_startups if s["id"] == startup_id), None)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    startup.update(startup_data)
    return startup
