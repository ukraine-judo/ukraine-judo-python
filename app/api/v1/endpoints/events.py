# app/api/v1/endpoints/events.py
from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from app.models.schemas import EventListItem, EventDetail
from app.services.supabase import supabase
from datetime import date as date_type, datetime


router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventListItem])
async def get_events(
    event_type: Optional[str] = Query(None, description="Фільтр за типом (national/international)"),
    category: Optional[str] = Query(None, description="Фільтр за категорією"),
    status: Optional[str] = Query(None, description="Фільтр за статусом"),
    age_group: Optional[str] = Query(None, description="Фільтр за віковою групою"),
    featured: Optional[bool] = Query(None, description="Тільки виділені події"),
    from_date: Optional[str] = Query(None, description="Дата від (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Дата до (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="Кількість подій"),
    offset: int = Query(0, ge=0, description="Зміщення для пагінації")
):
    """Отримати список подій з фільтрами"""
    try:
        query = supabase.table("events").select("*")
        
        if event_type:
            query = query.eq("event_type", event_type)
        
        if category:
            query = query.eq("category", category)
        
        if status:
            query = query.eq("status", status)
        
        if age_group:
            query = query.eq("age_group", age_group)
        
        if featured is not None:
            query = query.eq("featured", featured)
        
        if from_date:
            query = query.gte("date_start", from_date)
        
        if to_date:
            query = query.lte("date_start", to_date)
        
        query = query.order("date_start", desc=False)
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        return [EventListItem(**item) for item in response.data]
    
    except Exception as e:
        print(f"Error in get_events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/search", response_model=List[EventListItem])
async def search_events(
    q: str = Query(..., min_length=2, description="Пошуковий запит"),
    year: Optional[int] = Query(None, description="Рік для пошуку"),
    event_type: Optional[str] = Query(None, description="Тип події"),
    category: Optional[str] = Query(None, description="Категорія"),
    status: Optional[str] = Query(None, description="Статус"),
    limit: int = Query(100, ge=1, le=200, description="Макс. результатів")
):
    """
    Пошук подій по року за назвою, містом, регіоном, організатором
    """
    try:
        from datetime import datetime as dt
        
        # Визначаємо рік
        search_year = year if year else dt.now().year
        
        # Діапазон дат для року
        start_date = f"{search_year}-01-01"
        end_date = f"{search_year}-12-31"
        
        # Базовий запит
        query = supabase.table("events").select("*")
        query = query.gte("date_start", start_date).lte("date_start", end_date)
        
        # Додаткові фільтри
        if event_type:
            query = query.eq("event_type", event_type)
        
        if category:
            query = query.eq("category", category)
        
        query = query.order("date_start", desc=False).limit(limit)
        
        response = query.execute()
        events = response.data if response.data else []
        
        # Client-side filtering для пошуку (Supabase не підтримує LIKE/ILIKE в деяких планах)
        search_lower = q.lower().strip()
        filtered_events = []
        
        for event in events:
            # Пошук в різних полях
            title_match = search_lower in (event.get('title') or '').lower()
            city_match = search_lower in (event.get('city') or '').lower()
            region_match = search_lower in (event.get('region') or '').lower()
            organizer_match = search_lower in (event.get('organizer') or '').lower()
            
            if title_match or city_match or region_match or organizer_match:
                # Автовизначення статусу
                today = date_type.today()
                event_start = datetime.fromisoformat(event['date_start'].replace('Z', '+00:00')).date()
                event_end = event_start
                
                if event.get('date_end'):
                    event_end = datetime.fromisoformat(event['date_end'].replace('Z', '+00:00')).date()
                
                if event.get('status') != 'cancelled':
                    if event_start <= today <= event_end:
                        event['status'] = 'ongoing'
                    elif today > event_end:
                        event['status'] = 'completed'
                    else:
                        event['status'] = 'planned'
                
                # Статус фільтр після автовизначення
                if status:
                    if event.get('status') == status:
                        filtered_events.append(event)
                else:
                    filtered_events.append(event)
        
        return [EventListItem(**item) for item in filtered_events]
    
    except Exception as e:
        print(f"Error in search_events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/upcoming", response_model=List[EventListItem])
async def get_upcoming_events(
    limit: int = Query(10, ge=1, le=50, description="Кількість подій")
):
    """Отримати найближчі майбутні події"""
    try:
        today = date_type.today().isoformat()
        
        response = supabase.table("events") \
            .select("*") \
            .gte("date_start", today) \
            .eq("status", "planned") \
            .order("date_start", desc=False) \
            .limit(limit) \
            .execute()
        
        return [EventListItem(**item) for item in response.data]
    
    except Exception as e:
        print(f"Error in get_upcoming_events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/by-month/{year}/{month}", response_model=List[EventListItem])
async def get_events_by_month(year: int, month: int):
    """Отримати події за місяць"""
    try:
        # Формуємо діапазон дат
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        response = supabase.table("events") \
            .select("*") \
            .gte("date_start", start_date) \
            .lt("date_start", end_date) \
            .order("date_start") \
            .execute()
        
        events = response.data if response.data else []
        
        # Автоматично визначаємо статус
        today = date_type.today()
        for event in events:
            event_start = datetime.fromisoformat(event['date_start'].replace('Z', '+00:00')).date()
            event_end = event_start
            
            if event.get('date_end'):
                event_end = datetime.fromisoformat(event['date_end'].replace('Z', '+00:00')).date()
            
            if event.get('status') == 'cancelled':
                continue
            elif event_start <= today <= event_end:
                event['status'] = 'ongoing'
            elif today > event_end:
                event['status'] = 'completed'
            else:
                event['status'] = 'planned'
        
        return [EventListItem(**item) for item in events]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_slug}", response_model=EventDetail)
async def get_event_by_slug(
    event_slug: str = Path(..., description="Slug події")
):
    """Отримати повну детальну інформацію про подію за slug"""
    try:
        response = supabase.table("events") \
            .select("*") \
            .eq("slug", event_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return EventDetail(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_event_by_slug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/featured/list", response_model=List[EventListItem])
async def get_featured_events(
    limit: int = Query(5, ge=1, le=20, description="Кількість подій")
):
    """Отримати виділені події"""
    try:
        response = supabase.table("events") \
            .select("*") \
            .eq("featured", True) \
            .order("date_start", desc=False) \
            .limit(limit) \
            .execute()
        
        return [EventListItem(**item) for item in response.data]
    
    except Exception as e:
        print(f"Error in get_featured_events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
