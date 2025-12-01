"""Configuration management using Pydantic Settings"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    google_api_key: str

    # Workspace Configuration
    workspace_dir: str = "~/JobAgentWorkspace"

    # Server Configuration
    backend_host: str = "localhost"
    backend_port: int = 8000

    # CORS Configuration
    allowed_origins: str = "chrome-extension://*,http://localhost:*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def workspace_path(self) -> Path:
        """Returns expanded workspace directory path"""
        return Path(self.workspace_dir).expanduser().resolve()

    @property
    def origins_list(self) -> list[str]:
        """Returns list of allowed origins for CORS"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()
