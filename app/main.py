from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from app.config import get_settings
from app.api.v1.router import api_router
from app.services.supabase import supabase
from app.utils.categories import normalize_category, get_old_categories_for_filter, CATEGORY_LABELS, get_category_label
from app.utils.coach_categories import COACH_CATEGORY_LABELS, get_coach_category_label
from datetime import datetime, date
from typing import Optional, List, Dict, Any  # ✅ ДОДАЙ ЦЕЙ РЯДОК
import json
import os


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# API роутер
app.include_router(api_router, prefix="/api/v1")

# Статика
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", html=True), name="static")
    print("✓ Static files mounted from /static")

# Шаблони
templates = Jinja2Templates(directory="templates") if os.path.exists("templates") else None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Головна сторінка з SSR новинами"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        # Завантажуємо останні новини
        response = supabase.table("news") \
            .select("number, id, title, excerpt, category, publishedAt, featured, image_url, author_name, tags") \
            .order("publishedAt", desc=True) \
            .limit(6) \
            .execute()
        
        news_items = []
        for item in response.data:
            if item.get('image_url'):
                item['image_full_url'] = f"/static/{item['image_url']}"
            # ✅ ВИПРАВЛЕННЯ: зберігаємо англійську для логіки, додаємо українську для UI
            normalized = normalize_category(item.get('category', ''))
            item['category_key'] = normalized  # англійська для фільтрів
            item['display_category'] = get_category_label(normalized)  # українська для відображення
            news_items.append(item)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "news": news_items,
            "settings": settings
        })
    except Exception as e:
        print(f"Error loading news: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "news": [],
            "settings": settings
        })


@app.get("/news", response_class=HTMLResponse)
async def news_page(
    request: Request,
    category: str = None,
    search: str = None,
    page: int = 1
):
    """Сторінка новин з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        limit = 8
        offset = (page - 1) * limit
        
        query = supabase.table("news").select(
            "number, id, title, excerpt, category, publishedAt, featured, image_url, author_name, tags",
            count="exact"
        )
        
        # ✅ Фільтрація з маппінгом категорій
        if category and category != 'all':
            old_categories = get_old_categories_for_filter(category)
            query = query.in_("category", old_categories)
        
        if search:
            query = query.ilike("title", f"%{search}%")
        
        query = query.order("publishedAt", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        news_items = []
        for item in response.data:
            if item.get('image_url'):
                item['image_full_url'] = f"/static/{item['image_url']}"
            # ✅ ВИПРАВЛЕННЯ: зберігаємо англійську для логіки, додаємо українську для UI
            normalized = normalize_category(item.get('category', ''))
            item['category_key'] = normalized  # англійська для фільтрів
            item['display_category'] = get_category_label(normalized)  # українська для відображення
            news_items.append(item)
        
        total = response.count if hasattr(response, 'count') else len(response.data)
        total_pages = (total + limit - 1) // limit
        has_prev = page > 1
        has_next = page < total_pages
        
        return templates.TemplateResponse("news.html", {
            "request": request,
            "news": news_items,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "current_category": category or 'all',
            "search_query": search or '',
            "settings": settings,
            "category_labels": CATEGORY_LABELS  # ✅ Передаємо лейбли
        })
    except Exception as e:
        print(f"Error loading news: {e}")
        return templates.TemplateResponse("news.html", {
            "request": request,
            "news": [],
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "current_category": 'all',
            "search_query": '',
            "settings": settings,
            "category_labels": CATEGORY_LABELS
        })


@app.get("/news/{news_slug}", response_class=HTMLResponse)
async def news_detail(request: Request, news_slug: str):
    """Детальна сторінка новини з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        # Завантажуємо основну новину
        response = supabase.table("news") \
            .select("*") \
            .eq("id", news_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "settings": settings
            }, status_code=404)
        
        news_item = response.data[0]
        
        if news_item.get('image_url'):
            news_item['image_full_url'] = f"/static/{news_item['image_url']}"
        
        # Конвертуємо категорію
        news_item['display_category'] = get_category_label(normalize_category(news_item.get('category', '')))
        
        # ✅ Обробка тегів (розділених крапкою з комою)
        tags = news_item.get('tags', '')
        if tags:
            if isinstance(tags, str):
                # Розділяємо по крапці з комою (;)
                news_item['tags_list'] = [tag.strip() for tag in tags.split(';') if tag.strip()]
            elif isinstance(tags, list):
                # Якщо теги - це вже список
                news_item['tags_list'] = [tag.strip() for tag in tags if tag and tag.strip()]
            else:
                news_item['tags_list'] = []
        else:
            news_item['tags_list'] = []
        
        # Завантажуємо останні новини
        latest_news = []
        try:
            latest_response = supabase.table("news") \
                .select("id, title, publishedAt, image_url, category") \
                .neq("id", news_slug) \
                .order("publishedAt", desc=True) \
                .limit(5) \
                .execute()
            
            for item in latest_response.data:
                if item.get('image_url'):
                    item['image_full_url'] = f"/static/{item['image_url']}"
                item['display_category'] = get_category_label(normalize_category(item.get('category', '')))
                latest_news.append(item)
        except Exception as e:
            print(f"Error loading latest news: {e}")
        
        # Завантажуємо схожі новини
        related_news = []
        try:
            old_categories = get_old_categories_for_filter(normalize_category(news_item.get('category', '')))
            
            related_response = supabase.table("news") \
                .select("id, title, publishedAt, image_url, category") \
                .in_("category", old_categories) \
                .neq("id", news_slug) \
                .order("publishedAt", desc=True) \
                .limit(3) \
                .execute()
            
            for item in related_response.data:
                if item.get('image_url'):
                    item['image_full_url'] = f"/static/{item['image_url']}"
                item['display_category'] = get_category_label(normalize_category(item.get('category', '')))
                related_news.append(item)
        except Exception as e:
            print(f"Error loading related news: {e}")
        
        # Якщо схожих новин мало, додаємо останні новини
        if len(related_news) < 3:
            try:
                additional_response = supabase.table("news") \
                    .select("id, title, publishedAt, image_url, category") \
                    .neq("id", news_slug) \
                    .order("publishedAt", desc=True) \
                    .limit(3 - len(related_news)) \
                    .execute()
                
                for item in additional_response.data:
                    if not any(n['id'] == item['id'] for n in related_news):
                        if item.get('image_url'):
                            item['image_full_url'] = f"/static/{item['image_url']}"
                        item['display_category'] = get_category_label(normalize_category(item.get('category', '')))
                        related_news.append(item)
            except Exception as e:
                print(f"Error loading additional news: {e}")
        
        return templates.TemplateResponse("news_detail.html", {
            "request": request,
            "news": news_item,
            "related_news": related_news,
            "latest_news": latest_news,
            "settings": settings
        })
    except Exception as e:
        print(f"Error loading news detail: {e}")
        return templates.TemplateResponse("404.html", {
            "request": request,
            "settings": settings
        }, status_code=404)


def format_date(date_str):
    if not date_str:
        return "Дата невідома"
    try:
        from datetime import datetime
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        months_genitive = {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
            5: "травня", 6: "червня", 7: "липня", 8: "серпня",
            9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        }
        return f"{date.day} {months_genitive[date.month]} {date.year}"
    except:
        return date_str

def format_date_range(event):
    try:
        from datetime import datetime
        
        if not event.get('date'):
            return "Дата невідома"
            
        start = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
        
        if not event.get('endDate'):
            return format_date(event['date'])
            
        end = datetime.fromisoformat(event['endDate'].replace('Z', '+00:00'))
        
        if start.date() == end.date():
            return format_date(event['date'])
        
        if start.month == end.month and start.year == end.year:
            months_genitive = {
                1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
                5: "травня", 6: "червня", 7: "липня", 8: "серпня",
                9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
            }
            return f"{start.day}-{end.day} {months_genitive[start.month]} {start.year}"
        
        return f"{format_date(event['date'])} - {format_date(event['endDate'])}"
    except Exception as e:
        print(f"Error formatting date range: {e}")
        return "Дата невідома"

