# app/models/schemas.py
from __future__ import annotations

from pydantic import BaseModel, Field, computed_field
from datetime import date
from typing import Optional, List, Any, Dict

# ✅ Імпортуємо функції для обробки категорій новин
from app.utils.news.categories import (
    normalize_news_category,
    get_news_category_label
)


# ========== NEWS MODELS ==========
class NewsBase(BaseModel):
    """Базова модель новини"""
    id: str = Field(..., description="Slug для URL")
    title: str = Field(..., description="Заголовок")
    excerpt: str = Field(..., description="Короткий опис")
    category: str = Field(..., description="Категорія")
    publishedAt: date = Field(..., description="Дата публікації")
    featured: bool = Field(default=False, description="Виділена новина")
    image_url: Optional[str] = None
    author_name: str = Field(default="Пресс-служба ФДУ", description="Автор")
    tags: Optional[str] = None


class NewsListItem(NewsBase):
    """Новина для списку (БЕЗ content для оптимізації)"""
    number: Optional[int] = None
    
    @computed_field
    @property
    def image_full_url(self) -> Optional[str]:
        """Повний URL зображення"""
        if self.image_url:
            return f"/static/{self.image_url}"
        return None
    
    @computed_field
    @property
    def tags_list(self) -> List[str]:
        """Теги як список"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(';') if tag.strip()]
        return []
    
    @computed_field
    @property
    def published_date_formatted(self) -> str:
        """Відформатована дата"""
        months_uk = {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
            5: "травня", 6: "червня", 7: "липня", 8: "серпня",
            9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        }
        return f"{self.publishedAt.day} {months_uk[self.publishedAt.month]} {self.publishedAt.year}"
    
    # ✅ ДОДАНО: Нормалізована категорія
    @computed_field
    @property
    def category_normalized(self) -> str:
        """Нормалізована категорія (competitions, team, federation...)"""
        return normalize_news_category(self.category)
    
    # ✅ ДОДАНО: Читабельна назва категорії
    @computed_field
    @property
    def category_label(self) -> str:
        """Читабельна назва категорії (Змагання, Збірна, Федерація...)"""
        return get_news_category_label(self.category_normalized)
    
    # ✅ ДОДАНО: Для backward compatibility з шаблонами
    @computed_field
    @property
    def display_category(self) -> str:
        """Alias для category_label (для сумісності з шаблонами)"""
        return self.category_label
    
    class Config:
        from_attributes = True


class NewsDetail(NewsBase):
    """Повна новина (З content)"""
    number: Optional[int] = None
    content: str = Field(..., description="Повний HTML контент")
    
    @computed_field
    @property
    def image_full_url(self) -> Optional[str]:
        if self.image_url:
            return f"/static/{self.image_url}"
        return None
    
    @computed_field
    @property
    def tags_list(self) -> List[str]:
        if self.tags:
            return [tag.strip() for tag in self.tags.split(';') if tag.strip()]
        return []
    
    @computed_field
    @property
    def published_date_formatted(self) -> str:
        months_uk = {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
            5: "травня", 6: "червня", 7: "липня", 8: "серпня",
            9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        }
        return f"{self.publishedAt.day} {months_uk[self.publishedAt.month]} {self.publishedAt.year}"
    
    # ✅ ДОДАНО: Нормалізована категорія
    @computed_field
    @property
    def category_normalized(self) -> str:
        """Нормалізована категорія"""
        return normalize_news_category(self.category)
    
    # ✅ ДОДАНО: Читабельна назва категорії
    @computed_field
    @property
    def category_label(self) -> str:
        """Читабельна назва категорії"""
        return get_news_category_label(self.category_normalized)
    
    # ✅ ДОДАНО: Для backward compatibility
    @computed_field
    @property
    def display_category(self) -> str:
        """Alias для category_label"""
        return self.category_label
    
    class Config:
        from_attributes = True



# ========== NEW EVENT MODELS ==========

class ProgramItem(BaseModel):
    """Елемент програми змагань"""
    start: str
    end: str
    activity: str

class ProgramDay(BaseModel):
    """День програми"""
    date: str
    items: List[ProgramItem]

class WeightDivision(BaseModel):
    """Вагова категорія"""
    division: str
    weightClasses: List[str]

class Contact(BaseModel):
    """Контактна особа"""
    name: str
    phone: str
    comments: Optional[str] = None

class LiveStream(BaseModel):
    """Трансляція"""
    url: str
    title: str

class Protocol(BaseModel):
    """Протокол"""
    name: str
    path: str
    type: str  # "results" або "protocol"

class InfoBlock(BaseModel):
    """Інформаційний блок"""
    type: str  # "expenses", "prizes", "applications", "important", "rules"
    title: str
    content: str
    contacts: Optional[List[str]] = None
    deadline: Optional[str] = None

class EventBase(BaseModel):
    """Базова модель події (нова структура)"""
    id: int
    slug: str
    title: str
    event_type: str  # "national" або "international"
    category: str  # "cup", "championship", "tournament", "seminar"
    age_group: str
    date_start: date
    date_end: Optional[date] = None
    arrival_date: Optional[date] = None
    city: str
    region: Optional[str] = None
    address: Optional[str] = None
    status: str = "planned"  # "planned", "ongoing", "completed", "cancelled"
    featured: bool = False
    organizer: Optional[str] = None
    team_composition: Optional[str] = None
    program: Optional[List[Dict]] = None  # JSON масив програми
    weight_classes: Optional[List[Dict]] = None  # JSON вагових категорій
    contacts: Optional[List[Dict]] = None  # JSON контактів
    live_streams: Optional[List[Dict]] = None  # JSON трансляцій
    protocols: Optional[List[Dict]] = None  # JSON протоколів
    regulation_path: Optional[str] = None
    image_path: Optional[str] = None
    info_blocks: Optional[List[Dict]] = None  # JSON інфо-блоків
    description: Optional[str] = None

    class Config:
        from_attributes = True

class EventListItem(EventBase):
    """Подія для списку календаря"""
    
    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        """Повний URL зображення"""
        if self.image_path:
            return f"/static/{self.image_path}"
        return None
    
    @computed_field
    @property
    def event_type_label(self) -> str:
        """Українська назва типу"""
        labels = {
            "national": "Національна",
            "international": "Міжнародна"
        }
        return labels.get(self.event_type, self.event_type)
    
    @computed_field
    @property
    def category_label(self) -> str:
        """Українська назва категорії"""
        labels = {
            "cup": "Кубок",
            "championship": "Чемпіонат",
            "tournament": "Турнір",
            'training': 'Тренувальні збори',
            "seminar": "Семінар",
            "training": "Тренувальний збір"
        }
        return labels.get(self.category, self.category)
    
    @computed_field
    @property
    def status_label(self) -> str:
        """Українська назва статусу"""
        labels = {
            "planned": "Заплановано",
            "ongoing": "В процесі",
            "completed": "Завершено",
            "cancelled": "Скасовано"
        }
        return labels.get(self.status, self.status)
    
    @computed_field
    @property
    def date_formatted(self) -> str:
        """Відформатований діапазон дат"""
        months_uk = {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
            5: "травня", 6: "червня", 7: "липня", 8: "серпня",
            9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        }
        
        start = f"{self.date_start.day} {months_uk[self.date_start.month]}"
        
        if self.date_end and self.date_end != self.date_start:
            if self.date_start.month == self.date_end.month:
                return f"{self.date_start.day}-{self.date_end.day} {months_uk[self.date_end.month]} {self.date_end.year}"
            else:
                end = f"{self.date_end.day} {months_uk[self.date_end.month]}"
                return f"{start} - {end} {self.date_end.year}"
        
        return f"{start} {self.date_start.year}"

class EventDetail(EventBase):
    """Повна детальна інформація про подію"""
    
    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        if self.image_path:
            return f"/static/{self.image_path}"
        return None
    
    @computed_field
    @property
    def regulation_url(self) -> Optional[str]:
        """URL регламенту"""
        if self.regulation_path:
            return f"/static/{self.regulation_path}"
        return None
    
    @computed_field
    @property
    def program_parsed(self) -> List[ProgramDay]:
        """Розпарсована програма"""
        if self.program and isinstance(self.program, list):
            return [ProgramDay(**day) for day in self.program]
        return []
    
    @computed_field
    @property
    def weight_classes_parsed(self) -> List[WeightDivision]:
        """Розпарсовані вагові категорії"""
        if self.weight_classes and isinstance(self.weight_classes, list):
            return [WeightDivision(**wc) for wc in self.weight_classes]
        return []
    
    @computed_field
    @property
    def contacts_parsed(self) -> List[Contact]:
        """Розпарсовані контакти"""
        if self.contacts and isinstance(self.contacts, list):
            return [Contact(**c) for c in self.contacts]
        return []
    
    @computed_field
    @property
    def live_streams_parsed(self) -> List[LiveStream]:
        """Розпарсовані трансляції"""
        if self.live_streams and isinstance(self.live_streams, list):
            return [LiveStream(**ls) for ls in self.live_streams]
        return []
    
    @computed_field
    @property
    def protocols_parsed(self) -> List[Protocol]:
        """Розпарсовані протоколи"""
        if self.protocols and isinstance(self.protocols, list):
            return [Protocol(**p) for p in self.protocols]
        return []
    
    @computed_field
    @property
    def info_blocks_parsed(self) -> List[InfoBlock]:
        """Розпарсовані інфо-блоки"""
        if self.info_blocks and isinstance(self.info_blocks, list):
            return [InfoBlock(**ib) for ib in self.info_blocks]
        return []
    
    @computed_field
    @property
    def has_protocols(self) -> bool:
        """Чи є протоколи"""
        return bool(self.protocols and len(self.protocols) > 0)
    
    @computed_field
    @property
    def has_regulation(self) -> bool:
        """Чи є регламент"""
        return bool(self.regulation_path)
# ========== TEAM MODELS ==========
# ========== TEAM MODELS ==========

class AthleteBase(BaseModel):
    """Базова модель спортсмена"""
    id: int
    slug: str
    name: str
    sex: str
    weight: Optional[str] = None
    bdate: Optional[date] = None
    club: Optional[str] = None
    dan: Optional[str] = None
    status: str = "main"
    rating: Optional[int] = None
    trainer: Optional[str] = None  # Текстова назва тренера(ів)
    trainer_slug: Optional[List[str]] = None  # ✅ ЗМІНЕНО: масив slug тренерів
    photos: Optional[Any] = None  # JSON
    social: Optional[Any] = None  # JSON
    achievements: Optional[Any] = None  # JSON

    class Config:
        from_attributes = True

class AthleteListItem(AthleteBase):
    """Спортсмен для списку"""
    
    @computed_field
    @property
    def age(self) -> Optional[int]:
        """Вік спортсмена"""
        if self.bdate:
            today = date.today()
            return today.year - self.bdate.year - ((today.month, today.day) < (self.bdate.month, self.bdate.day))
        return None
    
    @computed_field
    @property
    def photo_url(self) -> Optional[str]:
        """URL основного фото"""
        if self.photos:
            if isinstance(self.photos, dict) and 'thumb' in self.photos:
                return f"/static/{self.photos['thumb']}"
        return None

class AthleteDetail(AthleteBase):
    """Повна детальна інформація про спортсмена"""
    
    @computed_field
    @property
    def age(self) -> Optional[int]:
        """Вік спортсмена"""
        if self.bdate:
            today = date.today()
            return today.year - self.bdate.year - ((today.month, today.day) < (self.bdate.month, self.bdate.day))
        return None
    
    @computed_field
    @property
    def birth_date_formatted(self) -> Optional[str]:
        """Відформатована дата народження"""
        if self.bdate:
            months_uk = {
                1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
                5: "травня", 6: "червня", 7: "липня", 8: "серпня",
                9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
            }
            return f"{self.bdate.day} {months_uk[self.bdate.month]} {self.bdate.year} року"
        return None
    
    @computed_field
    @property
    def photo_main(self) -> Optional[str]:
        """URL основного фото"""
        if self.photos and isinstance(self.photos, dict):
            if 'main' in self.photos:
                return f"/static/{self.photos['main']}"
            elif 'thumb' in self.photos:
                return f"/static/{self.photos['thumb']}"
        return None
    
    @computed_field
    @property
    def photo_gallery(self) -> List[str]:
        """Галерея фото"""
        if self.photos and isinstance(self.photos, dict) and 'gallery' in self.photos:
            return [f"/static/{photo}" for photo in self.photos['gallery']]
        return []
    
    @computed_field
    @property
    def social_links(self) -> dict:
        """Соціальні мережі"""
        if self.social and isinstance(self.social, dict):
            return self.social
        return {}
    
    @computed_field
    @property
    def achievements_list(self) -> List[dict]:
        """Список досягнень"""
        if self.achievements and isinstance(self.achievements, list):
            return self.achievements
        return []
    
    @computed_field
    @property
    def sex_label(self) -> str:
        """Стать українською"""
        return "Чоловік" if self.sex == "men" else "Жінка"
    
    @computed_field
    @property
    def status_label(self) -> str:
        """Статус українською"""
        labels = {
            "main": "Основний склад",
            "candidate": "Кандидат",
            "reserve": "Резерв"
        }
        return labels.get(self.status, self.status)

class CoachBase(BaseModel):
    """Базова модель тренера"""
    id: int
    slug: str
    name: str
    team_category: str
    position: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    image: Optional[str] = None
    gallery: Optional[Any] = None  # JSON
    awards: Optional[Any] = None  # JSON
    is_national_team: Optional[bool] = False
    club: Optional[str] = None
    athlete_ids: Optional[List[int]] = None  # ✅ ЗАЛИШАЄМО: масив ID спортсменів

    class Config:
        from_attributes = True

class CoachListItem(CoachBase):
    """Тренер для списку"""
    
    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        """URL фото тренера"""
        if self.image:
            return f"/static/{self.image}"
        return None
    
    @computed_field
    @property
    def category_label(self) -> str:
        """Українська назва категорії"""
        labels = {
            "men": "Чоловіча збірна",
            "women": "Жіноча збірна",
            "junior_men": "Юніори",
            "junior_women": "Юніорки",
            "cadet_boys": "Кадети (юнаки)",
            "cadet_girls": "Кадети (дівчата)",
            "youth": "Молодіжна збірна",

            "staff": "Адміністративний штаб",
            "reserve": "Резервна команда"
        }
        return labels.get(self.team_category, self.team_category)
    
    @computed_field
    @property
    def gallery_images(self) -> List[str]:
        """Галерея фото тренера"""
        if self.gallery:
            if isinstance(self.gallery, list):
                return [f"/static/{img}" for img in self.gallery]
        return []

class CoachDetail(CoachBase):
    """Повна детальна інформація про тренера"""
    
    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        """URL фото тренера"""
        if self.image:
            return f"/static/{self.image}"
        return None
    
    @computed_field
    @property
    def gallery_images(self) -> List[str]:
        """Галерея фото"""
        if self.gallery:
            if isinstance(self.gallery, list):
                return [f"/static/{img}" for img in self.gallery]
        return []
    
    @computed_field
    @property
    def awards_list(self) -> List[dict]:
        """Список нагород"""
        if self.awards and isinstance(self.awards, list):
            return self.awards
        return []
    
    @computed_field
    @property
    def category_label(self) -> str:
        """Українська назва категорії"""
        labels = {
            "men": "Чоловіча збірна",
            "women": "Жіноча збірна",
            "junior_men": "Юніори",
            "junior_women": "Юніорки",
            "cadet_boys": "Кадети (юнаки)",
            "cadet_girls": "Кадети (дівчата)",
            "youth": "Молодіжна збірна",
            "staff": "Адміністративний штаб",
            "reserve": "Резервна команда"
        }
        return labels.get(self.team_category, self.team_category)

# ========== REGIONS MODELS ==========

class RegionBase(BaseModel):
    """Базова модель регіону"""
    id: int
    slug: str
    info: Optional[Any] = None  # JSON: image, name-region, name-federation
    structure: Optional[Any] = None  # JSON: president, vice_presidents, personnel, contacts
    judo_schools: Optional[Any] = None  # JSON: масив шкіл
    
    class Config:
        from_attributes = True

class RegionListItem(RegionBase):
    """Регіон для списку"""
    
    @computed_field
    @property
    def logo_url(self) -> Optional[str]:
        """URL логотипу федерації"""
        if self.info and isinstance(self.info, list) and len(self.info) > 0:
            logo = self.info[0].get('image')
            if logo:
                return f"/static/{logo}"
        return None
    
    @computed_field
    @property
    def region_name(self) -> str:
        """Назва регіону"""
        if self.info and isinstance(self.info, list) and len(self.info) > 0:
            return self.info[0].get('name-region', 'Не вказано')
        return 'Не вказано'
    
    @computed_field
    @property
    def federation_name(self) -> str:
        """Назва федерації"""
        if self.info and isinstance(self.info, list) and len(self.info) > 0:
            return self.info[0].get('name-federation', 'Не вказано')
        return 'Не вказано'
    
    @computed_field
    @property
    def president_name(self) -> Optional[str]:
        """Ім'я президента"""
        if self.structure and isinstance(self.structure, dict):
            leadership = self.structure.get('leadership', {})
            president = leadership.get('president', {})
            return president.get('name')
        return None
    
    @computed_field
    @property
    def president_photo(self) -> Optional[str]:
        """Фото президента"""
        if self.structure and isinstance(self.structure, dict):
            leadership = self.structure.get('leadership', {})
            president = leadership.get('president', {})
            photo = president.get('photo')
            if photo:
                return f"/static/{photo}"
        return None

