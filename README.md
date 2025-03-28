# WhatsApp Financial Bot

WhatsApp Financial Bot is an AI-powered chatbot that helps users record and categorize their financial transactions directly from WhatsApp. It integrates FastAPI, Google Sheets API, and Google Gemini AI to process and store transaction data efficiently.

## Features

✅ **Automated Transaction Logging**: Saves WhatsApp messages containing financial transactions to Google Sheets.  
✅ **AI-Based Categorization**: Uses Google Gemini AI to classify transactions based on message content.  
✅ **Real-Time Responses**: Sends instant confirmations with categorized transaction details.  
✅ **WhatsApp Cloud API Integration**: Seamlessly connects to WhatsApp for message processing.  
✅ **Duplicate Entry Prevention**: Avoids storing duplicate transactions.

## How It Works

1. Users send transaction details via WhatsApp (e.g., _"beli pulsa Telkomsel 20000 pake e-wallet Dana"_).
2. The bot extracts the amount, payment method, and description.
3. Google Gemini AI categorizes the transaction (e.g., _"Isi Ulang; E-wallet; Pembelian pulsa Telkomsel senilai 20000 menggunakan Dana."_).
4. The transaction is stored in Google Sheets.
5. A confirmation message is sent back to the user.

## Tech Stack

- **FastAPI** - Backend framework for handling WhatsApp webhook events.
- **Google Sheets API** - Stores transaction records.
- **Google Gemini AI** - Provides AI-based categorization.
- **WhatsApp Cloud API** - Receives and processes WhatsApp messages.

## Installation

1.  Clone this repository:

    ```bash
    git clone https://github.com/yourusername/whatsapp-financial-bot.git
    cd whatsapp-financial-bot
    ```

2.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3.  Set up environment variables in a .env file:

    ```bash
    WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
    WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
    GEMINI_API_KEY=your_google_gemini_api_key
    ```

4.  Run the FastAPI server:

    ```bash
    uvicorn main:app --reload
    ```

5.  Set up the webhook URL in WhatsApp Cloud API.

## Usage

Once deployed, send financial transactions to your WhatsApp bot, and they will be logged and categorized automatically.

## License

This project is open-source and available under the MIT License.

Let me know if you need any modifications! 🚀
