# Telegram AI Transaction Bot

An AI-powered Telegram bot that records transactions from text messages and receipt images with detailed item extraction.

## 🚀 Features

- Receives and processes transactions from Telegram messages and images
- **Multi-AI Support**: Choose between ChatGPT or Gemini AI for transaction processing
- AI-powered receipt OCR with item detail extraction
- Google Sheets integration for transaction storage (latest entries appear at top)
- Support for multiple items per transaction (e.g., grocery receipts)
- RESTful API endpoints for AI provider configuration

## 📦 Technologies

- **Python** (FastAPI)
- **Telegram Bot API**
- **Google Sheets API**
- **ChatGPT/OpenAI API** (Primary AI provider)
- **Gemini AI** (Alternative AI provider)

## 🔧 Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/your-username/telegram-ai-bot.git
   cd telegram-ai-bot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```sh
   cp .env.example .env
   # Edit .env with your configuration:
   # - TELEGRAM_BOT_TOKEN: Your Telegram bot token
   # - OPENAI_API_KEY: Your OpenAI API key (for ChatGPT)
   # - GEMINI_API_KEY: Your Google Gemini API key (optional)
   # - AI_PROVIDER: Set to "chatgpt" or "gemini"
   ```

## 🤖 AI Provider Configuration

This bot supports two AI providers:

### ChatGPT (Default, Recommended)

- Better accuracy for financial data extraction
- Excellent image processing capabilities
- More reliable JSON response formatting

### Gemini AI (Alternative)

- Free tier available
- Good for basic text processing
- Backup option when OpenAI is unavailable

You can switch between providers using the API endpoints or by updating the `AI_PROVIDER` environment variable.

````

## 🚀 Running the Bot

Start the server with FastAPI:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
````

## 📌 Usage

The bot will automatically respond to Telegram messages:

- **Send text** → AI extracts transaction details and saves to Google Sheets
- **Send image** → OCR processes receipt with item details
- **Latest transactions appear at the top** of your Google Sheets

### Transaction Processing

When you send transaction data (text or image), the bot will:

1. Process with selected AI provider (ChatGPT or Gemini)
2. Extract transaction details (amount, category, payment method, etc.)
3. Save to Google Sheets with newest entries at the top
4. Send confirmation message with extracted details

Example response for a grocery receipt:

```
✅ Transaksi tercatat!
Belanja groceries di Alfamart
Jumlah: Rp87,900

Detail items:
• Indomie Goreng x5 @Rp3,000
• Teh Botol x2 @Rp4,500
• Snack x3 @Rp2,500
```

## 🛠 API Endpoints

| Method | Endpoint              | Description                           |
| ------ | --------------------- | ------------------------------------- |
| `GET`  | `/`                   | Home Page                             |
| `POST` | `/webhook`            | Receives webhooks from Telegram       |
| `GET`  | `/health`             | Health check & service status         |
| `GET`  | `/ai-provider`        | Get current AI provider               |
| `POST` | `/ai-provider`        | Set AI provider (chatgpt/gemini)      |
| `POST` | `/test-chatgpt`       | Test ChatGPT processing (development) |
| `POST` | `/test-gemini`        | Test Gemini processing (development)  |
| `POST` | `/test-google-sheets` | Test Google Sheets connection         |

### Example: Switch to ChatGPT

```bash
curl -X POST "http://localhost:8000/ai-provider" \
     -H "Content-Type: application/json" \
     -d '{"provider": "chatgpt"}'
```

### Example: Check current AI provider

```bash
curl -X GET "http://localhost:8000/ai-provider"
```

## 👨‍💻 Contributing

Pull requests are welcome! Please open an issue first if you want to add a new feature.

## 📜 License

MIT License. Feel free to use and modify it as needed!