def get_event_status(event):
    try:
        from datetime import datetime, date
        
        today = date.today()
        
        event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).date()
        
        end_date = event_date
        if event.get('endDate'):
            end_date = datetime.fromisoformat(event['endDate'].replace('Z', '+00:00')).date()
        
        if event.get('status') in ['canceled', 'cancelled']:
            return 'canceled'
        
        if event_date <= today <= end_date:
            return 'ongoing'
        elif today > end_date:
            return 'finished'
        else:
            return 'planned'
    except:
        return event.get('status', 'planned')

@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(
    request: Request,
    # Pagination
    month: Optional[int] = None,
    year: Optional[int] = None,
    # Filters
    search: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    age_group: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort: Optional[str] = "date_asc",
):
    """Сторінка календаря подій з розширеною фільтрацією"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        from datetime import datetime
            
        # Поточний місяць якщо не вказано
        now = datetime.now()
        current_year = year or now.year
        current_month = month or now.month
        
        # Назви місяців українською (повні назви)
        months_uk = {
            1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
            5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
            9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
        }
        
        # Словники перекладів
        age_groups_dict = {
            'U13': 'До 13 років',
            'U15': 'До 15 років',
            'U16': 'До 16 років',
            'U17': 'До 17 років',
            'U18': 'До 18 років',
            'U21': 'До 21 року',
            'U23': 'До 23 років',
            'adults': 'Дорослі',
            'officials': 'Офіційні особи',
            'veterans': 'Ветерани',
            'senior': 'Дорослі',
            'junior': 'Юніори',
            'cadet': 'Кадети',
            'youth': 'Юнаки'
        }
        
        categories_dict = {
            'cup': 'Кубок',
            'tournament': 'Турнір',
            'championship': 'Чемпіонат',
            'seminar': 'Семінар',
            'training_camp': 'Тренувальні збори',
            'training': 'Тренувальні збори',
            'university': 'Універсиада',
            'selection': 'Відбір'
        }
        
        months_genitive = {
            1: 'Січня', 2: 'Лютого', 3: 'Березня', 4: 'Квітня',
            5: 'Травня', 6: 'Червня', 7: 'Липня', 8: 'Серпня',
            9: 'Вересня', 10: 'Жовтня', 11: 'Листопада', 12: 'Грудня'
        }
        
        # 🔍 BUILD QUERY WITH FILTERS
        query = supabase.table("events").select("*")
        
        # Якщо є фільтри дат - використовуємо їх, інакше місяць
        if date_from or date_to:
            if date_from:
                query = query.gte("date_start", date_from)
            if date_to:
                query = query.lte("date_start", date_to)
        else:
            # Формуємо діапазон дат для поточного місяця
            start_date = f"{current_year}-{current_month:02d}-01"
            if current_month == 12:
                end_date = f"{current_year + 1}-01-01"
            else:
                end_date = f"{current_year}-{current_month + 1:02d}-01"
            
            query = query.gte("date_start", start_date).lt("date_start", end_date)
        
        # 🌍 Event Type Filter
        if type and type in ['international', 'national']:
            query = query.eq("event_type", type)
        
        # 👥 Age Group Filter
        if age_group:
            query = query.eq("age_group", age_group)
        
        # 🏆 Category Filter
        if category:
            query = query.eq("category", category)
        
        # Execute query
        response = query.order("date_start").execute()
        
        events = []
        today = datetime.now().date()
        
        for item in response.data:
            # ✅ КОНВЕРТАЦІЯ ДАТ З РЯДКІВ В DATE ОБ'ЄКТИ
            if isinstance(item.get('date_start'), str):
                item['date_start'] = datetime.fromisoformat(item['date_start'].replace('Z', '+00:00')).date()
            
            if item.get('date_end') and isinstance(item['date_end'], str):
                item['date_end'] = datetime.fromisoformat(item['date_end'].replace('Z', '+00:00')).date()
            
            if item.get('arrival_date') and isinstance(item['arrival_date'], str):
                item['arrival_date'] = datetime.fromisoformat(item['arrival_date'].replace('Z', '+00:00')).date()
            
            # Обробка JSON полів
            import json
            
            for json_field in ['program', 'weight_classes', 'contacts', 'live_streams', 'protocols', 'info_blocks']:
                if item.get(json_field):
                    if isinstance(item[json_field], str):
                        try:
                            item[f'{json_field}_parsed'] = json.loads(item[json_field])
                        except:
                            item[f'{json_field}_parsed'] = []
                    elif isinstance(item[json_field], list):
                        item[f'{json_field}_parsed'] = item[json_field]
                    else:
                        item[f'{json_field}_parsed'] = []
                else:
                    item[f'{json_field}_parsed'] = []
            
            # Повні URL
            if item.get('image_path'):
                item['image_url'] = f"/static/{item['image_path']}"
            else:
                item['image_url'] = None
                
            if item.get('regulation_path'):
                item['regulation_url'] = f"/static/{item['regulation_path']}"
            else:
                item['regulation_url'] = None
            
            # Автовизначення статусу
            event_start = item['date_start']
            event_end = item.get('date_end') or event_start
            
            if item.get('status') != 'cancelled':
                if event_start <= today <= event_end:
                    item['status'] = 'ongoing'
                elif today > event_end:
                    item['status'] = 'completed'
                else:
                    item['status'] = 'planned'
            
            # Додаємо переклади безпосередньо в об'єкт
            item['age_group_label'] = age_groups_dict.get(item.get('age_group'), item.get('age_group'))
            item['category_label'] = categories_dict.get(item.get('category'), item.get('category'))
            
            # Додаємо назву місяця в родовому відмінку для дати
            if item['date_start']:
                item['month_genitive'] = months_genitive.get(item['date_start'].month, '')
            
            # ✅ ПРІОРИТЕТНЕ СОРТУВАННЯ: Featured і Ongoing завжди вгорі!
            is_featured = item.get('featured', False)
            is_ongoing = item['status'] == 'ongoing'
            
            if is_featured and is_ongoing:
                item['sort_weight'] = 0
            elif is_ongoing:
                item['sort_weight'] = 1
            elif is_featured:
                item['sort_weight'] = 2
            elif item['status'] == 'planned':
                item['sort_weight'] = 10
            elif item['status'] == 'completed':
                item['sort_weight'] = 999
            elif item['status'] == 'cancelled':
                item['sort_weight'] = 998
            else:
                item['sort_weight'] = 500
            
            events.append(item)
        
        # 🔍 CLIENT-SIDE FILTERS (що не можна зробити в Supabase)
        
        # Search Filter
        if search:
            search_lower = search.lower()
            events = [e for e in events if 
                search_lower in (e.get('title') or '').lower() or
                search_lower in (e.get('city') or '').lower() or
                search_lower in (e.get('region') or '').lower()
            ]
        
        # Status Filter (після автовизначення)
        if status:
            events = [e for e in events if e.get('status') == status]
        
        # ✅ СОРТУВАННЯ
        if sort == "date_asc":
            events.sort(key=lambda x: (x['sort_weight'], x['date_start']))
        elif sort == "date_desc":
            events.sort(key=lambda x: (x['sort_weight'], x['date_start']), reverse=True)
        elif sort == "title_asc":
            events.sort(key=lambda x: (x.get('title') or '').lower())
        elif sort == "title_desc":
            events.sort(key=lambda x: (x.get('title') or '').lower(), reverse=True)
        else:
            # Default: priority + date
            events.sort(key=lambda x: (x['sort_weight'], x['date_start']))
        
        # 🏷️ BUILD ACTIVE FILTERS
        active_filters = []
        base_url = str(request.url).split('?')[0]
        
        def remove_param(param_name):
            params = dict(request.query_params)
            params.pop(param_name, None)
            return base_url + ('?' + '&'.join(f"{k}={v}" for k, v in params.items()) if params else '')
        
        if search:
            active_filters.append({
                'label': f'Пошук: "{search}"',
                'remove_url': remove_param('search')
            })
        
        if status:
            status_labels = {
                'ongoing': '🔴 Live',
                'planned': '🔵 Заплановано',
                'completed': '⚫ Завершено'
            }
            active_filters.append({
                'label': status_labels.get(status, status),
                'remove_url': remove_param('status')
            })
        
        if type:
            type_labels = {
                'international': '🌍 Міжнародні',
                'national': '🇺🇦 Національні'
            }
            active_filters.append({
                'label': type_labels.get(type, type),
                'remove_url': remove_param('type')
            })
        
        if age_group:
            active_filters.append({
                'label': f'Вік: {age_groups_dict.get(age_group, age_group)}',
                'remove_url': remove_param('age_group')
            })
        
        if category:
            active_filters.append({
                'label': f'{categories_dict.get(category, category)}',
                'remove_url': remove_param('category')
            })
        
        if date_from:
            active_filters.append({
                'label': f'Від: {date_from}',
                'remove_url': remove_param('date_from')
            })
        
        if date_to:
            active_filters.append({
                'label': f'До: {date_to}',
                'remove_url': remove_param('date_to')
            })
        
        # Підрахунок статистики
        international_count = sum(1 for e in events if e.get('event_type') == 'international')
        national_count = sum(1 for e in events if e.get('event_type') == 'national')
        upcoming_count = sum(1 for e in events if e.get('status') == 'planned')
        
        # Перевірка на AJAX запит
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        context = {
            "request": request,
            "events": events,
            "current_year": current_year,
            "current_month": current_month,
            "month_name": months_uk[current_month],
            "current_filter": type or 'all',
            "active_filters": active_filters,
            "total_events": len(events),
            "international_count": international_count,
            "national_count": national_count,
            "upcoming_count": upcoming_count,
            "current_search": search or '',
            "current_status": status or 'all',
            "current_type": type or 'all',
            "current_age_group": age_group or 'all',
            "current_category": category or 'all',
            "age_groups_dict": age_groups_dict,
            "categories_dict": categories_dict,
            "settings": settings
        }
        
        # Якщо AJAX - повертаємо тільки частину з подіями
        if is_ajax:
            # Рендеримо тільки events-grid та stats
            return templates.TemplateResponse("calendar_events_partial.html", context)
        
        return templates.TemplateResponse("calendar.html", context)
    
    except Exception as e:
        print(f"Error loading calendar: {e}")
        import traceback
        traceback.print_exc()
        
        from datetime import datetime
        now = datetime.now()
        months_uk = {
            1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
            5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
            9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
        }
        
        return templates.TemplateResponse("calendar.html", {
            "request": request,
            "events": [],
            "current_year": now.year,
            "current_month": now.month,
            "month_name": months_uk[now.month],
            "current_filter": 'all',
            "active_filters": [],
            "total_events": 0,
            "international_count": 0,
            "national_count": 0,
            "upcoming_count": 0,
            "current_search": '',
            "current_status": 'all',
            "current_type": 'all',
            "current_age_group": 'all',
            "current_category": 'all',
            "age_groups_dict": {},
            "categories_dict": {},
            "settings": settings
        })

@app.get("/calendar/{event_slug}", response_class=HTMLResponse)
async def event_detail_page(request: Request, event_slug: str):
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        from datetime import datetime
        import json
        
        # Словники розшифровки (як у calendar_page)
        age_groups_dict = {
            'U13': 'До 13 років',
            'U15': 'До 15 років',
            'U16': 'До 16 років',
            'U17': 'До 17 років',
            'U18': 'До 18 років',
            'U21': 'До 21 року',
            'U23': 'До 23 років',
            'adults': 'Дорослі',
            'officials': 'Офіційні особи',
            'veterans': 'Ветерани',
        }
        
        event_types_dict = {
            'international': 'Міжнародний',
            'national': 'Національний',
        }
        
        categories_dict = {
            'cup': 'Кубок',
            'tournament': 'Турнір',
            'championship': 'Чемпіонат',
            'seminar': 'Семінар',
            'training_camp': 'Навчально-тренувальний збір',
            'training': 'Тренування',
            'university': 'Університетські змагання',
        }
        
        response = supabase.table("events") \
            .select("*") \
            .eq("slug", event_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = response.data[0]
        
        # Розшифровка як у calendar_page
        event['age_group_label'] = age_groups_dict.get(event.get('age_group'), event.get('age_group'))
        event['event_type_label'] = event_types_dict.get(event.get('event_type'), event.get('event_type'))
        event['category_label'] = categories_dict.get(event.get('category'), event.get('category'))
        
        # AJAX endpoint debug - якщо потрібно
        if event.get('program_parsed'):
            print(f"DEBUG program_parsed: {event['program_parsed']}")
        
        # Parsing JSON fields
        for json_field in ['program', 'weight_classes', 'contacts', 'live_streams', 'protocols', 'info_blocks']:
            field_value = event.get(json_field)
            if field_value:
                if isinstance(field_value, str):
                    try:
                        parsed_data = json.loads(field_value)
                        event[f"{json_field}_parsed"] = parsed_data
                    except Exception as parse_error:
                        print(f"Error parsing {json_field}: {parse_error}")
                        event[f"{json_field}_parsed"] = []
                elif isinstance(field_value, list):
                    event[f"{json_field}_parsed"] = field_value
                elif isinstance(field_value, dict):
                    event[f"{json_field}_parsed"] = field_value
                else:
                    event[f"{json_field}_parsed"] = []
            else:
                event[f"{json_field}_parsed"] = []
        
        # Date parsing
        if isinstance(event.get('date_start'), str):
            event['date_start'] = datetime.fromisoformat(event['date_start'].replace('Z', '+00:00')).date()
        if event.get('date_end') and isinstance(event['date_end'], str):
            event['date_end'] = datetime.fromisoformat(event['date_end'].replace('Z', '+00:00')).date()
        if event.get('arrival_date') and isinstance(event['arrival_date'], str):
            event['arrival_date'] = datetime.fromisoformat(event['arrival_date'].replace('Z', '+00:00')).date()
        
        # Image and regulation URLs
        if event.get('image_path'):
            event['image_url'] = f"/static/{event['image_path']}"
        else:
            event['image_url'] = None
        
        if event.get('regulation_path'):
            event['regulation_url'] = f"/static/{event['regulation_path']}"
        else:
            event['regulation_url'] = None
        
        # Calculate days until event
        days_until = None
        if event.get('date_start') and event.get('status') == 'planned':
            now = datetime.now().date()
            days_until = (event['date_start'] - now).days
        
        return templates.TemplateResponse("event_detail.html", {
            "request": request,
            "event": event,
            "settings": settings,
            "days_until": days_until
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading event detail: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Помилка - Федерація Дзюдо України</title>
    <!-- Your error page HTML -->
</head>
<body>
    <div class="error-container">
        <h1>404</h1>
        <h2>Подію не знайдено</h2>
        <p>Вибачте, але події з таким ідентифікатором не існує.</p>
        <div class="error-code">Slug: {event_slug}</div>
        <a href="/calendar">← Повернутися до календаря</a>
    </div>
</body>
</html>""",
            status_code=404
        )



