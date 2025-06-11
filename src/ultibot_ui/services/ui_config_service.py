import json
from typing import Optional, Dict, Any, List # Added List
from uuid import UUID
from pathlib import Path

from src.ultibot_ui.services.api_client import UltiBotAPIClient
# Assuming a Pydantic model for configuration might exist in the future, e.g.:
# from src.ultibot_ui.models import UserConfiguration

# For local fallback or if not using API for certain configs
DEFAULT_FAVORITE_PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD"]
CONFIG_FILE_NAME = "ultibot_ui_config.json" # For local storage if needed

class UIConfigService:
    def __init__(self, api_client: UltiBotAPIClient, user_id: Optional[UUID] = None): # user_id can be set later
        self.api_client = api_client
        self.user_id = user_id # Store user_id for convenience
        # self.backend_config_service = backend_config_service # Removed
        self.config_data: Dict[str, Any] = {} # In-memory cache for config

        # For local config storage (optional, could be purely API driven)
        # self.config_dir = Path.home() / ".ultibot" # Example config directory
        # self.config_dir.mkdir(parents=True, exist_ok=True)
        # self.config_file_path = self.config_dir / CONFIG_FILE_NAME

    def set_user_id(self, user_id: UUID):
        """Sets the user ID for the service and clears any cached config for previous user."""
        if self.user_id != user_id:
            self.user_id = user_id
            self.config_data = {} # Reset cache

    async def load_user_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Loads user configuration from the backend.
        Uses cached data if available, otherwise fetches from API.
        For now, returns a dictionary. A Pydantic model can be used for validation/structure later.
        """
        if not self.user_id:
            # Or raise error, or handle anonymous users differently
            print("Error: User ID not set in UIConfigService.")
            return None

        if self.config_data: # Serve from cache if available
            return self.config_data

        # Try fetching from API
        config = await self.api_client.get_user_configuration(self.user_id)
        if config:
            self.config_data = config
            # Optionally, save a local copy as well if hybrid approach is desired
            # self._save_local_config_copy(config)
            return config

        # Fallback: if API fails or returns nothing, could try loading a local copy
        # config = self._load_local_config_copy()
        # if config:
        #     self.config_data = config
        #     return config

        # Fallback to default if nothing else
        # self.config_data = {"favoritePairs": DEFAULT_FAVORITE_PAIRS} # Example default
        return None # Or return some default config object

    async def save_user_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        Saves user configuration to the backend.
        Updates the in-memory cache on successful save.
        """
        if not self.user_id:
            print("Error: User ID not set in UIConfigService for saving.")
            return False

        success = await self.api_client.save_user_configuration(self.user_id, config_data)
        if success:
            self.config_data = config_data # Update cache
            # Optionally, save a local copy as well
            # self._save_local_config_copy(config_data)
        return success

    # --- Methods for managing specific config items like favoritePairs ---
    # These can operate on the self.config_data cache, and rely on
    # load_user_configuration and save_user_configuration to sync with backend.

    async def get_favorite_pairs(self) -> List[str]:
        """Gets favorite pairs from the loaded configuration."""
        config = await self.load_user_configuration() # Ensure config is loaded
        return config.get("favoritePairs", DEFAULT_FAVORITE_PAIRS) if config else DEFAULT_FAVORITE_PAIRS

    async def add_favorite_pair(self, pair: str) -> bool:
        """Adds a pair to favorites and attempts to save configuration."""
        if not self.user_id: return False
        config = await self.load_user_configuration() # Ensure config is loaded
        if not config: # If loading failed or returned None, initialize
            config = {"favoritePairs": []}

        current_favorites = config.get("favoritePairs", [])
        if pair not in current_favorites:
            current_favorites.append(pair)
            config["favoritePairs"] = current_favorites
            return await self.save_user_configuration(config)
        return True # Pair already exists

    async def remove_favorite_pair(self, pair: str) -> bool:
        """Removes a pair from favorites and attempts to save configuration."""
        if not self.user_id: return False
        config = await self.load_user_configuration()
        if not config: return False # Nothing to remove from

        current_favorites = config.get("favoritePairs", [])
        if pair in current_favorites:
            current_favorites.remove(pair)
            config["favoritePairs"] = current_favorites
            return await self.save_user_configuration(config)
        return True # Pair not found, or already removed

    # --- Local file storage (Optional, example if needed for offline or fallback) ---
    # def _save_local_config_copy(self, config_data: Dict[str, Any]):
    #     """Saves a copy of the config locally."""
    #     try:
    #         with open(self.config_file_path, "w") as f:
    #             json.dump(config_data, f, indent=4)
    #     except IOError as e:
    #         print(f"Error saving local config copy: {e}")

    # def _load_local_config_copy(self) -> Optional[Dict[str, Any]]:
    #     """Loads config from a local file, if it exists."""
    #     if self.config_file_path.exists():
    #         try:
    #             with open(self.config_file_path, "r") as f:
    #                 return json.load(f)
    #         except (IOError, json.JSONDecodeError) as e:
    #             print(f"Error loading local config copy: {e}")
    #             return None
    #     return None

    async def close_services(self):
        """Placeholder for any cleanup if needed."""
        print("UIConfigService closed.")

# Example UserConfiguration Pydantic model (can be in models.py)
# class UserConfiguration(BaseModel):
#     user_id: UUID
#     favoritePairs: List[str] = DEFAULT_FAVORITE_PAIRS
#     displaySettings: Optional[Dict[str, Any]] = None
#     # ... other config fields
