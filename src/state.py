# src/state.py

from typing import Optional, List, Callable

class AppState:
    """
    Holds the application's state, including user info, selections, and settings.
    Implements an observer pattern to notify listeners of state changes.
    """
    def __init__(self):
        # --- User and Session Data ---
        self.user: Optional[dict] = None
        self.worlds: List[dict] = []
        self.campaigns: List[dict] = []

        # --- Selections ---
        self.selected_world_id: Optional[int] = None
        self.selected_campaign_id: Optional[int] = None

        # --- Appearance Settings ---
        self.theme_mode: str = "dark" # "light" or "dark"

        # --- AI Model Configuration ---
        # Updated list of available text models as per your request.
        self.available_text_models: List[str] = [
            "gemini-2.5-pro",
            "gemini-2.5-flash",  # Default
            "Gemini-2.5-flash-lite-preview-06-17",
        ]
        self._selected_text_model: str = "gemini-1.5-flash"

        # Updated list of available image models.
        # NOTE: 'imagen' models often use a different API endpoint (Vertex AI).
        # For now, we list models compatible with the current GeminiService.
        self.available_image_models: List[str] = [
            "Gemini-2.0-flash-preview-image-generation",  # Default, can handle image generation prompts
            "imagen-4.0-generate-preview-06-06",
            "imagen-3.0-generate-002",
        ]
        self._selected_image_model: str = "gemini-1.5-flash"

        # --- Observer Pattern for State Changes ---
        self._callbacks: List[Callable] = []

    # --- Properties for reactive state changes ---

    @property
    def selected_text_model(self) -> str:
        return self._selected_text_model

    @selected_text_model.setter
    def selected_text_model(self, value: str):
        if self._selected_text_model != value:
            self._selected_text_model = value
            self.notify_listeners()

    @property
    def selected_image_model(self) -> str:
        return self._selected_image_model

    @selected_image_model.setter
    def selected_image_model(self, value: str):
        if self._selected_image_model != value:
            self._selected_image_model = value
            self.notify_listeners()

    def register_listener(self, callback: Callable):
        """Register a callback function to be called on state changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_listener(self, callback: Callable):
        """Remove a callback function from the listener list."""
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass # Listener not found

    def notify_listeners(self):
        """Execute all registered callback functions."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error notifying listener {callback.__name__}: {e}")

    def get_selected_world(self) -> Optional[dict]:
        """Finds and returns the full dictionary for the selected world."""
        if self.selected_world_id is None:
            return None
        return next((world for world in self.worlds if world['id'] == self.selected_world_id), None)