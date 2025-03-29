import asyncio
from datetime import datetime
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import pytz
from schemas.models import Transaction
from services.gemini_service import GeminiService
from services.sheets_service import SheetsService
from services.whatsapp_service import WhatsAppService, WhatsAppClient
from config import settings
from dialog.whatsapp_button import WhatsappButton

app = FastAPI()
logger = logging.getLogger(__name__)
sheets = SheetsService()
gemini = GeminiService()

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        payload = await request.json()
        
        # Ambil data pesan dari payload
        changes = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
        
        if "messages" in changes:
            message_data = changes["messages"][0]
            sender = message_data.get("from", "")
            message_text = message_data.get("text", {}).get("body", "")
            unix_time = message_data.get('timestamp', '')
            unix_time = int(unix_time)
            
            wib_now = datetime.fromtimestamp(unix_time).astimezone(pytz.timezone("Asia/Jakarta"))
            formatted_time = wib_now.strftime("%Y-%m-%d %H:%M:%S")
           
            # Jika pesan dari tombol interaktif
            interactive_payload = message_data.get("interactive", {}).get("button_reply", {})
            if interactive_payload:
                message_text = interactive_payload.get("id", message_text)
            
            logger.info(f"Pesan diterima dari {sender}: {message_text}")

            # Menentukan tombol yang akan dikirim
            # ==============================
            # 1. **Jika pesan berisi perintah tombol**
            # ==============================
            if message_text.lower() in ["start", "weekly", "recent", "weekly_report", "weekly_advice"]:
                if message_text.lower() == "start":
                    buttons = [
                        WhatsappButton("recent", "Transaksi Terakhir"),
                        WhatsappButton("weekly", "Menu Mingguan"),
                    ]
                    WhatsAppService.send_action_buttons(sender, "Pilih aksi:", buttons)

                elif message_text.lower() == "weekly":
                    weekly_buttons = [
                        WhatsappButton("weekly_report", "Laporan Mingguan"),
                        WhatsappButton("weekly_advice", "Rekomendasi Mingguan"),
                    ]
                    WhatsAppService.send_action_buttons(sender, "Pilih salah satu:", weekly_buttons)

                elif message_text.lower() == "recent":
                    recent_transactions = WhatsAppService.get_recent_transactions(sheets.sheet)
                    WhatsAppClient.send_text_message(sender, recent_transactions)

                elif message_text.lower() == "weekly_report":
                    _, report = WhatsAppService.get_weekly_report(sheet=sheets.sheet)
                    WhatsAppClient.send_text_message(sender, report)

                elif message_text.lower() == "weekly_advice":
                    csv_text, _ = WhatsAppService.get_weekly_report(sheet=sheets.sheet)
                    weekly_advice = gemini.weekly_recommendation(csv_text)
                    WhatsAppClient.send_text_message(sender, weekly_advice)

                return {"status": "success", "message": "Perintah tombol diproses."}

            # ==============================
            # 2. **Jika pesan merupakan transaksi**
            # ==============================
            transaction = await gemini.parse_transaction(message_text)
            if transaction:
                await sheets.add_transaction(transaction, message_text, formatted_time, wib_now)
                WhatsAppService.send_transaction_confirmation(sender, transaction, formatted_time)

                return {
                    "status": "success",
                    "data": transaction.model_dump()
                }
                
        elif "statuses" in changes:
            status_data = changes["statuses"][0]
            message_id = status_data.get("id", "")
            status = status_data.get("status", "")
            timestamp = status_data.get("timestamp", "")
            
            logger.info(f"Status pesan {message_id}: {status} pada {timestamp}")
            
        else:
            WhatsAppClient.send_text_message(sender, "Payload tidak dikenali")
            logger.warning("Payload tidak dikenali: %s", payload)

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

@app.get("/whatsapp/webhook")
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
    return {"message": "WhatsApp Finance Bot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)