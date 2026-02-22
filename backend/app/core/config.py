from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # This class defines ALL environment variables our app needs
    # Each attribute = one environment variable

    # Database configs  
    DATABASE_URL: str

    # Supabase project URL
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # Open AI config
    OPENAI_API_KEY: str = ""

    # Clearinghouse API config
    CLEARINGHOUSE_API_KEY: str = ""

    # Application settings
    ENVIRONMENT: str = "development" 
    DEBUG: bool = True

    # Pydantic configuration
    class Config:
        """Pydantic configuration for Settinngs class."""
        # This is a nested class that configures how Pydantic behaves
        env_file = ".env"
        case_sensitive = True

# Settings Getter function
@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only load .env once.
    
    Returns:
        Settings: Validated settings object
    """        
    return Settings()