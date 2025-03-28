from fastapi import FastAPI, Request
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import logging
import json
import pytz

app = FastAPI()

load_dotenv()

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Keuangan WhatsApp").sheet1

WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = os.getenv('GEMINI_API_URL') + GEMINI_API_KEY

VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

def get_wib_time():
    utc_now = datetime.utcnow()
    wib_tz = pytz.timezone("Asia/Jakarta")
    return utc_now.replace(tzinfo=pytz.utc).astimezone(wib_tz)

def classify_text(text):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": f"Kategorikan transaksi ini dalam satu kata, tentukan metode pembayarannya, dan buat deskripsi singkat tanpa simbol tambahan: {text}\nFormat jawaban: kategori; metode pembayaran; deskripsi."}]
        }]
    }
    response = requests.post(GEMINI_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        response_text = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Unknown; Unknown; Tidak ada deskripsi")
        parts = response_text.split(";")
        category = parts[0].strip() if len(parts) > 0 else "Unknown"
        payment_method = parts[1].strip() if len(parts) > 1 else "Unknown"
        description = parts[2].strip() if len(parts) > 2 else "Tidak ada deskripsi"
        return category, payment_method, description
    return "Unknown", "Unknown", "Tidak ada deskripsi"

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    print('sampe sini cok hahaha')
    response = requests.post(url, json=data, headers=headers)
    print(response.text)

def is_duplicate_entry(timestamp, message):
    records = sheet.get_all_values()
    for row in records:
        if row[0] == timestamp and row[1] == message:
            return True
    return False

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    response_message = ''
    data = await request.json()
    
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            message_data = change.get("value", {}).get("messages", [{}])[0]
            message = message_data.get("text", {}).get("body", "")
            sender = message_data.get("from", "")
            
            if not message:
                print("Pesan kosong atau tidak valid, abaikan.")
                continue
            
            category, payment_method, description = classify_text(message)
            amount = [int(s) for s in message.split() if s.isdigit()]
            amount = amount[0] if amount else 0
            timestamp = get_wib_time().strftime("%Y-%m-%d %H:%M:%S")  # Timestamp dalam WIB
            
            print(timestamp)
            
            if not is_duplicate_entry(timestamp, message):
                sheet.append_row([timestamp, message, category, amount, payment_method, description])
            else:
                print("Duplikasi transaksi terdeteksi, tidak menyimpan ulang.")
                continue
            
            response_message = f"✅ Transaksi tercatat!\nKategori: {category}\nJumlah: {amount}\nMetode Pembayaran: {payment_method}\nDeskripsi: {description}\nWaktu: {timestamp}\n\nData telah disimpan di Google Sheets."
            print(response_message)
            send_whatsapp_message(sender, response_message)
    
    return {"status": "success", "message": response_message}


@app.get('/')
async def home():
    return 'Home Page'

logging.basicConfig(level=logging.INFO)

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logging.info(f"Received verification request: mode={mode}, token={token}, challenge={challenge}")

    if mode == "subscribe" and token == "skyfel123":  # Samakan dengan token di Meta Developer Console
        return int(challenge)  # WhatsApp perlu ini untuk verifikasi
    return {"status": "failed"}, 403

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)