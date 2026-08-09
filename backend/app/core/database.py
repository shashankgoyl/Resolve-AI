from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client | None:
    """
    Returns a Supabase client authenticated with the service-role key.
    Returns None when Supabase isn't configured (e.g. pure demo mode) —
    callers must handle that case rather than assume a live DB.

    The service-role key never leaves this module / the backend process.
    """
    settings = get_settings()
    if not settings.supabase_configured:
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
