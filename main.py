
from fastapi import FastAPI, Request, HTTPException
import requests
import json
from config import settings
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Model untuk Telegram webhook
class TelegramMessage(BaseModel):
    message_id: int
    date: int
    text: Optional[str] = None
    
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

def send_telegram_message(chat_id: int, text: str):
    """Mengirim pesan ke Telegram menggunakan Bot API"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

@app.get("/")
def read_root():
    return {"message": "Telegram Finance Bot is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint untuk menerima webhook dari Telegram"""
    try:
        # Mendapatkan data dari webhook
        data = await request.json()
        
        # Cek apakah ada pesan dalam update
        if "message" in data and "text" in data["message"]:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_text = message["text"]
            user_name = message["from"].get("first_name", "User")
            
            # Membuat pesan balasan (echo)
            reply_text = f"Halo {user_name}! Anda mengirim pesan: '{user_text}'"
            
            # Mengirim pesan balasan
            send_telegram_message(chat_id, reply_text)
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=400, detail="Error processing webhook")

@app.post("/set-webhook")
def set_webhook():
    """Endpoint untuk mengatur webhook Telegram (untuk testing)"""
    webhook_url = "https://yourdomain.com/webhook"  # Ganti dengan URL domain Anda
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
    
    payload = {
        "url": webhook_url
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/webhook-info")
def get_webhook_info():
    """Mendapatkan informasi webhook yang sudah diset"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)