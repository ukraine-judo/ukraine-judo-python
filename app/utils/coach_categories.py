# app/utils/coach_categories.py

COACH_CATEGORY_LABELS = {
    'junior_women': 'Юніорки',
    'cadet_girls': 'Кадетки',
    'women': 'Жінки',
    'youth': 'Молодь',
    'senior': 'Ветерани',
    'staff': 'Штат',
    'junior_men': 'Юніори',
    'men': 'Чоловіки',
    'cadet_boys': 'Кадети',
    'reserve': 'Резерв'
}

def get_coach_category_label(category: str) -> str:
    """
    Повертає українську назву категорії тренера
    """
    return COACH_CATEGORY_LABELS.get(category, category)
