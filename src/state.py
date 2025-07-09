from dataclasses import dataclass, field
from typing import Optional
from src.services.supabase_service import SupabaseService
from src.services.gemini_service import GeminiService


@dataclass
class AppState:
    """
    A centralized data class for holding the application's global state.

    This object is created once at application startup and passed to all views.
    It holds instances of our services (like Supabase and Gemini) and any
    other session-wide information, such as the current user or active campaign.
    This approach avoids global variables and ensures a single, predictable
    source of truth for the entire application.
    """
    supabase_service: Optional[SupabaseService] = None
    gemini_service: Optional[GeminiService] = None

    # Example of other state variables you might add later:
    # current_user_id: Optional[str] = None
    # active_campaign_id: Optional[int] = None

    def __post_init__(self):
        """A hook that runs after the object is initialized."""
        print("AppState: Initialized.")
        if self.supabase_service:
            print("AppState: SupabaseService instance received.")
        if self.gemini_service:
            print("AppState: GeminiService instance received.")