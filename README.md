# LinkedIn ESG Sentiment Analysis

**Analisis sentimen postingan LinkedIn terhadap dampak *Environmental, Social, and Governance* (ESG) pada perusahaan tambang di Indonesia.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://img.shields.io/badge/DOI-pending-blue)]()

## 📋 Tentang Proyek

Penelitian ini menggunakan pendekatan **Mixed Methods** (QUAN→QUAL) untuk menganalisis peran sentimen media sosial LinkedIn terhadap dampak ESG pada lima perusahaan tambang terbesar di Indonesia:

- **Freeport Indonesia**
- **Vale Indonesia**
- **Adaro Energy**
- **Bukit Asam**
- **ANTAM**

### Metode
1. **Fase Kuantitatif:** Lexicon-based Sentiment Analysis (TextBlob + InSet Indonesia)
2. **Fase Kualitatif:** Reflexive Thematic Analysis (Braun & Clarke, 2006)
3. **Triangulasi:** Perbandingan dengan laporan ESG resmi perusahaan

## 🚀 Instalasi

```bash
git clone https://github.com/HoneyBee66661/linkedin-esg-sentiment.git
cd linkedin-esg-sentiment
pip install -e .
playwright install chromium     # Untuk scraper otomatis
```

## 💻 Penggunaan CLI

### Ekstrak postingan dari file HTML
```bash
linkedin-esg extract data/raw/vale_1.html --out data/
```

### Ekstrak dari folder (banyak file HTML)
```bash
linkedin-esg extract data/raw/ --out data/
```

### Terapkan quality gate ke CSV
```bash
linkedin-esg process data/clean/20251021-101729_offline_clean.csv --out data/processed/
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📁 Struktur Proyek

```
linkedin-esg-sentiment/
├── data/               # Data mentah & processed
│   ├── raw/            # HTML files + raw JSON
│   ├── processed/      # Clean CSV
│   └── external/       # Laporan ESG sekunder
├── src/                # Kode inti
│   ├── extract.py      # Ekstraksi HTML → dict posts
│   ├── quality_gate.py # Normalisasi, dedupe, validasi
│   ├── config.py       # Konstanta: keywords, mappings
│   ├── io_utils.py     # File I/O helpers
│   └── cli.py          # CLI entry point
├── tests/              # Test suite (36 test cases)
├── notebooks/          # Jupyter notebooks
├── paper/              # Draf artikel ilmiah
│   ├── manuscript.md   # Naskah artikel (Bahasa Indonesia)
│   └── references.bib  # Daftar pustaka BibTeX
└── results/            # Output analisis
```

## 🤖 Scraping LinkedIn Otomatis (Playwright Stealth)

Gunakan **Playwright Stealth** untuk mengambil postingan 5 perusahaan secara otomatis.

### Persiapan: Simpan Cookie LinkedIn

Pertama kali, jalankan dengan browser visible untuk login:
```bash
python -m src.linkedin_scraper --email your_email@example.com --password your_password
```
Browser akan terbuka, login otomatis terjadi, cookie disimpan ke `data/linkedin_cookies.json`.
Login hanya perlu sekali — selanjutnya cookie akan dipakai ulang.

### Scraping Semua Perusahaan
```bash
# Semua 5 perusahaan (headless — tanpa jendela browser)
python -m src.linkedin_scraper --all --target 200 --headless
```

### Scraping Perusahaan Tertentu
```bash
python -m src.linkedin_scraper --companies vale,freeport --target 300
```

### Parameter
| Argumen | Default | Deskripsi |
|---------|---------|-----------|
| `--companies`/`-c` | `vale` | Slugs: vale, freeport, adaro, bukit-asam, antam |
| `--all` | — | Scrape semua 5 perusahaan |
| `--target` | 200 | Target jumlah postingan per perusahaan |
| `--headless` | false | Mode tanpa jendela browser (setelah cookie siap) |
| `--email` | — | Email LinkedIn (opsional, interactive jika tidak ada) |
| `--output`/`-o` | `data/raw/linkedin_pages` | Folder output HTML |

### ⚠️ Catatan Penting
1. **Cookie dulu:** Jalankan sekali tanpa `--headless` untuk login
2. **Rate limiting:** Ada jeda 5 detik antar perusahaan
3. **Scroll smooth:** Scraper scroll naik-turun agar terlihat seperti manusia
4. **Range tanggal:** Scraper scroll terus sampai target tercapai atau tidak ada konten baru

Setelah scraping selesai, ekstrak data:
```bash
linkedin-esg extract data/raw/linkedin_pages/ --out data/
linkedin-esg process data/clean/*_offline_clean.csv --out data/processed/
```

## 📊 Cara Mengumpulkan Data LinkedIn Manual (Alternatif)
Jika scraping otomatis tidak berhasil (captcha/login block), gunakan metode manual:

1. Buka halaman perusahaan di LinkedIn: `https://www.linkedin.com/company/<slug>/posts/?feedView=all`
2. Scroll untuk memuat postingan yang diinginkan
3. File → Save Page As... → Webpage, Complete (.html + folder)
4. Simpan ke `data/raw/`
5. Jalankan: `linkedin-esg extract data/raw/ --out data/`

## 📄 Publikasi

Draf artikel ilmiah tersedia di [`paper/manuscript.md`](paper/manuscript.md).

## 📜 Lisensi

MIT License — lihat file [LICENSE](LICENSE).

## 📝 Sitasi

Jika menggunakan repositori ini dalam penelitian, silakan sitasi:

```
Subakti, J. (2026). LinkedIn ESG Sentiment Analysis. GitHub.
https://github.com/HoneyBee66661/linkedin-esg-sentiment
```
