# 🕷️ Bx-Spider - Website Builder Detector and Crawler
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

Bx-Spider adalah tool crawling website yang dapat mendeteksi platform website builder seperti Wix dan WordPress dengan analisis komprehensif terhadap status website.

<img src="/moz-pro-without-api-key.png" width="600" alt="Bx-Spider-Website-Builder-Detector-and-Crawler">

## ✨ Fitur

- 🎯 **Deteksi Platform**: Mendeteksi website Wix dan WordPress
- 🛡️ **Analisis Status**: Mengkategorikan website berdasarkan status (Protected, Error, dll)
- ⚡ **Async Crawling**: Pemindaian cepat dengan concurrent requests
- 📊 **Progress Bar**: Real-time progress dengan statistik
- 🎨 **Colorful Output**: Interface terminal yang menarik
- 💾 **Multiple Output**: Hasil tersimpan dalam file terpisah berdasarkan kategori
- 🔄 **Random User Agent**: Rotasi user agent untuk menghindari blocking
- 📈 **Comprehensive Reporting**: Laporan detail dengan breakdown status

## 📋 Requirements

- Python 3.7+
- Dependencies (lihat requirements.txt)

## 🚀 Instalasi

1. Clone atau download repository ini
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Buat file `user-agents.txt` (opsional) berisi daftar user agents:

```txt
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
```

## 📖 Penggunaan

### Command Line Options

```bash
python bx_spider.py [OPTIONS]
```

**Options:**
- `-u, --urls`: URL yang akan dipindai
- `-f, --file`: File berisi daftar URL (satu per baris)
- `-o, --output`: File output untuk semua hasil
- `-c, --concurrent`: Jumlah request bersamaan (default: 10)
- `-t, --timeout`: Timeout request dalam detik (default: 10)

### Contoh Penggunaan

**Scan single URL:**
```bash
python bx_spider.py -u example.com
```

**Scan multiple URLs:**
```bash
python bx_spider.py -u example.com google.com facebook.com
```

**Scan dari file:**
```bash
python bx_spider.py -f urls.txt
```
```bash
python bx_spider.py -f urls.txt -t 300
```

**Scan dengan custom settings:**
```bash
python bx_spider.py -f urls.txt -c 20 -t 15 -o results.txt
```

### Format File Input

Buat file `urls.txt` dengan format:
```txt
example.com
https://google.com
http://facebook.com
# Komentar diabaikan
another-site.com
```

## 📊 Output dan Hasil

### Kategorisasi Website

Bx-Spider mengkategorikan website ke dalam beberapa kategori:

1. **🎯 Wix Sites**: Website yang menggunakan platform Wix
2. **🎯 WordPress Sites**: Website yang menggunakan WordPress
3. **🛡️ Protected Sites**: Website yang membatasi akses (status 202, 403, 401, 429 | cek manual kembali)
4. **❌ Error Sites**: Website dengan error (404, 5xx, network errors)
5. **🔍 Other Platform Sites**: Website dengan platform lain

### File Output

Jika tidak menggunakan `-o`, hasil akan disimpan dalam file terpisah:

- `wix_sites.txt` - Daftar website Wix
- `wordpress.txt` - Daftar website WordPress  
- `protected_sites.txt` - Website yang diproteksi/dibatasi
- `error_sites.txt` - Website dengan error
- `no_template.txt` - Website platform lain

### Contoh Output Terminal

```
🕷️  HASIL PEMINDAIAN BX-SPIDER COMPREHENSIVE
============================================================
📊 Total URL yang dipindai: 100
🎯 Situs Wix ditemukan: 15
🎯 Situs WordPress ditemukan: 25
🛡️ Situs Protected: 10
❌ Situs Error: 20
🔍 Situs Platform Lain: 30

🛡️  PROTECTED SITES BREAKDOWN:
  ├─ 202: 5 sites (Accepted/Maintenance)
  ├─ 403: 3 sites (Forbidden/Blocked)
  ├─ 429: 2 sites (Rate Limited)

❌ ERROR SITES BREAKDOWN:
  ├─ 0: 10 sites (Network/DNS Error)
  ├─ 404: 8 sites (Not Found)
  ├─ 500: 2 sites (Internal Server Error)
```

## 🔧 Konfigurasi

### User Agents

Buat file `user-agents.txt` untuk rotasi user agent:
- Satu user agent per baris
- Baris yang dimulai dengan `#` diabaikan
- Jika file tidak ada, akan menggunakan default user agent

### Performance Tuning

- **Concurrent Requests**: Sesuaikan `-c` berdasarkan bandwidth dan target server
- **Timeout**: Sesuaikan `-t` untuk website yang lambat
- **Recommended**: `-c 10-20` untuk penggunaan normal

## 🛠️ Troubleshooting

### Error Umum

1. **"File user-agents.txt tidak ditemukan"**
   - Buat file user-agents.txt atau abaikan pesan ini (akan menggunakan default)

2. **"Network error" atau "DNS error"**
   - Periksa koneksi internet
   - URL mungkin tidak valid atau server down

3. **Rate limiting (429 errors)**
   - Kurangi concurrent requests dengan `-c`
   - Tambah delay atau gunakan proxy

4. **Timeout errors**
   - Tingkatkan timeout dengan `-t`
   - Periksa koneksi internet

### Tips Optimasi

- Gunakan concurrent requests sesuai kebutuhan (jangan terlalu tinggi)
- Untuk scan besar, gunakan timeout yang cukup (300 = 5 menit)


## 📝 Status Code Reference

| Status | Kategori | Deskripsi |
|--------|----------|-----------|
| 200 | Success | Website normal, dilanjutkan analisis platform |
| 202 | Protected | Accepted/Maintenance mode/redirect |
| 401 | Protected | Authentication required |
| 403 | Protected | Forbidden/Blocked |
| 404 | Error | Not found |
| 429 | Protected | Rate limited |
| 5xx | Error | Server errors |
| 0 | Error | Network/DNS errors |


## 🔗 Links

- **Repository**: [GitHub Repository URL]
- **Issues**: [GitHub Issues URL]
- **Documentation**: [Documentation URL]

## 📞 Support

Jika Anda mengalami masalah atau memiliki pertanyaan:

1. Periksa bagian Troubleshooting di atas
2. Buat issue di GitHub repository


---

**⚠️ Disclaimer**: Tool ini dibuat untuk tujuan edukasi dan testing. Pastikan Anda memiliki izin untuk melakukan crawling pada website target. Gunakan dengan bijak dan patuhi robots.txt serta terms of service website yang dipindai.

**Made with ❤️ by Dzone**