class RegionDetail(RegionBase):
    """Повна детальна інформація про регіон"""
    
    @computed_field
    @property
    def logo_url(self) -> Optional[str]:
        """URL логотипу федерації"""
        if self.info and isinstance(self.info, list) and len(self.info) > 0:
            logo = self.info[0].get('image')
            if logo:
                return f"/static/{logo}"
        return None
    
    @computed_field
    @property
    def region_name(self) -> str:
        """Назва регіону"""
        if self.info and isinstance(self.info, list) and len(self.info) > 0:
            return self.info[0].get('name-region', 'Не вказано')
        return 'Не вказано'
    
    @computed_field
    @property
    def federation_name(self) -> str:
        """Назва федерації"""
        if self.info and isinstance(self.info, list) and len(self.info) > 0:
            return self.info[0].get('name-federation', 'Не вказано')
        return 'Не вказано'
    
    @computed_field
    @property
    def leadership_data(self) -> dict:
        """Дані про керівництво"""
        if self.structure and isinstance(self.structure, dict):
            return self.structure.get('leadership', {})
        return {}
    
    @computed_field
    @property
    def contacts_data(self) -> dict:
        """Контакти федерації"""
        if self.structure and isinstance(self.structure, dict):
            return self.structure.get('contacts', {})
        return {}
    
    @computed_field
    @property
    def personnel_list(self) -> List[dict]:
        """Список персоналу"""
        if self.structure and isinstance(self.structure, dict):
            return self.structure.get('personnel', [])
        return []
    
    @computed_field
    @property
    def schools_list(self) -> List[dict]:
        """Список шкіл дзюдо"""
        if self.judo_schools and isinstance(self.judo_schools, dict):
            return self.judo_schools.get('judo_schools', [])
        return []
    
    @computed_field
    @property
    def schools_count(self) -> int:
        """Кількість шкіл"""
        return len(self.schools_list)

