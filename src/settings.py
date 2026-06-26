import os
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:
    BaseSettings = object
    SettingsConfigDict = lambda **kwargs: None

class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    tavily_api_key: str = ""
    database_url: str = "sqlite:///./data/chongmingbird.db"
    demo_mode: bool = True
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    if BaseSettings is object:
        def __init__(self):
            self.deepseek_api_key=os.getenv("DEEPSEEK_API_KEY","")
            self.deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com")
            self.deepseek_model=os.getenv("DEEPSEEK_MODEL","deepseek-chat")
            self.tavily_api_key=os.getenv("TAVILY_API_KEY","")
            self.database_url=os.getenv("DATABASE_URL","sqlite:///./data/chongmingbird.db")
            self.demo_mode=os.getenv("DEMO_MODE","true").lower() in ("1","true","yes")

def get_settings() -> Settings:
    return Settings()
