# app/utils/file_helpers.py

import os
from datetime import datetime, date

def get_file_extension(filename: str) -> str:
    """Отримати розширення файлу"""
    if not filename:
        return ""
    return os.path.splitext(filename)[1].lower().replace('.', '')

def get_file_icon(filename: str) -> str:
    """Отримати Material Icon для типу файлу"""
    ext = get_file_extension(filename)
    
    icons = {
        'pdf': 'picture_as_pdf',
        'doc': 'article',
        'docx': 'article',
        'xls': 'table_view',
        'xlsx': 'table_view',
        'csv': 'table_view',
        'ppt': 'slideshow',
        'pptx': 'slideshow',
        'zip': 'folder_zip',
        'rar': 'folder_zip',
        'jpg': 'image',
        'jpeg': 'image',
        'png': 'image',
        'txt': 'description',
    }
    
    return icons.get(ext, 'description')

def get_file_icon_color(filename: str) -> dict:
    """Отримати кольори для іконки файлу"""
    ext = get_file_extension(filename)
    
    colors = {
        'pdf': {
            'bg': 'bg-red-50',
            'text': 'text-red-600',
            'border': 'border-red-100'
        },
        'doc': {
            'bg': 'bg-blue-50',
            'text': 'text-blue-600',
            'border': 'border-blue-100'
        },
        'docx': {
            'bg': 'bg-blue-50',
            'text': 'text-blue-600',
            'border': 'border-blue-100'
        },
        'xls': {
            'bg': 'bg-green-50',
            'text': 'text-green-600',
            'border': 'border-green-100'
        },
        'xlsx': {
            'bg': 'bg-green-50',
            'text': 'text-green-600',
            'border': 'border-green-100'
        },
        'ppt': {
            'bg': 'bg-orange-50',
            'text': 'text-orange-600',
            'border': 'border-orange-100'
        },
        'pptx': {
            'bg': 'bg-orange-50',
            'text': 'text-orange-600',
            'border': 'border-orange-100'
        },
    }
    
    return colors.get(ext, {
        'bg': 'bg-gray-50',
        'text': 'text-gray-600',
        'border': 'border-gray-100'
    })

def format_file_size(size_bytes: int) -> str:
    """Форматувати розмір файлу"""
    if not size_bytes:
        return None
    
    # Bytes
    if size_bytes < 1024:
        return f"{size_bytes} B"
    
    # KB
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.1f} KB"
    
    # MB
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.1f} MB"
    
    # GB
    size_gb = size_mb / 1024
    return f"{size_gb:.1f} GB"

def format_date_ukrainian(date_obj) -> str:
    """Форматувати дату українською"""
    if not date_obj:
        return ""
    
    # Якщо це строка, конвертуємо в date
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            return date_obj
    
    months_uk = {
        1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
        5: "травня", 6: "червня", 7: "липня", 8: "серпня",
        9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
    }
    
    return f"{date_obj.day} {months_uk[date_obj.month]} {date_obj.year}"

def is_new_document(date_obj, days: int = 7) -> bool:
    """Перевірити чи документ новий (< days днів)"""
    if not date_obj:
        return False
    
    # Якщо це строка, конвертуємо в date
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            return False
    
    today = date.today()
    delta = today - date_obj
    
    return delta.days <= days
