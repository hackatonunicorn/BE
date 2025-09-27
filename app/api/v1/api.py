from fastapi import APIRouter
from app.api.v1.endpoints import startups, vcs, communications, analytics

api_router = APIRouter()

api_router.include_router(startups.router, prefix="/startups", tags=["startups"])
api_router.include_router(vcs.router, prefix="/vcs", tags=["venture-capital"])
api_router.include_router(communications.router, prefix="/communications", tags=["communications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
