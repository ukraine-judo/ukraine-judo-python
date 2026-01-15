# app/api/v1/endpoints/protocols_regulations.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.supabase import supabase
from datetime import datetime
import json

router = APIRouter(prefix="/documents/events", tags=["Protocols & Regulations"])


@router.get("")
async def get_protocols_and_regulations(
    year: Optional[int] = Query(None, description="Фільтр за роком"),
    event_type: Optional[str] = Query(None, description="Тип події (national/international)"),
    category: Optional[str] = Query(None, description="Категорія події"),
    search: Optional[str] = Query(None, description="Пошук за назвою"),
    limit: int = Query(20, ge=1, le=100, description="Кількість результатів"),
    offset: int = Query(0, ge=0, description="Зміщення для пагінації")
):
    """
    Отримати список подій з протоколами та регламентами
    """
    try:
        # Базовий запит
        query = supabase.table("events").select(
            "id, slug, title, event_type, category, age_group, "
            "date_start, date_end, city, region, organizer, protocols, regulation_path"
        )
        
        # Фільтри
        if year:
            query = query.gte("date_start", f"{year}-01-01")
            query = query.lte("date_start", f"{year}-12-31")
        
        if event_type and event_type != 'all':
            query = query.eq("event_type", event_type)
        
        if category and category != 'all':
            query = query.eq("category", category)
        
        if search:
            query = query.ilike("title", f"%{search}%")
        
        # Сортування
        query = query.order("date_start", desc=True)
        
        # Виконуємо запит
        response = query.execute()
        all_events = response.data if response.data else []
        
        # Фільтруємо: тільки з протоколами або регламентами
        filtered_events = []
        for event in all_events:
            has_protocols = event.get('protocols') and event.get('protocols') not in [None, '', '[]', 'null']
            has_regulation = event.get('regulation_path') and event.get('regulation_path') not in [None, '', 'null']
            
            if has_protocols or has_regulation:
                # Парсимо protocols якщо це JSON string
                if isinstance(event.get('protocols'), str):
                    try:
                        event['protocols'] = json.loads(event['protocols'])
                    except:
                        event['protocols'] = []
                
                filtered_events.append(event)
        
        # Пагінація
        total = len(filtered_events)
        paginated_events = filtered_events[offset:offset + limit]
        
        return {
            "data": paginated_events,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        print(f"Error in get_protocols_and_regulations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats")
async def get_protocols_regulations_stats():
    """
    Отримати статистику по протоколам та регламентам
    """
    try:
        # Отримуємо всі події
        response = supabase.table("events").select(
            "protocols, regulation_path, date_start"
        ).execute()
        
        all_events = response.data if response.data else []
        
        # Рахуємо статистику
        total_with_protocols = 0
        total_with_regulations = 0
        total_with_both = 0
        years = set()
        
        for event in all_events:
            has_protocols = event.get('protocols') and event.get('protocols') not in [None, '', '[]', 'null']
            has_regulation = event.get('regulation_path') and event.get('regulation_path') not in [None, '', 'null']
            
            if has_protocols or has_regulation:
                if has_protocols:
                    total_with_protocols += 1
                if has_regulation:
                    total_with_regulations += 1
                if has_protocols and has_regulation:
                    total_with_both += 1
                
                # Збираємо роки
                if event.get('date_start'):
                    try:
                        year = datetime.fromisoformat(event['date_start'].replace('Z', '+00:00')).year
                        years.add(year)
                    except:
                        pass
        
        return {
            "total_events": total_with_protocols + total_with_regulations - total_with_both,
            "total_with_protocols": total_with_protocols,
            "total_with_regulations": total_with_regulations,
            "total_with_both": total_with_both,
            "available_years": sorted(list(years), reverse=True)
        }
        
    except Exception as e:
        print(f"Error in get_protocols_regulations_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
