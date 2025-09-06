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
        message_text = message_data.get("text", "")
        unix_time = message_data.get('date', '')
        unix_time = int(unix_time) if unix_time else int(datetime.now().timestamp())
        wib_now = datetime.fromtimestamp(unix_time).astimezone(pytz.timezone("Asia/Jakarta"))
        formatted_time = wib_now.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Pesan diterima dari {sender}: {message_text}")

        # Menentukan tombol yang akan dikirim
        # 1. **Jika pesan berisi perintah tombol**
        if message_text.lower() in ["start", "weekly", "recent", "weekly_report", "weekly_advice"]:
            if message_text.lower() == "start":
                buttons = [
                    TelegramButton("recent", "Transaksi Terakhir").to_dict(),
                    TelegramButton("weekly", "Menu Mingguan").to_dict(),
                ]
                TelegramClient.send_message(sender, "Pilih aksi:")
                # Inline keyboard: not implemented here, just send text
            elif message_text.lower() == "weekly":
                weekly_buttons = [
                    TelegramButton("weekly_report", "Laporan Mingguan").to_dict(),
                    TelegramButton("weekly_advice", "Rekomendasi Mingguan").to_dict(),
                ]
                TelegramClient.send_message(sender, "Pilih salah satu:")
            elif message_text.lower() == "recent":
                TelegramClient.send_message(sender, "Fitur transaksi terbaru belum diimplementasi.")
            elif message_text.lower() == "weekly_report":
                TelegramClient.send_message(sender, "Fitur laporan mingguan belum diimplementasi.")
            elif message_text.lower() == "weekly_advice":
                TelegramClient.send_message(sender, "Fitur rekomendasi mingguan belum diimplementasi.")
            return {"status": "success", "message": "Perintah tombol diproses."}

        # 2. **Jika pesan merupakan transaksi**
        transaction = await gemini.parse_transaction(message_text)
        if transaction:
            await sheets.add_transaction(transaction, message_text, formatted_time, wib_now)
            TelegramClient.send_message(sender, f"Transaksi tercatat!\n{transaction}")
            return {
                "status": "success",
                "data": transaction.model_dump()
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