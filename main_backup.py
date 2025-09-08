
from fastapi import FastAPI, Request, HTTPException
import requests
import json
import os
import io
import base64
from datetime import datetime
import pytz
from config import settings
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from PIL import Image
import google.generativeai as genai

app = FastAPI()

# Konfigurasi Gemini AI
genai.configure(api_key=settings.GEMINI_API_KEY)

# Model untuk response data keuangan
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

# Model untuk Telegram webhook
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

def get_file_url(file_id: str):
    """Mendapatkan URL file dari Telegram"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile"
    payload = {"file_id": file_id}
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        
        if result.get("ok"):
            file_path = result["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
            return file_url
        return None
    except Exception as e:
        print(f"Error getting file URL: {e}")
        return None

def download_image(file_url: str):
    """Mengunduh gambar dari URL"""
    try:
        response = requests.get(file_url)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def process_image(image_data: bytes):
    """Memproses gambar dan mendapatkan informasi dasar"""
    try:
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        format_img = image.format
        mode = image.mode
        
        return {
            "width": width,
            "height": height,
            "format": format_img,
            "mode": mode,
            "size_bytes": len(image_data)
        }
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def encode_image_to_base64(image_data: bytes) -> str:
    """Mengconvert image data ke base64 untuk Gemini AI"""
    return base64.b64encode(image_data).decode('utf-8')

def get_current_timestamp() -> str:
    """Mendapatkan timestamp saat ini dalam timezone Jakarta"""
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(jakarta_tz)
    return current_time.strftime("%Y-%m-%d %H:%M:%S")

def create_gemini_prompt() -> str:
    """Membuat prompt untuk Gemini AI"""
    return """
Saya akan memberikan Anda teks atau gambar yang berkaitan dengan transaksi keuangan. 
Tolong analisis dan ekstrak informasi berikut dalam format JSON yang VALID:

{
  "timestamp": "YYYY-MM-DD HH:MM:SS (jika ada waktu di gambar, gunakan itu. Jika tidak, gunakan waktu saat ini)",
  "prompt_text": "teks yang diberikan atau deskripsi gambar",
  "category": "kategori transaksi (entertainment, transfer, billings, food, shopping, transport, dll)",
  "amount": "total jumlah uang (angka saja, tanpa mata uang)",
  "payment_method": "metode pembayaran (cash, dana, gopay, shopeepay, ovo, bca, bni, dll)",
  "type": "jenis transaksi (income/expense/transfer)",
  "summary": "ringkasan singkat transaksi",
  "items": [
    {
      "name": "nama item",
      "quantity": "jumlah item (angka)",
      "price": "harga per item (angka)"
    }
  ]
}

Aturan penting:
1. Berikan HANYA JSON yang valid, tanpa penjelasan tambahan
2. Untuk amount, gunakan angka saja (contoh: 50000, bukan "Rp 50.000")
3. Jika tidak ada informasi spesifik, gunakan nilai default yang masuk akal
4. Untuk timestamp, jika ada tanggal/waktu di gambar, gunakan itu. Jika tidak, biarkan kosong
5. Items hanya diisi jika ada daftar pembelian yang jelas (seperti struk belanja)
6. Category harus spesifik (contoh: food, transport, entertainment, shopping, transfer, billings)
7. Type: "expense" untuk pengeluaran, "income" untuk pemasukan, "transfer" untuk transfer antar akun

Analisis data berikut:
"""

async def process_with_gemini(text_content: str = None, image_data: bytes = None) -> Dict[str, Any]:
    """Memproses teks atau gambar dengan Gemini AI"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = create_gemini_prompt()
        
        if image_data and text_content:
            # Jika ada gambar dan teks
            image_base64 = encode_image_to_base64(image_data)
            prompt += f"\n\nTeks: {text_content}\nGambar: [Gambar terlampir]"
            
            response = model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            ])
            
        elif image_data:
            # Hanya gambar
            image_base64 = encode_image_to_base64(image_data)
            prompt += "\n\nGambar: [Gambar terlampir]"
            
            response = model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg", 
                    "data": image_base64
                }
            ])
            
        elif text_content:
            # Hanya teks
            prompt += f"\n\nTeks: {text_content}"
            response = model.generate_content(prompt)
            
        else:
            return {"error": "Tidak ada teks atau gambar yang diberikan"}
        
        # Parse response JSON
        response_text = response.text.strip()
        
        # Membersihkan response jika ada markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        financial_data = json.loads(response_text)
        
        # Jika timestamp kosong, gunakan waktu saat ini
        if not financial_data.get("timestamp"):
            financial_data["timestamp"] = get_current_timestamp()

        return financial_data
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response text: {response_text}")
        return {"error": f"Invalid JSON response from Gemini: {str(e)}"}
    except Exception as e:
        print(f"Error processing with Gemini: {e}")
        return {"error": str(e)}

