from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP service configuration loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # External API Keys
    courtlistener_api_key: str = ""
    open_states_api_key: str = ""
    ipinfo_token: str = ""
    
    # Service Configuration
    mcp_port: int = 8001
    mcp_case_result_limit: int = 10
    mcp_doc_text_char_limit: int = 6000


settings = Settings()
