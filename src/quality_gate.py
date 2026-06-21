# -*- coding: utf-8 -*-
"""
Quality gate and normalization for LinkedIn ESG data.

Applies after extraction to clean, normalize, and enrich the DataFrame.
"""
import re
import pandas as pd
import logging
from typing import Callable

from .config import COMPANY_MAPPINGS

logger = logging.getLogger(__name__)


def sanitize_text(s: str | None) -> str:
    """Remove non-breaking spaces, zero-width spaces, collapse whitespace."""
    if s is None:
        return ""
    s = s.replace("\u00a0", " ").replace("\u200b", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def norm_company(s: str) -> str:
    """Normalize company name using configured mappings."""
    if not s:
        return "unknown"
    t = sanitize_text(str(s))
    t_low = t.lower()
    for key, val in COMPANY_MAPPINGS.items():
        if key in t_low:
            return val
    return t.title()


def quality_gate_and_normalize(
    df: pd.DataFrame,
    logcb: Callable = print,
) -> pd.DataFrame:
    """Apply quality gate and normalization to a cleaned DataFrame.

    Steps:
    1. Timestamp coercion + fallback
    2. Text sanitization
    3. Word count & media flag
    4. Month extraction
    5. Company name normalization
    6. Document ID generation
    7. Engagement NaN -> 0
    """
    if df is None or df.empty:
        logcb("No data to process.")
        return df

    df = df.copy()

    # ── Timestamp ──
    df["posted_at_utc"] = pd.to_datetime(df["posted_at_utc"], errors="coerce", utc=True)

    # Per-row fallback: if posted_at is NaT, use crawl_timestamp_utc date
    if "crawl_timestamp_utc" in df.columns:
        crawl_dt = pd.to_datetime(df["crawl_timestamp_utc"], errors="coerce", utc=True)
        null_mask = df["posted_at_utc"].isna()
        if null_mask.any():
            df.loc[null_mask, "posted_at_utc"] = crawl_dt[null_mask]
            logcb(f"Timestamp fallback applied for {null_mask.sum()} rows (crawl_timestamp_utc)")

    # ── Text sanitization ──
    df["text_raw"] = df["text_raw"].map(sanitize_text)
    df["text_clean"] = df["text_clean"].map(sanitize_text)

    # ── Derived fields ──
    df["word_count"] = df["text_raw"].map(lambda s: len(s.split()) if s else 0)
    df["has_media"] = df["media_urls"].map(lambda x: "Y" if isinstance(x, str) and x.strip() else "N")
    df["month"] = df["posted_at_utc"].dt.strftime("%Y-%m")

    # ── Company normalization ──
    df["company_norm"] = df["company"].map(norm_company)

    # ── Document ID ──
    def make_doc_id(row):
        dt = row["posted_at_utc"].strftime("%Y%m%d") if pd.notna(row["posted_at_utc"]) else "NA"
        return f"{row['company_norm']}|{row['post_id']}|{dt}"

    df["document_id"] = df.apply(make_doc_id, axis=1)

    # ── Engagement NaNs -> 0 ──
    for col in ["reactions_count", "comments_count", "reshares_count"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    return df
