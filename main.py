import asyncio
from datetime import datetime
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import pytz
from schemas.models import Transaction
from services.gemini_service import GeminiService
from services.sheets_service import SheetsService
from services.telegram_service import TelegramClient
from config import settings
from dialog.telegram_button import TelegramButton

app = FastAPI()
logger = logging.getLogger(__name__)
sheets = SheetsService()
gemini = GeminiService()

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    try:
        payload = await request.json()

        # Ambil data pesan dari payload Telegram
        message_data = payload.get("message", {})
        sender = message_data.get("chat", {}).get("id", "")
        unix_time = message_data.get('date', '')
        unix_time = int(unix_time) if unix_time else int(datetime.now().timestamp())
        wib_now = datetime.fromtimestamp(unix_time).astimezone(pytz.timezone("Asia/Jakarta"))
        formatted_time = wib_now.strftime("%Y-%m-%d %H:%M:%S")

        # Deteksi apakah pesan berupa foto atau teks
        message_text = message_data.get("text", "")
        image_bytes = None
        if "photo" in message_data:
            # Ambil file_id foto dengan resolusi terbesar
            photo_sizes = message_data["photo"]
            file_id = photo_sizes[-1]["file_id"] if photo_sizes else None
            if file_id:
                # Dapatkan file_path dari Telegram API
                import requests
                bot_token = settings.TELEGRAM_BOT_TOKEN
                file_info = requests.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}").json()
                file_path = file_info.get("result", {}).get("file_path")
                if file_path:
                    # Download file gambar
                    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                    img_response = requests.get(file_url)
                    if img_response.ok:
                        image_bytes = img_response.content
                        message_text = None  # Kosongkan agar Gemini hanya dapat gambar
                    else:
                        message_text = "Gagal mengunduh gambar dari Telegram."
                        logger.warning("Gagal mengunduh gambar dari Telegram.")

        logger.info(f"Pesan diterima dari {sender}: {message_text}")

        # Menentukan tombol yang akan dikirim
        # 1. **Jika pesan berisi perintah tombol**
        if (message_text or "").lower() in ["start", "weekly", "recent", "weekly_report", "weekly_advice"]:
            if (message_text or "").lower() == "start":
                buttons = [
                    TelegramButton("recent", "Transaksi Terakhir").to_dict(),
                    TelegramButton("weekly", "Menu Mingguan").to_dict(),
                ]
                TelegramClient.send_message(sender, "Pilih aksi:")
                # Inline keyboard: not implemented here, just send text
            elif (message_text or "").lower() == "weekly":
                weekly_buttons = [
                    TelegramButton("weekly_report", "Laporan Mingguan").to_dict(),
                    TelegramButton("weekly_advice", "Rekomendasi Mingguan").to_dict(),
                ]
                TelegramClient.send_message(sender, "Pilih salah satu:")
            elif (message_text or "").lower() == "recent":
                TelegramClient.send_message(sender, "Fitur transaksi terbaru belum diimplementasi.")
            elif (message_text or "").lower() == "weekly_report":
                TelegramClient.send_message(sender, "Fitur laporan mingguan belum diimplementasi.")
            elif (message_text or "").lower() == "weekly_advice":
                TelegramClient.send_message(sender, "Fitur rekomendasi mingguan belum diimplementasi.")
            return {"status": "success", "message": "Perintah tombol diproses."}

        # 2. **Jika pesan merupakan transaksi**
        extraction_prompt = """
Extract transaction from text/image to JSON:
{
  "timestamp": "<ISO 8601 Asia/Jakarta>",
  "prompt_text": "<user input or OCR summary>", 
  "summary_text": "<transaction summary in Indonesian>",
  "amount": <number>,
  "type": "expense|income",
  "category": "food|grocery|transport|fuel|utility|health|entertainment|education|gift|salary|other"
}

Rules:
- Use current time if no date given
- For images: find largest Total amount 
- Expense: beli, bayar, isi bensin, etc
- Income: gaji, refund, transfer masuk, etc
- Categories: food (makan), grocery (minimarket), fuel (bensin), transport (gojek/grab), utility (listrik/air), etc
- Return only JSON, no markdown

Examples:
"beli nasi 15000" → {"timestamp":"2025-09-06T12:00:00+07:00","prompt_text":"beli nasi 15000","summary_text":"Beli nasi","amount":15000,"type":"expense","category":"food"}
"""
        
        # Kirim ke Gemini: jika ada gambar, kirim image_bytes, jika tidak kirim message_text
        if image_bytes:
            extraction_result = await gemini.parse_transaction(image_bytes, system_prompt=extraction_prompt, is_image=True)
        else:
            extraction_result = await gemini.parse_transaction(message_text, system_prompt=extraction_prompt)
        
        if extraction_result:
            await sheets.add_transaction(extraction_result, message_text or "image", formatted_time, wib_now)
            summary = extraction_result.get("summary_text", "Transaksi")
            amount = extraction_result.get("amount", 0)
            TelegramClient.send_message(sender, f"✅ Transaksi tercatat!\n{summary}\nJumlah: Rp{amount:,.0f}")
            return {
                "status": "success",
                "data": extraction_result
            }

        return {
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Failed to process message",
                "details": str(e),
                "example": "Beli nasi padang 15000 cash"
            }
        )

@app.get("/telegram/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logging.info(f"Received verification request: mode={mode}, token={token}, challenge={challenge}")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return int(challenge)
    return {"status": "failed"}, 403

@app.get("/")
def read_root():
    return {"message": "Telegram Finance Bot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)