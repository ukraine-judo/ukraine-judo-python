from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.supabase import supabase
from app.models.schemas import DocumentListItem, ProtocolListItem, RegulationListItem

router = APIRouter(prefix="/documents")

@router.get("/documents", response_model=List[DocumentListItem])
async def get_documents(
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Отримати список документів"""
    try:
        query = supabase.table("documents").select("*").order("date", desc=True)
        
        if category:
            query = query.eq("category", category)
        
        if search:
            query = query.or_(f"title.ilike.%{search}%,tags.ilike.%{search}%")
        
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/protocols", response_model=List[ProtocolListItem])
async def get_protocols(
    year: Optional[int] = None,
    category: Optional[str] = None
):
    """Отримати список протоколів"""
    try:
        query = supabase.table("protocols").select("*").order("date", desc=True)
        
        if year:
            query = query.eq("year", year)
        
        if category:
            query = query.eq("category", category)
        
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error fetching protocols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulations", response_model=List[RegulationListItem])
async def get_regulations(
    year: Optional[int] = None,
    status: Optional[str] = None
):
    """Отримати список регламентів"""
    try:
        query = supabase.table("regulations").select("*").order("date_start", desc=True)
        
        if year:
            query = query.eq("year", year)
        
        if status:
            query = query.eq("status", status)
        
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error fetching regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