def send_telegram_message(chat_id: int, text: str):
    """Mengirim pesan ke Telegram menggunakan Bot API"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
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
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "User")
            
            # Menangani pesan teks
            if "text" in message:
                user_text = message["text"]
                
                # Kirim pesan bahwa bot sedang memproses
                send_telegram_message(chat_id, "🤖 Sedang menganalisis pesan Anda...")
                
                # Proses dengan Gemini AI
                financial_data = await process_with_gemini(text_content=user_text)
                
                if "error" in financial_data:
                    reply_text = f"❌ *Error*\n\n{financial_data['error']}"
                else:
                    # Format response yang lebih readable
                    reply_text = f"� *Analisis Keuangan*\n\n"
                    reply_text += f"👤 *User:* {user_name}\n"
                    reply_text += f"⏰ *Waktu:* {financial_data.get('timestamp', 'N/A')}\n"
                    reply_text += f"📝 *Teks:* {financial_data.get('prompt_text', 'N/A')}\n"
                    reply_text += f"🏷️ *Kategori:* {financial_data.get('category', 'N/A')}\n"
                    reply_text += f"💵 *Jumlah:* Rp {financial_data.get('amount', 0):,.0f}\n"
                    reply_text += f"💳 *Metode:* {financial_data.get('payment_method', 'N/A')}\n"
                    reply_text += f"📊 *Tipe:* {financial_data.get('type', 'N/A')}\n"
                    reply_text += f"📋 *Ringkasan:* {financial_data.get('summary', 'N/A')}\n"
                    
                    if financial_data.get('items'):
                        reply_text += f"\n🛒 *Item yang dibeli:*\n"
                        for item in financial_data['items']:
                            reply_text += f"• {item.get('name', 'N/A')} x{item.get('quantity', 1)} - Rp {item.get('price', 0):,.0f}\n"
                
                send_telegram_message(chat_id, reply_text)
            
            # Menangani pesan gambar
            elif "photo" in message:
                photos = message["photo"]
                largest_photo = photos[-1]
                file_id = largest_photo["file_id"]
                caption = message.get("caption", "")
                
                # Kirim pesan bahwa bot sedang memproses
                send_telegram_message(chat_id, "🤖 Sedang menganalisis gambar Anda...")
                
                # Mendapatkan URL file
                file_url = get_file_url(file_id)
                
                if file_url:
                    # Mengunduh gambar
                    image_data = download_image(file_url)
                    
                    if image_data:
                        # Proses dengan Gemini AI
                        financial_data = await process_with_gemini(
                            text_content=caption if caption else None,
                            image_data=image_data
                        )
                        
                        if "error" in financial_data:
                            reply_text = f"❌ *Error*\n\n{financial_data['error']}"
                        else:
                            # Format response
                            reply_text = f"🖼️💰 *Analisis Gambar Keuangan*\n\n"
                            reply_text += f"👤 *User:* {user_name}\n"
                            reply_text += f"⏰ *Waktu:* {financial_data.get('timestamp', 'N/A')}\n"
                            
                            if caption:
                                reply_text += f"📝 *Caption:* {caption}\n"
                            
                            reply_text += f"🏷️ *Kategori:* {financial_data.get('category', 'N/A')}\n"
                            reply_text += f"💵 *Jumlah:* Rp {financial_data.get('amount', 0):,.0f}\n"
                            reply_text += f"💳 *Metode:* {financial_data.get('payment_method', 'N/A')}\n"
                            reply_text += f"📊 *Tipe:* {financial_data.get('type', 'N/A')}\n"
                            reply_text += f"� *Ringkasan:* {financial_data.get('summary', 'N/A')}\n"
                            
                            if financial_data.get('items'):
                                reply_text += f"\n� *Item yang dibeli:*\n"
                                for item in financial_data['items']:
                                    reply_text += f"• {item.get('name', 'N/A')} x{item.get('quantity', 1)} - Rp {item.get('price', 0):,.0f}\n"
                        
                        send_telegram_message(chat_id, reply_text)
                    else:
                        send_telegram_message(chat_id, f"❌ Gagal mengunduh gambar dari {user_name}")
                else:
                    send_telegram_message(chat_id, f"❌ Gagal mendapatkan URL gambar dari {user_name}")
            
            # Menangani jenis pesan lainnya
            else:
                reply_text = f"ℹ️ *Pesan Tidak Didukung*\n\nHalo {user_name}!\n"
                reply_text += "Saat ini bot hanya mendukung:\n"
                reply_text += "• 🗨️ Pesan teks tentang transaksi keuangan\n"
                reply_text += "• 🖼️ Gambar struk/nota/transaksi\n"
                reply_text += "\nBot akan menganalisis dan mengekstrak informasi keuangan dari pesan Anda."
                
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

@app.post("/test-send")
def test_send_message(chat_id: int, message: str):
    """Endpoint untuk testing pengiriman pesan (untuk development)"""
    try:
        result = send_telegram_message(chat_id, message)
        return {"status": "sent", "result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/bot-info")
def get_bot_info():
    """Mendapatkan informasi bot"""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/test-gemini")
async def test_gemini(text: str = None):
    """Endpoint untuk testing Gemini AI dengan teks (untuk development)"""
    try:
        if not text:
            return {"error": "Text parameter is required"}
            
        result = await process_with_gemini(text_content=text)
        return {"status": "processed", "result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": get_current_timestamp(),
        "services": {
            "telegram_bot": "configured" if settings.TELEGRAM_BOT_TOKEN else "not_configured",
            "gemini_ai": "configured" if settings.GEMINI_API_KEY else "not_configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)