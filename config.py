from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_sheet_name: str = "Keuangan Telegram"
    
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    
    GEMINI_API_KEY: str
    GEMINI_API_URL: str
    
    OPENAI_API_KEY: str
    
    VERIFY_TOKEN: str
    
    # AI Provider setting - default menggunakan chatgpt
    ai_provider: str = "chatgpt"  # "chatgpt" atau "gemini"
    
    class Config:
        env_file = ".env"

settings = Settings()