def get_sex_label(sex):
    """Повертає текстову назву статі"""
    if sex in ['men', 'man']:
        return 'Чоловіки'
    elif sex in ['women', 'woman']:
        return 'Жінки'
    else:
        return 'Не вказано'

def get_age_category(age, sex):
    """
    Визначити вікову категорію спортсмена
    Підтримує різні формати статі: men/man/male та women/woman/female
    """
    if not age or age < 12:
        return "Не вказано"
    
    # Нормалізуємо стать - перевіряємо чи це чоловік
    is_male = str(sex).lower() in ['men', 'man', 'male', 'м', 'чоловік'] if sex else False
    
    if age <= 13:
        return "Діти"
    elif age <= 14:
        return "Молодші юнаки" if is_male else "Молодші дівчата"
    elif age <= 15:
        return "Юнаки" if is_male else "Дівчата"
    elif age <= 16:
        return "Молодші кадети" if is_male else "Молодші кадетки"
    elif age <= 17:
        return "Кадети" if is_male else "Кадетки"
    elif age <= 20:
        return "Юніори" if is_male else "Юніорки"
    elif age <= 22:
        return "Молодь"
    else:
        return "Чоловіки" if is_male else "Жінки"


@app.get("/team", response_class=HTMLResponse)
async def team_page(
    request: Request,
    sex: str = None,
    status: str = None,
    search: str = None,
    page: int = 1,
    coaches_page: int = 1,
    coaches_tab: str = 'all',
    coach_category: str = None,
    coaches_search: str = None
):
    """Сторінка команди з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    def safe_int(value, default=0):
        """Безпечна конвертація в int"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    try:
        # ================== СПОРТСМЕНИ ==================
        limit = 12
        offset = (page - 1) * limit
        
        query = supabase.table("athletes").select("*", count="exact")
        
        if sex and sex != "all":
            query = query.eq("sex", sex)
        
        if status and status != "all":
            query = query.eq("status", status)
        
        if search:
            query = query.ilike("name", f"%{search}%")
        
        athletes_response = query.execute()
        
        athletes = []
        status_priority = {"main": 1, "candidate": 2, "reserve": 3}
        
        for athlete in athletes_response.data:
            athlete['rating'] = safe_int(athlete.get('rating'), 0)
            
            athlete['photo_url'] = None
            if athlete.get('photos'):
                try:
                    if isinstance(athlete['photos'], str):
                        photos_data = json.loads(athlete['photos'])
                    else:
                        photos_data = athlete['photos']
                    
                    if photos_data and 'thumb' in photos_data:
                        athlete['photo_url'] = f"/static/{photos_data['thumb']}"
                except Exception as e:
                    athlete['photo_url'] = None
            
            if athlete.get('bdate'):
                try:
                    from datetime import datetime, date
                    if isinstance(athlete['bdate'], str):
                        birth_date = datetime.strptime(athlete['bdate'], '%Y-%m-%d').date()
                    else:
                        birth_date = athlete['bdate']
                    
                    today = date.today()
                    athlete['age'] = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    athlete['age_category'] = get_age_category(athlete['age'], athlete.get('sex'))
                except:
                    athlete['age'] = None
                    athlete['age_category'] = 'Не вказано'
            else:
                athlete['age'] = None
                athlete['age_category'] = 'Не вказано'
            
            athlete['status_priority'] = status_priority.get(athlete.get('status', 'reserve'), 99)
            athletes.append(athlete)
        
        athletes.sort(key=lambda x: (x['status_priority'], -x['rating']))
        
        total_athletes = len(athletes)
        athletes_paginated = athletes[offset:offset + limit]
        total_pages = (total_athletes + limit - 1) // limit if total_athletes > 0 else 1
        has_prev = page > 1
        has_next = page < total_pages
        
        # ================== ТРЕНЕРИ ==================
        coaches_limit = 8
        coaches_offset = (coaches_page - 1) * coaches_limit
        
        # Завжди отримуємо ПОВНИЙ список
        all_coaches_full_response = supabase.table("coach").select("*").order("id", desc=False).execute()
        all_coaches_full = all_coaches_full_response.data if all_coaches_full_response.data else []
        
        print(f"\n[TEAM] Total coaches in DB: {len(all_coaches_full)}")
        
        # ✅ ВИПРАВЛЕНО: Нормалізуємо is_national_team для ВСІХ тренерів ОДРАЗУ
        for coach in all_coaches_full:
            is_nat = coach.get('is_national_team')
            # Конвертуємо в boolean
            coach['is_national_team'] = is_nat is True or str(is_nat).lower() == 'true'
        
        # Підрахунок національних та регіональних (тепер з boolean значеннями)
        national_coaches_total = len([c for c in all_coaches_full if c['is_national_team']])
        regional_coaches_total = len([c for c in all_coaches_full if not c['is_national_team']])
        
        print(f"[TEAM] Total: National={national_coaches_total}, Regional={regional_coaches_total}")
        
        # Фільтруємо для відображення
        if coaches_tab == 'national':
            filtered_coaches = [c for c in all_coaches_full if c['is_national_team']]
        elif coaches_tab == 'regional':
            filtered_coaches = [c for c in all_coaches_full if not c['is_national_team']]
        else:
            filtered_coaches = list(all_coaches_full)
        
        print(f"[TEAM] After team type filter ({coaches_tab}): {len(filtered_coaches)} coaches")
        
        # Фільтр по категорії
        if coach_category and coach_category != 'all':
            filtered_coaches = [c for c in filtered_coaches if c.get('team_category') == coach_category]
            print(f"[TEAM] After category filter: {len(filtered_coaches)} coaches")
        
        # Фільтр по пошуку
        if coaches_search and coaches_search.strip():
            search_lower = coaches_search.lower().strip()
            filtered_coaches = [
                c for c in filtered_coaches 
                if (c.get('name') and search_lower in c.get('name', '').lower()) or 
                   (c.get('position') and search_lower in c.get('position', '').lower()) or
                   (c.get('city') and search_lower in c.get('city', '').lower())
            ]
            print(f"[TEAM] After search filter '{coaches_search}': {len(filtered_coaches)} coaches")
        
        # Обробка тренерів (image, category_label, awards)
        for coach in filtered_coaches:
            if coach.get('image'):
                coach['image_url'] = f"/static/{coach['image']}"
            else:
                coach['image_url'] = None
            
            coach['category_label'] = get_coach_category_label(coach.get('team_category', ''))
            
            if coach.get('awards'):
                try:
                    if isinstance(coach['awards'], str):
                        coach['awards'] = json.loads(coach['awards'])
                except:
                    coach['awards'] = []
        
        # ✅ DEBUG: Виводимо перших 3 тренерів
        if filtered_coaches:
            print(f"[TEAM DEBUG] Sample coaches:")
            for i, coach in enumerate(filtered_coaches[:3]):
                print(f"  {i+1}. {coach.get('name')} - is_national_team: {coach.get('is_national_team')} (type: {type(coach.get('is_national_team'))})")
        
        # Пагінація
        coaches_total = len(filtered_coaches)
        coaches_display = filtered_coaches[coaches_offset:coaches_offset + coaches_limit]
        coaches_total_pages = (coaches_total + coaches_limit - 1) // coaches_limit if coaches_total > 0 else 1
        
        print(f"[TEAM] Final: {len(coaches_display)} coaches displayed (page {coaches_page}/{coaches_total_pages})\n")
        
        return templates.TemplateResponse("team.html", {
            "request": request,
            # Спортсмені
            "athletes": athletes_paginated,
            "current_page": page,
            "total_pages": total_pages,
            "total_athletes": total_athletes,
            "has_prev": has_prev,
            "has_next": has_next,
            "current_sex": sex or 'all',
            "current_status": status or 'all',
            "search_query": search or '',
            # Тренери
            "coaches": coaches_display,
            "national_coaches_total": national_coaches_total,
            "regional_coaches_total": regional_coaches_total,
            "coaches_page": coaches_page,
            "coaches_total_pages": coaches_total_pages,
            "coaches_tab": coaches_tab,
            "current_coach_category": coach_category,
            "coaches_search_query": coaches_search or '',
            "coaches_has_prev": coaches_page > 1,
            "coaches_has_next": coaches_page < coaches_total_pages,
            # Інше
            "coach_category_labels": COACH_CATEGORY_LABELS,
            "settings": settings
        })
    
    except Exception as e:
        print(f"[TEAM ERROR] {e}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse("team.html", {
            "request": request,
            "athletes": [],
            "coaches": [],
            "current_page": 1,
            "total_pages": 1,
            "total_athletes": 0,
            "has_prev": False,
            "has_next": False,
            "current_sex": 'all',
            "current_status": 'all',
            "search_query": '',
            "national_coaches_total": 0,
            "regional_coaches_total": 0,
            "coaches_page": 1,
            "coaches_total_pages": 1,
            "coaches_tab": 'all',
            "current_coach_category": None,
            "coaches_search_query": '',
            "coaches_has_prev": False,
            "coaches_has_next": False,
            "coach_category_labels": COACH_CATEGORY_LABELS,
            "settings": settings
        })