# ========== DOCUMENTS MODELS ==========

class DocumentBase(BaseModel):
    """Базова модель документа"""
    number: int
    id: str
    title: str
    category: str
    filename: str
    date: date
    description: Optional[str] = None
    tags: Optional[str] = None
    
    class Config:
        from_attributes = True

class DocumentListItem(DocumentBase):
    """Документ для списку"""
    
    @computed_field
    @property
    def file_url(self) -> str:
        """URL файлу"""
        return f"/static/assets/documents/{self.filename}"
    
    @computed_field
    @property
    def category_display(self) -> str:
        """Відображення категорії"""
        categories = {
            'statutory': 'Статутні документи',
            'athletes': 'Спортсмени',
            'education': 'Освіта',
            'competitions': 'Змагання'
        }
        return categories.get(self.category, self.category)
    
    @computed_field
    @property
    def tags_list(self) -> List[str]:
        """Список тегів"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(';')]
        return []


# ========== PROTOCOLS MODELS ==========

class ProtocolBase(BaseModel):
    """Базова модель протоколу"""
    category: str
    year: int
    title: str
    location: str
    date: date
    status: str
    files: Optional[Any] = None
    
    class Config:
        from_attributes = True

class ProtocolListItem(ProtocolBase):
    """Протокол для списку"""
    
    @computed_field
    @property
    def files_list(self) -> List[dict]:
        """Список файлів"""
        if isinstance(self.files, str):
            import json
            try:
                return json.loads(self.files.replace('""', '"'))
            except:
                return []
        elif isinstance(self.files, list):
            return self.files
        return []
    
    @computed_field
    @property
    def category_display(self) -> str:
        """Відображення категорії"""
        categories = {
            'turnir': 'Турніри',
            'training': 'Тренувальні збори',
            'u16': 'До 16 років',
            'u18': 'До 18 років',
            "adults": "Дорослі",
            'u21': 'До 21 року',
            'u23': 'До 23 років',
            'cup': 'Кубок України'
        }
        return categories.get(self.category, self.category)


# ========== REGULATIONS MODELS ==========

class RegulationBase(BaseModel):
    """Базова модель регламенту"""
    number: int
    year: int
    id: str
    title: str
    city: str
    date_start: date
    date_end: date
    age: str
    organizer: str
    description: Optional[str] = None
    content_type: str  # pdf або images
    path: str
    images: Optional[Any] = None
    status: str
    
    class Config:
        from_attributes = True

class RegulationListItem(RegulationBase):
    """Регламент для списку"""
    
    @computed_field
    @property
    def file_url(self) -> Optional[str]:
        """URL PDF файлу"""
        if self.content_type == 'pdf':
            return f"/static/{self.path}"
        return None
    
    @computed_field
    @property
    def images_list(self) -> List[dict]:
        """Список зображень"""
        if self.content_type == 'images' and self.images:
            if isinstance(self.images, str):
                import json
                try:
                    imgs = json.loads(self.images.replace('""', '"'))
                    # Додаємо повні шляхи
                    for img in imgs:
                        img['url'] = f"/static/{self.path}/{img['filename']}"
                    return imgs
                except:
                    return []
            elif isinstance(self.images, list):
                for img in self.images:
                    img['url'] = f"/static/{self.path}/{img['filename']}"
                return self.images
        return []
    
    @computed_field
    @property
    def status_display(self) -> str:
        """Відображення статусу"""
        statuses = {
            'upcoming': 'Заплановано',
            'completed': 'Завершено',
            'cancelled': 'Скасовано'
        }
        return statuses.get(self.status, self.status)
