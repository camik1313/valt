# ============================================================
# config.py — one place that loads all backend SETTINGS.
#
# Settings come from environment variables (your .env file), so
# you never hard-code things like folder paths or allowed URLs
# into the code. Change the .env, not the code.
#
# pydantic-settings reads the .env automatically and validates it.
# ============================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Tells pydantic to read a file named ".env" in the backend folder.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Comma-separated list of frontend URLs allowed to call this API.
    # (This is the CORS allow-list — explained in main.py.)
    allowed_origins: str = "http://localhost:3000"

    # Where uploaded videos are saved (relative to the backend/ folder).
    upload_dir: str = "data/uploads"

    # Where finished analysis results are saved.
    analyses_dir: str = "data/analyses"

    def origins_list(self) -> list[str]:
        """Turn the comma-separated string into a clean Python list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


# A single shared Settings object the rest of the app imports.
# Created once when the app starts.
settings = Settings()
