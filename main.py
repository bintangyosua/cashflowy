import asyncio
from datetime import datetime
import logging
from fastapi import FastAPI, Request, HTTPException
import pytz
from schemas.models import Transaction
from services.gemini_service import GeminiService
from services.sheets_service import SheetsService
from services.whatsapp_service import WhatsAppService
from config import settings

app = FastAPI()
logger = logging.getLogger(__name__)
sheets = SheetsService()
gemini = GeminiService()

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        payload = await request.json()
        
        # Timezone WIB
        wib_tz = pytz.timezone("Asia/Jakarta")
        wib_now = datetime.now(wib_tz)
        formatted_time = wib_now.strftime("%Y-%m-%d %H:%M:%S")

        # 🔥 Fix loop untuk ekstrak pesan
        messages = payload.get("messages", [])  # Langsung ambil dari root payload
        if not messages:
            raise ValueError("Payload tidak mengandung pesan yang valid.")

        message_data = messages[0]  # Ambil pesan pertama
        message = message_data.get("text", {}).get("body", "")
        sender = message_data.get("from", "")

        if not message:
            raise ValueError("Tidak ada teks dalam pesan WhatsApp.")

        # Proses transaksi
        transaction = await gemini.parse_transaction(message)
        await sheets.add_transaction(transaction, message, formatted_time, wib_now)
        
        WhatsAppService.async_send_message(
            sender, WhatsAppService.format_response(transaction, formatted_time)
        )
        
        return {
            "status": "success",
            "data": transaction.model_dump()
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