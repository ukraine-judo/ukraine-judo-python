from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.supabase import supabase
from app.models.schemas import RegionListItem, RegionDetail

router = APIRouter(prefix="/regions")

@router.get("", response_model=List[RegionListItem])
async def get_regions(search: Optional[str] = None):
    """Отримати список усіх регіонів"""
    try:
        query = supabase.table("regions").select("*").order("id", desc=False)
        
        if search:
            query = query.or_(f"info->>name-region.ilike.%{search}%")
        
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error fetching regions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{region_slug}", response_model=RegionDetail)
async def get_region_detail(region_slug: str):
    """Отримати детальну інформацію про регіон"""
    try:
        response = supabase.table("regions") \
            .select("*") \
            .eq("slug", region_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Region not found")
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching region: {e}")
        raise HTTPException(status_code=500, detail=str(e))
