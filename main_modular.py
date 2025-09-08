from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from config import settings
from services.finance_bot_service import FinanceBotService
from services.telegram_service import TelegramService
from services.gemini_service import GeminiService
import os
from datetime import datetime
import pytz

app = FastAPI()

# Initialize services
finance_bot = FinanceBotService()
telegram_service = TelegramService()
gemini_service = GeminiService()

# Models untuk Telegram webhook
class TelegramPhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None

class TelegramMessage(BaseModel):
    message_id: int
    date: int
    text: Optional[str] = None
    photo: Optional[List[dict]] = None
    caption: Optional[str] = None
    
class TelegramChat(BaseModel):
    id: int
    type: str

class TelegramUser(BaseModel):
    id: int
    first_name: str
    username: Optional[str] = None

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None

# Models untuk response data keuangan
class FinancialItem(BaseModel):
    name: str
    quantity: Optional[int] = 1
    price: Optional[float] = 0.0

class FinancialData(BaseModel):
    timestamp: str
    prompt_text: str
    category: str
    amount: float
    payment_method: str
    type: str  # income/expense/transfer
    summary: str
    items: List[FinancialItem] = []

@app.get("/")
def read_root():
    return {"message": "Telegram Finance Bot is running (Modular Version)"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint untuk menerima webhook dari Telegram"""
    try:
        # Mendapatkan data dari webhook
        data = await request.json()
        
        # Cek apakah ada pesan dalam update
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "User")
            
            # Menangani pesan teks
            if "text" in message:
                user_text = message["text"]
                await finance_bot.process_text_message(chat_id, user_name, user_text)
            
            # Menangani pesan gambar
            elif "photo" in message:
                photos = message["photo"]
                largest_photo = photos[-1]
                file_id = largest_photo["file_id"]
                caption = message.get("caption", "")
                
                await finance_bot.process_image_message(chat_id, user_name, file_id, caption)
            
            # Menangani jenis pesan lainnya
            else:
                finance_bot.process_unsupported_message(chat_id, user_name)
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=400, detail="Error processing webhook")

@app.post("/set-webhook")
def set_webhook():
    """Endpoint untuk mengatur webhook Telegram (untuk testing)"""
    webhook_url = "https://yourdomain.com/webhook"  # Ganti dengan URL domain Anda
    result = telegram_service.set_webhook(webhook_url)
    return result

@app.get("/webhook-info")
def get_webhook_info():
    """Mendapatkan informasi webhook yang sudah diset"""
    return telegram_service.get_webhook_info()

@app.post("/test-send")
def test_send_message(chat_id: int, message: str):
    """Endpoint untuk testing pengiriman pesan (untuk development)"""
    try:
        result = telegram_service.send_message(chat_id, message)
        return {"status": "sent", "result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/bot-info")
def get_bot_info():
    """Mendapatkan informasi bot"""
    return telegram_service.get_bot_info()

@app.post("/test-gemini")
async def test_gemini(text: str = None):
    """Endpoint untuk testing Gemini AI dengan teks (untuk development)"""
    try:
        if not text:
            return {"error": "Text parameter is required"}
            
        result = await gemini_service.process_financial_data(text_content=text)
        return {"status": "processed", "result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(jakarta_tz)
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "healthy",
        "timestamp": timestamp,
        "services": {
            "telegram_bot": "configured" if settings.TELEGRAM_BOT_TOKEN else "not_configured",
            "gemini_ai": "configured" if settings.GEMINI_API_KEY else "not_configured",
            "google_sheets": "configured" if os.path.exists('credentials.json') else "not_configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
