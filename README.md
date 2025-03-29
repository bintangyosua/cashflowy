# WhatsApp AI Transaction Bot

An AI-powered WhatsApp bot that records transactions from WhatsApp messages and provides interactive buttons for navigation.

## 🚀 Features

- Receives and processes transactions from WhatsApp messages.
- Provides interactive buttons to view recent transactions and weekly reports.
- Uses AI to convert transaction text into structured data.
- Integrates with Google Sheets for transaction storage.

## 📦 Technologies

- **Python** (FastAPI)
- **WhatsApp Business API**
- **Google Sheets API**
- **Gemini AI** (for transaction parsing)

## 🔧 Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/your-username/whatsapp-ai-bot.git
   cd whatsapp-ai-bot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```sh
   cp .env.example .env
   # Edit .env according to your WhatsApp API & Google Sheets configuration
   ```

## 🚀 Running the Bot

Start the server with FastAPI:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📌 Usage

The bot will automatically respond to WhatsApp messages:

- **"start"** → Displays "Recent Transactions" and "Weekly Menu" buttons.
- **"recent"** → Shows the latest transactions.
- **"weekly"** → Displays weekly report options.
- **Transaction text** → AI processes and records the transaction in Google Sheets.

## 🛠 API Endpoints

| Method | Endpoint   | Description                     |
| ------ | ---------- | ------------------------------- |
| `GET`  | `/`        | Home Page                       |
| `POST` | `/webhook` | Receives webhooks from WhatsApp |

## 👨‍💻 Contributing

Pull requests are welcome! Please open an issue first if you want to add a new feature.

## 📜 License

MIT License. Feel free to use and modify it as needed!
