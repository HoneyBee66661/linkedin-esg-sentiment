# -*- coding: utf-8 -*-
"""
Configuration constants for LinkedIn ESG Sentiment Analysis.
"""
import re

# ── Company Name Mappings ────────────────────────────────────────────
# Maps various raw title variants to normalized company names
COMPANY_MAPPINGS = {
    "pt freeport indonesia": "Freeport Indonesia",
    "freeport indonesia": "Freeport Indonesia",
    "freeport": "Freeport Indonesia",
    "pt vale indonesia tbk": "Vale Indonesia",
    "vale indonesia": "Vale Indonesia",
    "pt vale": "Vale Indonesia",
    "vale": "Vale Indonesia",
    "pt antam": "ANTAM",
    "antam": "ANTAM",
    "pt timah": "Timah",
    "timah": "Timah",
    "pt bukit asam": "Bukit Asam",
    "bukit asam": "Bukit Asam",
    "adaro energy": "Adaro Energy",
    "pt adaro": "Adaro Energy",
    "adaro": "Adaro Energy",
}

TARGET_COMPANIES = [
    "Freeport Indonesia",
    "Vale Indonesia",
    "Adaro Energy",
    "Bukit Asam",
    "ANTAM",
]

# ── Hiring Filter Keywords ───────────────────────────────────────────
# Combined into a single compiled pattern to avoid duplication
EXCLUDE_JOB_PATTERNS = [
    r"\bhiring\b",
    r"\bvacanc(?:y|ies)\b",
    r"\blowongan\b",
    r"\brekrut\w*\b",
    r"\b(?:membuka|buka|open)\s+(?:lowongan|karir|posisi|position)\b",
    r"\bkarir\s+(?:baru|di|bersama|kami)\b",
    r"\bcareer\s+opportunit(?:y|ies)\b",
    r"\bjoin\s+our\s+team\b",
    r"\bjob\s+opening\b",
    r"\bwe\s+are\s+hiring\b",
    r"\bwe'?re\s+hiring\b",
    r"\bnow\s+hiring\b",
    r"\bis\s+hiring\b",
]

EXCLUDE_JOB_REGEX = re.compile("|".join(EXCLUDE_JOB_PATTERNS), re.IGNORECASE)


def looks_like_hiring(text: str | None) -> bool:
    """Returns True if text appears to be a hiring/job post."""
    if not text:
        return False
    return bool(EXCLUDE_JOB_REGEX.search(text))


# ── ESG Keywords for Categorization ──────────────────────────────────
ESG_KEYWORDS = {
    "E": [
        "lingkungan", "environment", "carbon", "emisi", "emission",
        "climate", "iklim", "energi", "energy", "renewable",
        "terbarukan", "reklamasi", "reclamation", "limbah", "waste",
        "polusi", "pollution", "deforestasi", "deforestation",
        "keanekaragaman hayati", "biodiversity", "green", "hijau",
        "net zero", "decarbonization", "dekarbonisasi",
    ],
    "S": [
        "sosial", "social", "community", "masyarakat", "csr",
        "pekerja", "worker", "employee", "karyawan", "k3",
        "safety", "keselamatan", "health", "kesehatan",
        "hak asasi", "human rights", "child labor", "pekerja anak",
        "diversity", "inklusif", "inclusion", "gendered",
        "pendidikan", "education", "pemberdayaan", "empowerment",
    ],
    "G": [
        "governance", "tata kelola", "transparansi", "transparency",
        "anti korupsi", "anticorruption", "fraud",
        "audit", "compliance", "kepatuhan",
        "dewan direksi", "board of directors", "executive",
        "whistleblower", "etika", "ethics",
        "pemegang saham", "shareholder", "stakeholder",
    ],
}


def categorize_esg(text: str) -> list[str]:
    """Returns list of ESG pillars (E, S, G) found in text."""
    if not text:
        return []
    t = text.lower()
    found = []
    for pillar, keywords in ESG_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                found.append(pillar)
                break
    return found


# ── HTML Parsing Selectors ──────────────────────────────────────────
# CSS selectors for finding posts in saved LinkedIn HTML
POST_SELECTORS = [
    'article[data-urn^="urn:li:activity:"]',
    'div[data-urn^="urn:li:activity:"]',
]

TEXT_SELECTORS = [
    "div.update-components-text",
    "div.feed-shared-update-v2__description",
    "div.break-words",
    "span[dir]",
]

REACTIONS_SELECTORS = [
    '[data-test-reactions-count]',
    'span.social-details-social-counts__reactions-count',
]
