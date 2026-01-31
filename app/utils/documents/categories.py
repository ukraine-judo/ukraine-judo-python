"""
Document category mapping utilities
Категорії для документів ФДУ
"""

# Категорії документів
DOCUMENT_CATEGORY_MAPPING = {
    'statutory': 'statutory',
    'competitions': 'competitions',
    'athletes': 'athletes',
    'education': 'education',
    'medical': 'medical',
}

DOCUMENT_CATEGORY_LABELS = {
    'all': 'Всі документи',
    'statutory': 'Статутні документи',
    'competitions': 'Змагання та протоколи',
    'athletes': 'Спортсмени та рейтинги',
    'education': 'Освіта та суддівство',
    'medical': 'Медичні документи',
}


def normalize_document_category(category: str) -> str:
    """Нормалізує категорію документа"""
    if not category:
        return 'statutory'
    return DOCUMENT_CATEGORY_MAPPING.get(category, category)


def get_document_category_label(category: str) -> str:
    """Повертає читабельну назву категорії документа"""
    return DOCUMENT_CATEGORY_LABELS.get(category, category.capitalize())