@app.get("/team/athletes/{athlete_slug}", response_class=HTMLResponse)
async def athlete_detail(request: Request, athlete_slug: str):
    """Детальна сторінка спортсмена з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        from datetime import datetime, date
        import json
        
        # Завантажуємо спортсмена
        response = supabase.table("athletes") \
            .select("*") \
            .eq("slug", athlete_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": "Спортсмена не знайдено",
                "settings": settings
            }, status_code=404)
        
        athlete = response.data[0]
        
        # ✅ ЗАВАНТАЖУЄМО ТРЕНЕРІВ ЗА trainer_slug
        trainers = []
        if athlete.get('trainer_slug'):
            try:
                trainer_slugs = athlete['trainer_slug']
                
                # Якщо це строка, парсимо JSON
                if isinstance(trainer_slugs, str):
                    trainer_slugs = json.loads(trainer_slugs)
                
                if trainer_slugs and len(trainer_slugs) > 0:
                    # ✅ Отримуємо тренерів за slug
                    trainers_response = supabase.table("coach") \
                        .select("id, slug, name, position, image, team_category") \
                        .in_("slug", trainer_slugs) \
                        .execute()
                    
                    for trainer in trainers_response.data:
                        if trainer.get('image'):
                            trainer['image_url'] = f"/static/{trainer['image']}"
                        else:
                            trainer['image_url'] = None
                        
                        trainer['category_label'] = get_coach_category_label(trainer.get('team_category', ''))
                    
                    trainers = trainers_response.data
            except Exception as e:
                print(f"Error loading trainers: {e}")
        
        # Обробка фото
        if athlete.get('photos'):
            try:
                if isinstance(athlete['photos'], str):
                    photos_data = json.loads(athlete['photos'])
                else:
                    photos_data = athlete['photos']
                
                # Основне фото
                if photos_data and 'main' in photos_data:
                    athlete['photo_main'] = f"/static/{photos_data['main']}"
                elif photos_data and 'thumb' in photos_data:
                    athlete['photo_main'] = f"/static/{photos_data['thumb']}"
                else:
                    athlete['photo_main'] = None
                
                # Галерея
                if photos_data and 'gallery' in photos_data:
                    athlete['photo_gallery'] = [f"/static/{photo}" for photo in photos_data['gallery']]
                else:
                    athlete['photo_gallery'] = []
            except Exception as e:
                print(f"Error processing photos: {e}")
                athlete['photo_main'] = None
                athlete['photo_gallery'] = []
        else:
            athlete['photo_main'] = None
            athlete['photo_gallery'] = []
        
        # Обробка соціальних мереж
        if athlete.get('social'):
            try:
                if isinstance(athlete['social'], str):
                    athlete['social_links'] = json.loads(athlete['social'])
                else:
                    athlete['social_links'] = athlete['social']
            except:
                athlete['social_links'] = {}
        else:
            athlete['social_links'] = {}
        
        # Обробка досягнень
        if athlete.get('achievements'):
            try:
                if isinstance(athlete['achievements'], str):
                    athlete['achievements_list'] = json.loads(athlete['achievements'])
                else:
                    athlete['achievements_list'] = athlete['achievements']
            except:
                athlete['achievements_list'] = []
        else:
            athlete['achievements_list'] = []
        
        # Вік та дата народження
        if athlete.get('bdate'):
            try:
                if isinstance(athlete['bdate'], str):
                    birth_date = datetime.strptime(athlete['bdate'], '%Y-%m-%d').date()
                else:
                    birth_date = athlete['bdate']
                
                today = date.today()
                athlete['age'] = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                
                months_uk = {
                    1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
                    5: "травня", 6: "червня", 7: "липня", 8: "серпня",
                    9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
                }
                
                athlete['birth_date_formatted'] = f"{birth_date.day} {months_uk[birth_date.month]} {birth_date.year} року"
            except Exception as e:
                print(f"Error calculating age: {e}")
                athlete['age'] = None
                athlete['birth_date_formatted'] = None
        else:
            athlete['age'] = None
            athlete['birth_date_formatted'] = None
        
        # Лейбли
        athlete['sex_label'] = "Чоловік" if athlete.get('sex') == 'men' else "Жінка"
        athlete['status_label'] = {
            "main": "Основний склад",
            "candidate": "Кандидат",
            "reserve": "Резерв"
        }.get(athlete.get('status', 'main'), athlete.get('status'))
        
        def get_age_category(age, sex):
            """
            Визначити вікову категорію спортсмена
            Підтримує різні формати статі: men/man/male та women/woman/female
            """
            if not age or age < 12:
                return "Не вказано"
            
            # Нормалізуємо стать - перевіряємо чи це чоловік
            is_male = str(sex).lower() in ['men', 'man', 'male', 'м', 'чоловік'] if sex else False
            
            if age <= 13:
                return "Діти"
            elif age <= 14:
                return "Молодші юнаки" if is_male else "Молодші дівчата"
            elif age <= 15:
                return "Юнаки" if is_male else "Дівчата"
            elif age <= 16:
                return "Молодші кадети" if is_male else "Молодші кадетки"
            elif age <= 17:
                return "Кадети" if is_male else "Кадетки"
            elif age <= 20:
                return "Юніори" if is_male else "Юніорки"
            elif age <= 22:
                return "Молодь"
            else:
                return "Чоловіки" if is_male else "Жінки"

        
        athlete['age_category'] = get_age_category(athlete.get('age'), athlete.get('sex'))
        
        # Завантажуємо схожих спортсменів
        similar_athletes = []
        try:
            similar_query = supabase.table("athletes").select("id, slug, name, sex, weight, photos")
            
            if athlete.get('sex'):
                similar_query = similar_query.eq("sex", athlete['sex'])
            
            if athlete.get('weight'):
                similar_query = similar_query.eq("weight", athlete['weight'])
            
            similar_query = similar_query.neq("slug", athlete_slug).limit(4)
            
            similar_response = similar_query.execute()
            
            for similar in similar_response.data:
                if similar.get('photos'):
                    try:
                        if isinstance(similar['photos'], str):
                            photos = json.loads(similar['photos'])
                        else:
                            photos = similar['photos']
                        
                        if photos and 'thumb' in photos:
                            similar['photo_url'] = f"/static/{photos['thumb']}"
                        else:
                            similar['photo_url'] = None
                    except:
                        similar['photo_url'] = None
                else:
                    similar['photo_url'] = None
                
                similar_athletes.append(similar)
        except Exception as e:
            print(f"Error loading similar athletes: {e}")
        
        return templates.TemplateResponse("athlete_detail.html", {
            "request": request,
            "athlete": athlete,
            "trainers": trainers,  # ✅ Тренери завантажені за slug
            "similar_athletes": similar_athletes,
            "settings": settings
        })
    
    except Exception as e:
        print(f"Error loading athlete detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("404.html", {
            "request": request,
            "message": "Помилка завантаження даних спортсмена",
            "settings": settings
        }, status_code=500)
@app.get("/team/coaches/{coach_slug}", response_class=HTMLResponse)
async def coach_detail(request: Request, coach_slug: str):
    """Детальна сторінка тренера з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        import json
        
        # Завантажуємо тренера
        response = supabase.table("coach") \
            .select("*") \
            .eq("slug", coach_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "message": "Тренера не знайдено",
                "settings": settings
            }, status_code=404)
        
        coach = response.data[0]
        
        # ✅ ДОДАНО: Нормалізуємо is_national_team
        is_nat = coach.get('is_national_team')
        coach['is_national_team'] = is_nat is True or str(is_nat).lower() == 'true'
        
        print(f"[COACH DETAIL] {coach.get('name')} - is_national_team: {coach['is_national_team']} (type: {type(coach['is_national_team'])})")
        
        # ✅ СПОСІБ 1: Завантажуємо спортсменів за athlete_ids (якщо є)
        athletes = []
        if coach.get('athlete_ids'):
            try:
                athlete_ids = coach['athlete_ids']
                
                if isinstance(athlete_ids, str):
                    try:
                        athlete_ids = json.loads(athlete_ids)
                    except:
                        athlete_ids = [int(x.strip()) for x in athlete_ids.strip('[]').split(',') if x.strip()]
                
                if athlete_ids and len(athlete_ids) > 0:
                    athletes_response = supabase.table("athletes") \
                        .select("id, slug, name, sex, weight, rating, status, photos, bdate") \
                        .in_("id", athlete_ids) \
                        .execute()
                    
                    athletes = athletes_response.data
                    
            except Exception as e:
                print(f"Error loading athletes by IDs: {e}")
        
        # ✅ СПОСІБ 2: Якщо athlete_ids порожній, шукаємо за trainer_slug
        if not athletes:
            try:
                print(f"[DEBUG] Searching athletes by trainer_slug containing: {coach_slug}")
                
                # Отримуємо всіх спортсменів
                all_athletes_response = supabase.table("athletes") \
                    .select("id, slug, name, sex, weight, rating, status, photos, bdate, trainer_slug") \
                    .execute()
                
                # Фільтруємо тих, у кого в trainer_slug є цей тренер
                for athlete in all_athletes_response.data:
                    trainer_slugs = athlete.get('trainer_slug')
                    
                    if trainer_slugs:
                        if isinstance(trainer_slugs, str):
                            try:
                                trainer_slugs = json.loads(trainer_slugs)
                            except:
                                trainer_slugs = []
                        
                        if isinstance(trainer_slugs, list) and coach_slug in trainer_slugs:
                            athletes.append(athlete)
                
                print(f"[DEBUG] Found {len(athletes)} athletes by trainer_slug")
                
            except Exception as e:
                print(f"Error loading athletes by trainer_slug: {e}")
        
        # Обробка спортсменів
        for athlete in athletes:
            # Додаємо фото
            if athlete.get('photos'):
                try:
                    if isinstance(athlete['photos'], str):
                        photos = json.loads(athlete['photos'])
                    else:
                        photos = athlete['photos']
                    
                    if photos and 'thumb' in photos:
                        athlete['photo_url'] = f"/static/{photos['thumb']}"
                    else:
                        athlete['photo_url'] = None
                except:
                    athlete['photo_url'] = None
            else:
                athlete['photo_url'] = None
            
            # Лейбл статусу
            athlete['status_label'] = {
                "main": "Основний склад",
                "candidate": "Кандидат",
                "reserve": "Резерв"
            }.get(athlete.get('status', 'main'), athlete.get('status'))
            
            # Вік
            if athlete.get('bdate'):
                try:
                    from datetime import datetime, date
                    if isinstance(athlete['bdate'], str):
                        birth_date = datetime.strptime(athlete['bdate'], '%Y-%m-%d').date()
                    else:
                        birth_date = athlete['bdate']
                    
                    today = date.today()
                    athlete['age'] = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                except:
                    athlete['age'] = None
        
        # Сортуємо спортсменів
        if athletes:
            status_priority = {"main": 1, "candidate": 2, "reserve": 3}
            athletes = sorted(
                athletes,
                key=lambda x: (
                    status_priority.get(x.get('status', 'reserve'), 99),
                    -int(x.get('rating', 0)) if x.get('rating') else 0
                )
            )
        
        # Обробка фото тренера
        if coach.get('image'):
            coach['image_url'] = f"/static/{coach['image']}"
        else:
            coach['image_url'] = None
        
        # Галерея
        if coach.get('gallery'):
            try:
                if isinstance(coach['gallery'], str):
                    gallery_data = json.loads(coach['gallery'])
                else:
                    gallery_data = coach['gallery']
                
                if isinstance(gallery_data, list):
                    coach['gallery_images'] = [f"/static/{img}" for img in gallery_data if img]
                else:
                    coach['gallery_images'] = []
            except:
                coach['gallery_images'] = []
        else:
            coach['gallery_images'] = []
        
        # Обробка нагород
        if coach.get('awards'):
            try:
                if isinstance(coach['awards'], str):
                    coach['awards_list'] = json.loads(coach['awards'])
                else:
                    coach['awards_list'] = coach['awards']
            except:
                coach['awards_list'] = []
        else:
            coach['awards_list'] = []
        
        # Лейбл категорії
        coach['category_label'] = get_coach_category_label(coach.get('team_category', ''))
        
        return templates.TemplateResponse("coach_detail.html", {
            "request": request,
            "coach": coach,
            "athletes": athletes,
            "settings": settings
        })
    
    except Exception as e:
        print(f"Error loading coach detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("404.html", {
            "request": request,
            "message": "Помилка завантаження даних тренера",
            "settings": settings
        }, status_code=500)


