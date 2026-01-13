# app/api/v1/endpoints/health.py
from fastapi import APIRouter
from app.services.supabase import supabase


router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}


@router.get("/test-db")
async def test_database():
    """Тестовий ендпоінт для перевірки з'єднання з Supabase"""
    try:
        response = supabase.table("news").select("*").limit(1).execute()
        return {
            "status": "ok",
            "message": "Database connection successful",
            "sample_data": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
