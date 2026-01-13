from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

# Supabase РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РўРћР›Р¬РљРћ РґР»СЏ PostgreSQL Р‘Р”
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_key
)

# вќЊ РЈР±СЂР°Р»Рё РІСЃС‘ РїСЂРѕ Storage - РЅРµ РЅСѓР¶РЅРѕ!