# Роут для завантаження файлів з assets
@app.get("/static/assets/{path:path}")
async def get_static_asset(path: str):
    """Завантаження статичних файлів з assets"""
    file_path = os.path.join("static", "assets", path)
    
    if os.path.exists(file_path):
        # Визначаємо MIME type
        if path.endswith('.pdf'):
            media_type = "application/pdf"
        elif path.endswith('.doc'):
            media_type = "application/msword"
        elif path.endswith('.docx'):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename={os.path.basename(path)}"
            }
        )
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)
@app.get("/regions", response_class=HTMLResponse)
async def regions_page(request: Request, search: str = None):
    """Сторінка регіонів з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        import json
        
        query = supabase.table("regions").select("*").order("number", desc=False)
        
        if search:
            query = query.ilike("id", f"%{search}%")
        
        response = query.execute()
        
        print(f"\n[REGIONS] Отримано {len(response.data)} регіонів з БД")
        
        regions = []
        
        for region in response.data:
            print(f"\n[REGION] Обробка: number={region.get('number')}, id={region.get('id')}")
            
            # Мапимо колонки з БД
            region_data = {
                'number': region.get('number'),
                'slug': region.get('id'),  # id це slug
                'info': region.get('region'),  # region це info
                'structure': region.get('staff'),  # staff це structure
                'judo_schools': region.get('school')  # school це judo_schools
            }
            
            # Обробка region (info) - JSON з назвою та логотипом
            info = region_data.get('info')
            print(f"  info type: {type(info)}")
            
            if isinstance(info, str):
                try:
                    # Замінюємо подвійні лапки на одинарні (CSV формат)
                    info_clean = info.replace('""', '"')
                    info = json.loads(info_clean)
                    print(f"  ✅ Успішно розпарсили info JSON")
                except Exception as e:
                    print(f"  ❌ Помилка парсингу info JSON: {e}")
                    info = []
            
            if isinstance(info, list) and len(info) > 0:
                logo = info[0].get('image', '')
                # ✅ Додаємо /static/ перед шляхом
                region_data['logo_url'] = f"/static/{logo}" if logo else None
                region_data['region_name'] = info[0].get('name-region', 'Не вказано')
                region_data['federation_name'] = info[0].get('name-federation', 'Не вказано')
                print(f"  ✅ logo: {region_data['logo_url']}")
                print(f"  ✅ region: {region_data['region_name']}")
            else:
                region_data['logo_url'] = None
                region_data['region_name'] = 'Не вказано'
                region_data['federation_name'] = 'Не вказано'
                print(f"  ⚠️ info порожній або не список")
            
            # Обробка staff (structure) - керівництво
            structure = region_data.get('structure')
            if isinstance(structure, str):
                try:
                    structure_clean = structure.replace('""', '"')
                    structure = json.loads(structure_clean)
                    print(f"  ✅ Успішно розпарсили structure JSON")
                except Exception as e:
                    print(f"  ❌ Помилка парсингу structure JSON: {e}")
                    structure = {}
            
            if isinstance(structure, dict):
                leadership = structure.get('leadership', {})
                president = leadership.get('president', {})
                region_data['president_name'] = president.get('name')
                photo = president.get('photo', '')
                # ✅ Додаємо /static/ перед шляхом
                region_data['president_photo'] = f"/static/{photo}" if photo else None
                region_data['president_phone'] = president.get('phone')
                print(f"  ✅ president: {region_data['president_name']}")
            else:
                region_data['president_name'] = None
                region_data['president_photo'] = None
                region_data['president_phone'] = None
            
            # Обробка school (judo_schools)
            schools = region_data.get('judo_schools')
            if isinstance(schools, str):
                try:
                    schools_clean = schools.replace('""', '"')
                    schools = json.loads(schools_clean)
                    print(f"  ✅ Успішно розпарсили schools JSON")
                except Exception as e:
                    print(f"  ❌ Помилка парсингу schools JSON: {e}")
                    schools = {}
            
            if isinstance(schools, dict):
                region_data['schools_count'] = len(schools.get('judo_schools', []))
            else:
                region_data['schools_count'] = 0
            
            print(f"  ✅ schools_count: {region_data['schools_count']}")
            
            regions.append(region_data)
        
        print(f"\n[REGIONS] Успішно оброблено {len(regions)} регіонів")
        
        return templates.TemplateResponse("regions.html", {
            "request": request,
            "regions": regions,
            "search_query": search or '',
            "settings": settings
        })
    
    except Exception as e:
        print(f"❌ [REGIONS ERROR] {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("regions.html", {
            "request": request,
            "regions": [],
            "search_query": '',
            "settings": settings
        })


@app.get("/regions/{region_slug}", response_class=HTMLResponse)
async def region_detail_page(request: Request, region_slug: str):
    """Детальна сторінка регіону з SSR"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        response = supabase.table("regions") \
            .select("*") \
            .eq("id", region_slug) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            return templates.TemplateResponse("404.html", {
                "request": request,
                "settings": settings
            }, status_code=404)
        
        region_raw = response.data[0]
        
        import json
        
        # Мапимо колонки
        region = {
            'number': region_raw.get('number'),
            'slug': region_raw.get('id'),
            'info_raw': region_raw.get('region'),
            'structure_raw': region_raw.get('staff'),
            'schools_raw': region_raw.get('school')
        }
        
        # Обробка region (info)
        info = region.get('info_raw')
        if isinstance(info, str):
            info = json.loads(info.replace('""', '"'))
        
        if isinstance(info, list) and len(info) > 0:
            logo = info[0].get('image', '')
            # ✅ Додаємо /static/
            region['logo_url'] = f"/static/{logo}" if logo else None
            region['region_name'] = info[0].get('name-region', 'Не вказано')
            region['federation_name'] = info[0].get('name-federation', 'Не вказано')
        else:
            region['logo_url'] = None
            region['region_name'] = 'Не вказано'
            region['federation_name'] = 'Не вказано'
        
        # Обробка staff (structure)
        structure = region.get('structure_raw')
        if isinstance(structure, str):
            structure = json.loads(structure.replace('""', '"'))
        
        region['leadership'] = {}
        region['contacts'] = {}
        region['personnel'] = []
        
        if isinstance(structure, dict):
            region['leadership'] = structure.get('leadership', {})
            region['contacts'] = structure.get('contacts', {})
            region['personnel'] = structure.get('personnel', [])
            
            # ✅ Додаємо /static/ до фото президента
            if region['leadership'].get('president', {}).get('photo'):
                photo = region['leadership']['president']['photo']
                region['leadership']['president']['photo_url'] = f"/static/{photo}"
        
        # Обробка school (judo_schools)
        schools = region.get('schools_raw')
        if isinstance(schools, str):
            schools = json.loads(schools.replace('""', '"'))
        
        if isinstance(schools, dict):
            region['schools'] = schools.get('judo_schools', [])
        else:
            region['schools'] = []
        
        return templates.TemplateResponse("region_detail.html", {
            "request": request,
            "region": region,
            "settings": settings
        })
    
    except Exception as e:
        print(f"❌ Error loading region detail: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("404.html", {
            "request": request,
            "settings": settings
        }, status_code=404)
