# Google Sheets Setup

## Header Kolom yang Diperlukan

Pastikan Google Sheets Anda memiliki header kolom sebagai berikut di baris pertama:

| A         | B           | C        | D      | E              | F    | G       | H     | I         |
| --------- | ----------- | -------- | ------ | -------------- | ---- | ------- | ----- | --------- |
| Timestamp | Prompt Text | Category | Amount | Payment Method | Type | Summary | Items | Image URL |

### Penjelasan Kolom:

1. **Timestamp** - Waktu transaksi (format ISO 8601 Asia/Jakarta)
2. **Prompt Text** - Teks input user atau ringkasan OCR
3. **Category** - Kategori transaksi (food, grocery, transport, dll)
4. **Amount** - Jumlah uang (angka)
5. **Payment Method** - Metode pembayaran (cash, debit, credit, ewallet, transfer, other)
6. **Type** - Jenis transaksi (expense/income)
7. **Summary** - Ringkasan transaksi dalam bahasa Indonesia
8. **Image URL** - Link gambar di Google Drive (jika ada)

## Contoh Data:

```
2025-09-06T14:30:00+07:00 | beli groceries alfamart | grocery | 87900 | debit | expense | Belanja groceries di minimarket | Indomie Goreng x5 @3,000; Teh Botol x2 @4,500 | https://drive.google.com/file/d/abc123/view
```

## Setup Google Drive

1. Buat folder baru di Google Drive untuk menyimpan gambar receipt
2. Klik kanan folder → Share → Get shareable link
3. Copy folder ID dari URL (bagian setelah `/folders/`)
4. Ganti `your_folder_id_here` di file `services/sheets_service.py` dengan folder ID Anda

## Permissions

Pastikan service account Google Anda memiliki akses:

- Google Sheets API (untuk menulis data)
- Google Drive API (untuk upload gambar)
- Akses ke spreadsheet dan folder Google Drive yang dituju
