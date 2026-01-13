# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase (тільки для БД!)
    supabase_url: str
    supabase_key: str
    
    # App
    app_name: str = "Федерація Дзюдо України"
    debug: bool = False
    
    # Assets base URL (для фронтенда)
    assets_base_url: str = "/static/assets"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
