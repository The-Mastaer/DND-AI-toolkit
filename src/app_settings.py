from dataclasses import dataclass, asdict
import json


@dataclass
class AppSettings:
    """
    A data class to hold user-configurable application settings.

    This provides a structured way to manage settings like AI model parameters.
    It includes methods for serialization to and from JSON, which is necessary
    for storing the object in Flet's client storage.
    """
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7
    top_p: float = 1.0

    def to_json(self) -> str:
        """Serializes the dataclass instance to a JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'AppSettings':
        """
        Creates a dataclass instance from a JSON string.

        Args:
            json_str: The JSON string representing the settings.

        Returns:
            An instance of AppSettings. Returns default settings if JSON is
            invalid or empty.
        """
        if not json_str:
            return cls()
        try:
            data = json.loads(json_str)
            return cls(**data)
        except (json.JSONDecodeError, TypeError):
            # Return default settings if there's an error
            return cls()