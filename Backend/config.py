from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend service configuration loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # LLM Configuration
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-20240307"
    
    # Internal Services
    mcp_base_url: str = "http://localhost:8001"
    
    # Service Configuration
    backend_port: int = 8000


settings = Settings()