# ========== DOCUMENTS PAGE (ВИПРАВЛЕНО) ==========
@app.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    category: str = None,
    search: str = None,
    page: int = 1
):
    """Сторінка документів"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        per_page = 12
        
        # Базовий запит
        query = supabase.table("documents").select("*", count="exact")
        
        # Фільтри
        if category and category != 'all':
            query = query.eq("category", category)
        
        if search:
            query = query.or_(f"title.ilike.%{search}%,tags.ilike.%{search}%")
        
        # Загальна кількість
        total_response = query.execute()
        total_count = total_response.count if hasattr(total_response, 'count') else len(total_response.data)
        total_pages = (total_count + per_page - 1) // per_page
        
        # Отримуємо документи для поточної сторінки
        offset = (page - 1) * per_page
        documents_response = query.order("date", desc=True).range(offset, offset + per_page - 1).execute()
        
        # Обробка документів
        documents = []
        for doc in documents_response.data:
            # ✅ ВИПРАВЛЕНО: filename з БД + додаємо префікс
            filename = doc.get("filename", "")
            file_url = f"/static/assets/documents/{filename}" if filename else ""
            
            # Обробка тегів
            tags_list = []
            if doc.get("tags"):
                tags = doc["tags"]
                if isinstance(tags, str):
                    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                elif isinstance(tags, list):
                    tags_list = [tag.strip() for tag in tags if tag and tag.strip()]
            
            documents.append({
                "id": doc.get("id"),
                "title": doc.get("title", ""),
                "description": doc.get("description", ""),
                "category": doc.get("category", ""),
                "category_display": get_category_display(doc.get("category", "")),
                "date": doc.get("date", ""),
                "file_url": file_url,
                "tags_list": tags_list
            })
        
        return templates.TemplateResponse("documents.html", {
            "request": request,
            "documents": documents,
            "category": category,
            "search_query": search or "",
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        })
    
    except Exception as e:
        print(f"❌ ERROR в documents_page: {e}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse("documents.html", {
            "request": request,
            "documents": [],
            "category": None,
            "search_query": "",
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False
        })


# ========== PROTOCOLS PAGE (ВИПРАВЛЕНО) ==========
@app.get("/protocols", response_class=HTMLResponse)
async def protocols_page(
    request: Request,
    year: int = None,
    category: str = None,
    page: int = 1
):
    """Сторінка протоколів"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        per_page = 10
        
        # Базовий запит
        query = supabase.table("protocols").select("*", count="exact")
        
        # Фільтри
        if year:
            query = query.eq("year", year)
        
        if category and category != 'all':
            query = query.eq("category", category)
        
        # Загальна кількість
        total_response = query.execute()
        total_count = total_response.count if hasattr(total_response, 'count') else len(total_response.data)
        total_pages = (total_count + per_page - 1) // per_page
        
        # Отримуємо протоколи
        offset = (page - 1) * per_page
        protocols_response = query.order("date", desc=True).range(offset, offset + per_page - 1).execute()
        
        # Обробка протоколів
        protocols = []
        for protocol in protocols_response.data:
            files_list = []
            if protocol.get("files"):
                # Парсинг JSON
                files = protocol["files"]
                if isinstance(files, str):
                    try:
                        files = json.loads(files)
                    except:
                        files = []
                
                # ✅ ВИПРАВЛЕНО: використовуємо поле "path" з JSON
                for file in files:
                    file_path = file.get("path", "")
                    # path вже містить "assets/protocols/..." тому просто додаємо /static/
                    file_url = f"/static/{file_path}" if file_path else ""
                    
                    files_list.append({
                        "name": file.get("name", "Файл"),
                        "url": file_url,
                        "type": file.get("type", "document"),
                        "description": file.get("description", ""),
                        "icon": file.get("icon", "results")
                    })
            
            protocols.append({
                "id": protocol.get("id"),
                "title": protocol.get("title", ""),
                "category": protocol.get("category", ""),
                "category_display": get_protocol_category_display(protocol.get("category", "")),
                "location": protocol.get("location", ""),
                "date": protocol.get("date", ""),
                "year": protocol.get("year", ""),
                "status": protocol.get("status", ""),
                "files_list": files_list
            })
        
        return templates.TemplateResponse("protocols.html", {
            "request": request,
            "protocols": protocols,
            "year": year,
            "category": category,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        })
    
    except Exception as e:
        print(f"❌ ERROR в protocols_page: {e}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse("protocols.html", {
            "request": request,
            "protocols": [],
            "year": None,
            "category": None,
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False
        })


