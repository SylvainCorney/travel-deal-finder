from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel Deal Scraper"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    
    CORS_ORIGINS: str = "http://localhost:5173"

    # Natural-language search (local Ollama model)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:32b"
    HOME_LOCATION: str = "Bromont, QC"
    DEFAULT_ORIGIN_AIRPORT: str = "YUL"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
