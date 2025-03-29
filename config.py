from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_sheet_name: str = "Keuangan Whatsapp"
    
    WHATSAPP_PHONE_NUMBER_ID: int
    WHATSAPP_ACCESS_TOKEN: str
    
    GEMINI_API_KEY: str
    GEMINI_API_URL: str
    
    VERIFY_TOKEN: str
    
    class Config:
        env_file = ".env"

settings = Settings()