@app.get("/regulations", response_class=HTMLResponse)
async def regulations_page(
    request: Request,
    year: int = None,
    status: str = None,
    page: int = 1
):
    """SSR: Regulations page"""
    if not templates:
        return JSONResponse({"error": "Templates directory not found"}, status_code=500)
    
    try:
        from datetime import datetime, date
        
        limit = 12
        offset = (page - 1) * limit
        
        # Query
        query = supabase.table('regulations').select('*', count='exact')
        
        # Filters
        if year and year != 'all':
            query = query.eq('year', year)
        
        if status and status != 'all':
            query = query.eq('status', status)
        
        query = query.order('date_start', desc=True)
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        regulations = response.data if response.data else []
        
        # ✅ АВТОМАТИЧНЕ ВИЗНАЧЕННЯ СТАТУСУ ПО ДАТІ
        today = date.today()
        
        for regulation in regulations:
            try:
                date_start = datetime.fromisoformat(str(regulation.get('date_start')).replace('Z', '+00:00')).date()
                date_end_str = regulation.get('date_end')
                
                # ✅ Якщо date_end відсутня, використовуємо date_start
                if date_end_str:
                    date_end = datetime.fromisoformat(str(date_end_str).replace('Z', '+00:00')).date()
                else:
                    date_end = date_start
                
                # ✅ Визначаємо статус по даті
                if regulation.get('status') in ['cancelled', 'canceled']:
                    regulation['computed_status'] = 'cancelled'
                elif today > date_end:
                    regulation['computed_status'] = 'completed'
                elif date_start <= today <= date_end:
                    regulation['computed_status'] = 'ongoing'
                else:
                    regulation['computed_status'] = 'upcoming'
                
                # ✅ Форматуємо дату (без "None")
                if date_end and date_end != date_start:
                    regulation['date_formatted'] = f"{date_start.strftime('%d.%m.%Y')} — {date_end.strftime('%d.%m.%Y')}"
                else:
                    regulation['date_formatted'] = date_start.strftime('%d.%m.%Y')
                
            except Exception as e:
                print(f"Date parsing error: {e}")
                regulation['computed_status'] = regulation.get('status', 'upcoming')
                regulation['date_formatted'] = str(regulation.get('date_start', ''))
            
            # Status labels
            status_labels = {
                'upcoming': 'Заплановано',
                'ongoing': 'Поточні',
                'completed': 'Завершено',
                'cancelled': 'Скасовано'
            }
            regulation['status_display'] = status_labels.get(regulation.get('computed_status'), 'Заплановано')
            
            # ✅ PDF файл
            if regulation.get('content_type') == 'pdf':
                regulation['file_url'] = f"/static/{regulation.get('path')}"
            
            # ✅ Зображення (для медіа-переглядача)
            if regulation.get('content_type') == 'images' and regulation.get('images'):
                import json
                try:
                    if isinstance(regulation['images'], str):
                        imgs = json.loads(regulation['images'].replace("'", '"'))
                    else:
                        imgs = regulation['images']
                    
                    regulation['images_list'] = []
                    for img in imgs:
                        img['url'] = f"/static/{regulation.get('path')}/{img['filename']}"
                        regulation['images_list'].append(img)
                except:
                    regulation['images_list'] = []
        
        # Pagination
        total = response.count if hasattr(response, 'count') else len(regulations)
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        has_prev = page > 1
        has_next = page < total_pages
        
        return templates.TemplateResponse("regulations.html", {
            "request": request,
            "regulations": regulations,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "year": year,
            "status": status,
            "settings": settings
        })
        
    except Exception as e:
        print(f"REGULATIONS ERROR: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("regulations.html", {
            "request": request,
            "regulations": [],
            "current_page": 1,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "year": None,
            "status": None,
            "settings": settings
        })



# ========== ДОПОМІЖНІ ФУНКЦІЇ (БЕЗ ЗМІН) ==========
def get_category_display(category: str) -> str:
    """Українські назви категорій документів"""
    categories = {
        "statutory": "Статутні",
        "athletes": "Спортсмени",
        "education": "Освіта",
        "competitions": "Змагання"
    }
    return categories.get(category, category.capitalize())


def get_protocol_category_display(category: str) -> str:
    """Українські назви категорій протоколів"""
    categories = {
        "turnir": "Турніри",
        "u16": "До 16 років",
        "u18": "До 18 років",
        "u21": "До 21 року",
        "u23": "До 23 років",
        "cup": "Кубок України",
        "adults": "Дорослі"
    }
    return categories.get(category, category.capitalize())


def get_regulation_status_display(status: str) -> str:
    """Українські назви статусів регламентів"""
    statuses = {
        "upcoming": "Заплановано",
        "ongoing": "Поточні",
        "completed": "Завершено",
        "cancelled": "Скасовано"
    }
    return statuses.get(status, status.capitalize())
