from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

# Mock data for demonstration
mock_communications = [
    {
        "id": 1,
        "startup_id": 1,
        "vc_id": 1,
        "type": "initial_outreach",
        "status": "sent",
        "subject": "Partnership Opportunity",
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": 2,
        "startup_id": 2,
        "vc_id": 2,
        "type": "follow_up",
        "status": "draft",
        "subject": "Follow-up on Investment Discussion",
        "created_at": "2024-01-16T14:30:00Z"
    }
]

@router.get("/", response_model=List[Dict[str, Any]])
async def get_communications():
    """Get all communications"""
    return mock_communications

@router.get("/{communication_id}", response_model=Dict[str, Any])
async def get_communication(communication_id: int):
    """Get specific communication by ID"""
    comm = next((c for c in mock_communications if c["id"] == communication_id), None)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return comm

@router.post("/send", response_model=Dict[str, Any])
async def send_communication(communication_data: Dict[str, Any]):
    """Send a new communication"""
    new_communication = {
        "id": len(mock_communications) + 1,
        "status": "sent",
        **communication_data,
        "created_at": "2024-01-17T12:00:00Z"
    }
    mock_communications.append(new_communication)
    return {"message": "Communication sent successfully", "communication": new_communication}

@router.post("/generate", response_model=Dict[str, Any])
async def generate_communication(request_data: Dict[str, Any]):
    """Generate AI-powered communication content"""
    # Mock AI generation
    startup_id = request_data.get("startup_id")
    vc_id = request_data.get("vc_id")
    communication_type = request_data.get("type", "initial_outreach")
    
    generated_content = {
        "subject": f"Exciting Partnership Opportunity - {communication_type}",
        "content": f"Dear VC Team,\n\nI hope this message finds you well. I'm reaching out regarding an exciting partnership opportunity...\n\nBest regards,\nStartup Team",
        "type": communication_type,
        "startup_id": startup_id,
        "vc_id": vc_id
    }
    
    return {"message": "Communication content generated", "generated_content": generated_content}

@router.get("/startup/{startup_id}")
async def get_startup_communications(startup_id: int):
    """Get all communications for a specific startup"""
    startup_comms = [c for c in mock_communications if c.get("startup_id") == startup_id]
    return {"startup_id": startup_id, "communications": startup_comms}
