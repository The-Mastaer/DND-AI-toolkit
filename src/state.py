# src/state.py

from dataclasses import dataclass
from .services.supabase_service import SupabaseService
from .services.gemini_service import GeminiService
from .app_settings import AppSettings

@dataclass
class AppState:
    """
    A centralized class to hold the application's state.
    This includes initialized service clients and runtime data
    that needs to be shared across different views.
    """
    supabase_service: SupabaseService
    gemini_service: GeminiService
    app_settings: AppSettings
    selected_world_for_campaigns: dict = None # Used to pass context from World Manager to Campaign Manager
    refresh_home_view: callable = None # Callback to refresh the home view
