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

## 📊 Cara Mengumpulkan Data LinkedIn Baru

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
