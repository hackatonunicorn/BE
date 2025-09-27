from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

# Mock data for demonstration
mock_vcs = [
    {"id": 1, "name": "Innovation Ventures", "focus": "Early-stage tech", "aum": "100M", "location": "Silicon Valley"},
    {"id": 2, "name": "Green Capital", "focus": "CleanTech & Sustainability", "aum": "250M", "location": "New York"},
]

@router.get("/", response_model=List[Dict[str, Any]])
async def get_vcs():
    """Get all VCs in the platform"""
    return mock_vcs

@router.get("/{vc_id}", response_model=Dict[str, Any])
async def get_vc(vc_id: int):
    """Get specific VC by ID"""
    vc = next((v for v in mock_vcs if v["id"] == vc_id), None)
    if not vc:
        raise HTTPException(status_code=404, detail="VC not found")
    return vc

@router.post("/", response_model=Dict[str, Any])
async def create_vc(vc_data: Dict[str, Any]):
    """Create a new VC profile"""
    new_vc = {
        "id": len(mock_vcs) + 1,
        **vc_data
    }
    mock_vcs.append(new_vc)
    return new_vc

@router.get("/{vc_id}/portfolio")
async def get_vc_portfolio(vc_id: int):
    """Get VC's portfolio companies"""
    vc = next((v for v in mock_vcs if v["id"] == vc_id), None)
    if not vc:
        raise HTTPException(status_code=404, detail="VC not found")
    
    # Mock portfolio data
    return {
        "vc_id": vc_id,
        "portfolio": [
            {"company": "Portfolio Company 1", "investment_stage": "Series A", "investment_amount": "5M"},
            {"company": "Portfolio Company 2", "investment_stage": "Seed", "investment_amount": "2M"}
        ]
    }
