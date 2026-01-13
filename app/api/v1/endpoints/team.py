# app/api/v1/endpoints/team.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.schemas import AthleteListItem, AthleteDetail, CoachListItem, CoachDetail
from app.services.supabase import supabase

router = APIRouter(prefix="/team", tags=["Team"])

# ============ ATHLETES ENDPOINTS ============

@router.get("/athletes", response_model=List[AthleteListItem])
async def get_athletes(
    sex: Optional[str] = Query(None, description="Фільтр за статтю (men/women)"),
    status: Optional[str] = Query(None, description="Фільтр за статусом (main/candidate/reserve)"),
    weight: Optional[str] = Query(None, description="Фільтр за вагою"),
    limit: int = Query(100, ge=1, le=200, description="Кількість спортсменів")
):
    """
    Отримати список спортсменів з фільтрами
    Сортування: main -> candidate -> reserve, потім за рейтингом (вищий краще)
    """
    try:
        query = supabase.table("athletes").select("*")
        
        if sex:
            query = query.eq("sex", sex)
        
        if status:
            query = query.eq("status", status)
        
        if weight:
            query = query.eq("weight", weight)
        
        response = query.limit(limit).execute()
        
        # Конвертуємо rating в int перед сортуванням
        for item in response.data:
            try:
                item['rating'] = int(item.get('rating', 0)) if item.get('rating') else 0
            except (ValueError, TypeError):
                item['rating'] = 0
        
        # СОРТУВАННЯ
        status_priority = {"main": 1, "candidate": 2, "reserve": 3}
        
        sorted_athletes = sorted(
            response.data,
            key=lambda x: (
                status_priority.get(x.get('status', 'reserve'), 99),
                -x.get('rating', 0)
            )
        )
        
        return [AthleteListItem(**item) for item in sorted_athletes]
    
    except Exception as e:
        print(f"Error in get_athletes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/athletes/{athlete_slug}", response_model=AthleteDetail)
