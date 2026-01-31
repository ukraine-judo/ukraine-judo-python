"""
News category mapping utilities
Конвертує старі категорії новин в нові без зміни БД
"""

# Маппінг старих категорій новин на нові
NEWS_CATEGORY_MAPPING = {
    # Змагання (competitions)
    'achievements': 'competitions',
    'results': 'competitions',
    'announcements': 'competitions',
    'events': 'competitions',
    
    # Федерація (federation)
    'decisions': 'federation',
    'statements': 'federation',
    'federationNews': 'federation',
    'partnerships': 'federation',
    
    # Збірна (team)
    'greetings': 'team',
    
    # Залишаються без змін
    'competitions': 'competitions',
    'interviews': 'interviews',
    'education': 'education',
    'team': 'team',
    'federation': 'federation',
    'media': 'media',
}

# Нові назви категорій для відображення
NEWS_CATEGORY_LABELS = {
    'all': 'Усі новини',
    'competitions': 'Змагання',
    'team': 'Збірна',
    'federation': 'Федерація',
    'interviews': 'Інтерв\'ю',
    'education': 'Освіта',
    'media': 'Медіа',
}

# Зворотній маппінг: нова категорія -> список старих
NEWS_REVERSE_CATEGORY_MAPPING = {
    'competitions': ['achievements', 'results', 'announcements', 'events', 'competitions'],
    'federation': ['decisions', 'statements', 'federationNews', 'partnerships', 'federation'],
    'team': ['greetings', 'team'],
    'interviews': ['interviews'],
    'education': ['education'],
    'media': ['media'],
}


def normalize_news_category(old_category: str) -> str:
    """
    Конвертує стару категорію новини в нову
    
    Args:
        old_category: Стара назва категорії з БД
        
    Returns:
        Нова назва категорії
    """
    if not old_category:
        return 'media'  # Дефолтна категорія
    return NEWS_CATEGORY_MAPPING.get(old_category, old_category)


def get_old_news_categories_for_filter(new_category: str) -> list:
    """
    Повертає список старих категорій новин для фільтрації в БД
    
    Args:
        new_category: Нова назва категорії (competitions, team, etc.)
        
    Returns:
        Список старих категорій для SQL запиту
    """
    return NEWS_REVERSE_CATEGORY_MAPPING.get(new_category, [new_category])


def get_news_category_label(category: str) -> str:
    """
    Повертає читабельну назву категорії новини
    
    Args:
        category: Назва категорії
        
    Returns:
        Читабельна назва
    """
    return NEWS_CATEGORY_LABELS.get(category, category.capitalize())
