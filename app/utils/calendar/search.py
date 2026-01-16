# app/utils/calendar/search.py
"""
Утиліти для пошуку подій
"""

from typing import List, Dict, Any


def search_events(events: List[Dict[str, Any]], search_query: str) -> List[Dict[str, Any]]:
    """
    Пошук подій по title, city, region, organizer
    
    Args:
        events: Список подій
        search_query: Пошуковий запит
        
    Returns:
        Відфільтрований список подій
    """
    if not search_query or not search_query.strip():
        return events
    
    search_lower = search_query.lower().strip()
    
    filtered_events = []
    for event in events:
        # Пошук в назві
        if search_lower in (event.get('title') or '').lower():
            filtered_events.append(event)
            continue
            
        # Пошук в місті
        if search_lower in (event.get('city') or '').lower():
            filtered_events.append(event)
            continue
            
        # Пошук в регіоні
        if search_lower in (event.get('region') or '').lower():
            filtered_events.append(event)
            continue
            
        # Пошук в організаторі
        if search_lower in (event.get('organizer') or '').lower():
            filtered_events.append(event)
            continue
    
    return filtered_events


def highlight_search_term(text: str, search_query: str) -> str:
    """
    Підсвічує пошуковий термін в тексті (для майбутнього використання)
    
    Args:
        text: Текст для підсвітки
        search_query: Пошуковий запит
        
    Returns:
        Текст з HTML тегами для підсвітки
    """
    if not search_query or not text:
        return text
    
    import re
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark>{m.group()}</mark>', text)
