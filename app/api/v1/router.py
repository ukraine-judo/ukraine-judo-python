from fastapi import APIRouter
from app.api.v1.endpoints import news, health, events, team, regions, documents

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(news.router, tags=["News"])
api_router.include_router(events.router, tags=["Events"])
api_router.include_router(team.router, tags=["Team"])
api_router.include_router(regions.router, tags=["Regions"])
api_router.include_router(documents.router, tags=["Documents"])  # ✅ Додали
