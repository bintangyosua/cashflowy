import json
from typing import Dict, Any

class MessageFormatterService:
    """Service untuk memformat pesan response"""
    
    def format_financial_analysis(self, financial_data: Dict[str, Any], user_name: str, 
                                 sheet_saved: bool, is_image: bool = False, caption: str = None) -> str:
        """Format pesan analisis keuangan"""
        
        # Pilih emoji dan title berdasarkan jenis input
        if is_image:
            title = "🖼️💰 *Analisis Gambar Keuangan*"
        else:
            title = "📊 *Analisis Keuangan*"
        
        # Status penyimpanan Google Sheets
        sheet_status = "✅ Disimpan ke Google Sheets" if sheet_saved else "⚠️ Gagal menyimpan ke Google Sheets"
        
        # Buat pesan utama
        reply_text = f"{title}\n\n"
        reply_text += f"👤 *User:* {user_name}\n"
        reply_text += f"⏰ *Waktu:* {financial_data.get('timestamp', 'N/A')}\n"
        
        # Tambahkan caption jika ada (untuk gambar)
        if caption:
            reply_text += f"📝 *Caption:* {caption}\n"
        
        # Jika bukan gambar, tampilkan teks input
        if not is_image:
            reply_text += f"📝 *Teks:* {financial_data.get('prompt_text', 'N/A')}\n"
        
        # Informasi keuangan
        reply_text += f"🏷️ *Kategori:* {financial_data.get('category', 'N/A')}\n"
        reply_text += f"💵 *Jumlah:* Rp {financial_data.get('amount', 0):,.0f}\n"
        reply_text += f"💳 *Metode:* {financial_data.get('payment_method', 'N/A')}\n"
        reply_text += f"📊 *Tipe:* {financial_data.get('type', 'N/A')}\n"
        reply_text += f"📋 *Ringkasan:* {financial_data.get('summary', 'N/A')}\n"
        reply_text += f"💾 *Status:* {sheet_status}\n"
        
        # Tambahkan daftar item jika ada
        if financial_data.get('items'):
            reply_text += f"\n🛒 *Item yang dibeli:*\n"
            for item in financial_data['items']:
                reply_text += f"• {item.get('name', 'N/A')} x{item.get('quantity', 1)} - Rp {item.get('price', 0):,.0f}\n"
        
        return reply_text
    
    def format_error_message(self, error: str) -> str:
        """Format pesan error"""
        return f"❌ *Error*\n\n{error}"
    
    def format_json_response(self, financial_data: Dict[str, Any]) -> str:
        """Format JSON response dari Gemini AI"""
        return f"🔧 *JSON Response dari Gemini AI:*\n\n```json\n{json.dumps(financial_data, indent=2, ensure_ascii=False)}\n```"
    
    def format_unsupported_message(self, user_name: str) -> str:
        """Format pesan untuk jenis pesan yang tidak didukung"""
        reply_text = f"ℹ️ *Pesan Tidak Didukung*\n\nHalo {user_name}!\n"
        reply_text += "Saat ini bot hanya mendukung:\n"
        reply_text += "• 🗨️ Pesan teks tentang transaksi keuangan\n"
        reply_text += "• 🖼️ Gambar struk/nota/transaksi\n"
        reply_text += "\nBot akan menganalisis dan mengekstrak informasi keuangan dari pesan Anda."
        return reply_text
    
    def format_processing_message(self, is_image: bool = False) -> str:
        """Format pesan sedang memproses"""
        if is_image:
            return "🤖 Sedang menganalisis gambar Anda..."
        else:
            return "🤖 Sedang menganalisis pesan Anda..."
