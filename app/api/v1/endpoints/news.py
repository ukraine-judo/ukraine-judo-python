from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.models.schemas import NewsListItem, NewsDetail
from app.services.supabase import supabase

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_news_list(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and excerpt"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(8, ge=1, le=100, description="Items per page")
):
    """Get paginated list of news articles with optional filtering"""
    try:
        offset = (page - 1) * limit
        
        # Build query
        query = supabase.table("news").select(
            "id, title, excerpt, category, publishedAt, featured, image_url, author_name, tags, number",
            count="exact"
        )
        
        # Apply filters
        if category and category != "all":
            query = query.eq("category", category)
        
        if featured is not None:
            query = query.eq("featured", featured)
        
        if search:
            query = query.ilike("title", f"%{search}%")
        
        # Apply ordering and pagination
        query = query.order("publishedAt", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        # ✅ СПРОЩЕНО: Pydantic автоматично обробить категорії через computed_field
        news_items = [NewsListItem(**item) for item in response.data]
        
        # Calculate pagination metadata
        total = response.count if hasattr(response, 'count') and response.count is not None else len(response.data)
        total_pages = ((total - 1) // limit + 1) if total > 0 else 1
        
        return {
            "data": news_items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/latest", response_model=List[NewsListItem])
async def get_latest_news(limit: int = Query(6, ge=1, le=20)):
    """Get latest news articles"""
    try:
        response = (
            supabase.table("news")
            .select("id, title, excerpt, category, publishedAt, featured, image_url, author_name, tags, number")
            .order("publishedAt", desc=True)
            .limit(limit)
            .execute()
        )
        
        # ✅ СПРОЩЕНО: Pydantic автоматично обробить
        return [NewsListItem(**item) for item in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/featured", response_model=List[NewsListItem])
async def get_featured_news(limit: int = Query(3, ge=1, le=10)):
    """Get featured news articles only"""
    try:
        response = (
            supabase.table("news")
            .select("id, title, excerpt, category, publishedAt, featured, image_url, author_name, tags, number")
            .eq("featured", True)
            .order("publishedAt", desc=True)
            .limit(limit)
            .execute()
        )
        
        # ✅ СПРОЩЕНО
        return [NewsListItem(**item) for item in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{news_slug}", response_model=NewsDetail)
async def get_news_by_slug(news_slug: str):
    """Get single news article by slug/id"""
    try:
        response = (
            supabase.table("news")
            .select("*")
            .eq("id", news_slug)
            .execute()
        )
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="News article not found")
        
        # ✅ СПРОЩЕНО
        return NewsDetail(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
