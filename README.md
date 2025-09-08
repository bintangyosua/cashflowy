# Telegram AI Transaction Bot

An AI-powered Telegram bot that records transactions from text messages and receipt images with detailed item extraction.

## 🚀 Features

- Receives and processes transactions from Telegram messages and images
- AI-powered receipt OCR with item detail extraction
- Google Sheets integration for transaction storage
- Google Drive integration for receipt image storage
- Support for multiple items per transaction (e.g., grocery receipts)
- Interactive buttons for navigation and reports

## 📦 Technologies

- **Python** (FastAPI)
- **Telegram Bot API**
- **Google Sheets API**
- **Google Drive API**
- **Gemini AI** (for transaction parsing and OCR)

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
   # Edit .env with your Telegram Bot Token, Google credentials, etc.
   ```

## 🛠️ Google Drive Setup

To enable image upload functionality:

1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder for storing receipt images
3. Right-click the folder → Share → Get link
4. Copy the folder ID from the URL (e.g., `1abcd1234efgh5678ijkl`)
5. Update `services/sheets_service.py` line 28:
   ```python
   'parents': ['your_folder_id_here']  # Replace with your folder ID
   ```

## 🚀 Running the Bot

Start the server with FastAPI:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📌 Usage

The bot will automatically respond to Telegram messages:

- **"start"** → Displays "Recent Transactions" and "Weekly Menu" buttons
- **"recent"** → Shows the latest transactions
- **"weekly"** → Displays weekly report options
- **Send text** → AI extracts transaction details
- **Send image** → OCR processes receipt with item details + uploads image

## 📊 Receipt Processing

When you send a receipt image, the bot will:

1. Extract all items with quantities and prices
2. Calculate the total amount from Grand Total
3. Store item details in the sheet
4. Upload the receipt image to Google Drive
5. Save the image URL in the transaction record

Example response for a grocery receipt:

```
✅ Transaksi tercatat!
Belanja groceries di Alfamart
Jumlah: Rp87,900

Detail items:
• Indomie Goreng x5 @Rp3,000
• Teh Botol x2 @Rp4,500
• Snack x3 @Rp2,500

📷 Gambar tersimpan
```

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