async def get_athlete_by_slug(athlete_slug: str):
    """
    Отримати повну інформацію про спортсмена за slug
    """
    try:
        response = supabase.table("athletes") \
            .select("*") \
            .eq("slug", athlete_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Athlete not found")
        
        return AthleteDetail(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_athlete_by_slug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/athletes/weight-categories/{sex}")
async def get_weight_categories(sex: str):
    """
    Отримати всі вагові категорії для статі
    """
    try:
        response = supabase.table("athletes") \
            .select("weight") \
            .eq("sex", sex) \
            .execute()
        
        # Збираємо унікальні ваги
        weights = list(set([item['weight'] for item in response.data if item.get('weight')]))
        weights.sort()
        
        return {"sex": sex, "weights": weights}
    
    except Exception as e:
        print(f"Error in get_weight_categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============ COACHES ENDPOINTS ============

@router.get("/coaches", response_model=List[CoachListItem])
async def get_coaches(
    team_category: Optional[str] = Query(None, description="Фільтр за категорією (men/women/youth/etc)"),
    is_national_team: Optional[bool] = Query(None, description="Тільки тренери національної команди"),
    limit: int = Query(50, ge=1, le=100, description="Кількість тренерів")
):
    """
    Отримати список тренерів з фільтрами
    """
    try:
        query = supabase.table("coach").select("*")
        
        if team_category:
            query = query.eq("team_category", team_category)
        
        if is_national_team is not None:
            query = query.eq("is_national_team", is_national_team)
        
        query = query.order("id", desc=False).limit(limit)
        
        response = query.execute()
        
        return [CoachListItem(**item) for item in response.data]
    
    except Exception as e:
        print(f"Error in get_coaches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/coaches/{coach_slug}", response_model=CoachDetail)
async def get_coach_by_slug(coach_slug: str):
    """
    Отримати тренера за slug
    """
    try:
        response = supabase.table("coach") \
            .select("*") \
            .eq("slug", coach_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Coach not found")
        
        return CoachDetail(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_coach_by_slug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stats")
async def get_team_stats():
    """
    Статистика по команді
    """
    try:
        # Кількість спортсменів
        athletes_response = supabase.table("athletes").select("id", count="exact").execute()
        
        # По статі
        men_response = supabase.table("athletes").select("id", count="exact").eq("sex", "men").execute()
        women_response = supabase.table("athletes").select("id", count="exact").eq("sex", "women").execute()
        
        # По статусу
        main_response = supabase.table("athletes").select("id", count="exact").eq("status", "main").execute()
        candidate_response = supabase.table("athletes").select("id", count="exact").eq("status", "candidate").execute()
        reserve_response = supabase.table("athletes").select("id", count="exact").eq("status", "reserve").execute()
        
        # Кількість тренерів
        coaches_response = supabase.table("coach").select("id", count="exact").execute()
        national_coaches = supabase.table("coach").select("id", count="exact").eq("is_national_team", True).execute()
        
        return {
            "athletes": {
                "total": athletes_response.count if hasattr(athletes_response, 'count') else 0,
                "men": men_response.count if hasattr(men_response, 'count') else 0,
                "women": women_response.count if hasattr(women_response, 'count') else 0,
                "main": main_response.count if hasattr(main_response, 'count') else 0,
                "candidate": candidate_response.count if hasattr(candidate_response, 'count') else 0,
                "reserve": reserve_response.count if hasattr(reserve_response, 'count') else 0
            },
            "coaches": {
                "total": coaches_response.count if hasattr(coaches_response, 'count') else 0,
                "national_team": national_coaches.count if hasattr(national_coaches, 'count') else 0
            }
        }
    
    except Exception as e:
        print(f"Error in get_team_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ✅ ЗМІНЕНО: Отримати тренерів спортсмена за SLUG
@router.get("/athletes/{athlete_slug}/coaches", response_model=List[CoachListItem])
async def get_athlete_coaches(athlete_slug: str):
    """
    Отримати тренерів конкретного спортсмена
    """
    try:
        # Спочатку отримуємо спортсмена
        athlete_response = supabase.table("athletes") \
            .select("trainer_slug") \
            .eq("slug", athlete_slug) \
            .execute()
        
        if not athlete_response.data or len(athlete_response.data) == 0:
            raise HTTPException(status_code=404, detail="Athlete not found")
        
        trainer_slugs = athlete_response.data[0].get('trainer_slug')
        
        if not trainer_slugs:
            return []
        
        # ✅ Отримуємо тренерів за slug
        coaches_response = supabase.table("coach") \
            .select("*") \
            .in_("slug", trainer_slugs) \
            .execute()
        
        return [CoachListItem(**item) for item in coaches_response.data]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_athlete_coaches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ✅ ЗАЛИШАЄМО: Отримати спортсменів тренера (використовує athlete_ids)
@router.get("/coaches/{coach_slug}/athletes", response_model=List[AthleteListItem])
async def get_coach_athletes(coach_slug: str):
    """
    Отримати спортсменів конкретного тренера
    """
    try:
        # Спочатку отримуємо тренера
        coach_response = supabase.table("coach") \
            .select("athlete_ids") \
            .eq("slug", coach_slug) \
            .execute()
        
        if not coach_response.data or len(coach_response.data) == 0:
            raise HTTPException(status_code=404, detail="Coach not found")
        
        athlete_ids = coach_response.data[0].get('athlete_ids')
        
        if not athlete_ids:
            return []
        
        # Отримуємо спортсменів
        athletes_response = supabase.table("athletes") \
            .select("*") \
            .in_("id", athlete_ids) \
            .execute()
        
        # Сортуємо
        status_priority = {"main": 1, "candidate": 2, "reserve": 3}
        sorted_athletes = sorted(
            athletes_response.data,
            key=lambda x: (
                status_priority.get(x.get('status', 'reserve'), 99),
                -x.get('rating', 0)
            )
        )
        
        return [AthleteListItem(**item) for item in sorted_athletes]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_coach_athletes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
