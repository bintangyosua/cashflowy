import asyncio
from datetime import datetime
import logging
from fastapi import FastAPI, Request, HTTPException
import pytz
from services.gemini_service import GeminiService
from services.sheets_service import SheetsService
from services.whatsapp_service import WhatsAppService
from config import settings

app = FastAPI()
sheets = SheetsService()
gemini = GeminiService()

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        payload = await request.json()
        
        # Handle timezone conversion
        utc_now = datetime.now(pytz.utc)
        wib_tz = pytz.timezone("Asia/Jakarta")
        wib_now = utc_now.astimezone(wib_tz)
        formatted_time = wib_now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract message
        message = ''
        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                if 'messages' in change.get('value', {}):
                    message = change['value']['messages'][0]['text']['body']
                    break
            if message:
                break
                
        if not message:
            raise ValueError("No valid message found in payload")
        
        # Process transaction
        transaction = await gemini.parse_transaction(message)
        
        # Send WhatsApp message and WAIT for it to complete
        await WhatsAppService.send_whatsapp_message(
            settings.WHATSAPP_PHONE_NUMBER_ID,
            WhatsAppService.format_response(transaction, timestamp=formatted_time)
        )

        # Save to Google Sheets
        await sheets.add_transaction(transaction, message, formatted_time, wib_now)
        
        return {
            "status": "success",
            "data": transaction.model_dump()
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
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