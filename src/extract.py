# -*- coding: utf-8 -*-
"""
Extract LinkedIn company posts from saved HTML pages.

Usage:
    python -m src.extract <html_file_or_folder> [--out DIR] [--company NAME]

The extractor relies on rendered DOM in the saved HTML (no network calls).
Uses stable markers like data-urn="urn:li:activity:..." to find posts.
"""
import os
import re
import hashlib
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional
import logging

from .config import (
    looks_like_hiring,
    COMPANY_MAPPINGS,
    POST_SELECTORS,
    TEXT_SELECTORS,
    REACTIONS_SELECTORS,
)
from .io_utils import save_json, save_csv, list_html_files

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────


def clean_company_name(raw: str) -> str:
    """Normalize a raw company name from page title."""
    if not raw:
        return "unknown"

    # Remove leading "(N)" prefix e.g. "(7) PT Vale Indonesia Tbk: Posts"
    cleaned = re.sub(r"^\(\d+\)\s*", "", raw).strip()
    # Remove trailing "Posts", ":", etc.
    cleaned = re.sub(r"\s*:\s*Posts?.*$", "", cleaned, flags=re.IGNORECASE).strip()

    # Try exact mapping
    cleaned_lower = cleaned.lower()
    for key, val in COMPANY_MAPPINGS.items():
        if key in cleaned_lower:
            return val

    # Fallback: title case first two words
    words = cleaned.split()
    if len(words) >= 2:
        return " ".join(words[:2]).title()
    return cleaned.title() if cleaned else "unknown"


def find_company_from_title(soup: BeautifulSoup) -> str:
    """Extract company name from the HTML <title> tag."""
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    return clean_company_name(title)


def int_or_none(s: str | None) -> int | None:
    """Extract integer from string, stripping non-digit characters."""
    if not s:
        return None
    try:
        return int(re.sub(r"[^0-9]", "", s) or 0)
    except (ValueError, TypeError):
        return None


def _make_dedupe_hash(company: str, posted_at: str | None, text_excerpt: str) -> str:
    """Create a stable deduplication hash."""
    key = f"{company}|{posted_at or 'NA'}|{text_excerpt[:200]}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


# ── Main Extraction ──────────────────────────────────────────────────


def extract_posts_from_html(
    html_path: str | Path,
    company_override: str | None = None,
) -> list[dict]:
    """Extract LinkedIn posts from a saved HTML page.

    Args:
        html_path: Path to the saved .html file.
        company_override: Optional company name override (if None, infer from title).

    Returns:
        List of post dictionaries.
    """
    html_path = str(html_path)
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")

    company_hint = company_override or find_company_from_title(soup)

    posts = []
    for selector in POST_SELECTORS:
        cards = soup.select(selector)
        if cards:
            break

    for card in cards:
        try:
            urn = card.get("data-urn") or ""
            if "urn:li:activity:" not in urn:
                continue
            activity_id = urn.split(":")[-1].strip()
            permalink = f"https://www.linkedin.com/feed/update/{urn}"

            # Timestamp
            t_el = card.select_one("time[datetime]")
            posted_at_iso = t_el.get("datetime") if t_el else None

            # Text
            text_raw = ""
            for sel in TEXT_SELECTORS:
                el = card.select_one(sel)
                if el:
                    txt = el.get_text(separator=" ", strip=True)
                    if txt and len(txt) > len(text_raw):
                        text_raw = txt

            hashtags = re.findall(r"#\w+", text_raw or "")

            # Engagement counts
            reactions_count = int_or_none(
                card.select_one(REACTIONS_SELECTORS[0]).get_text(" ", strip=True)
                if card.select_one(REACTIONS_SELECTORS[0])
                else None
            )

            comments_count = None
            reshares_count = None
            for b in card.select('button[aria-label], a[aria-label]'):
                label = (b.get("aria-label") or "").lower()
                if "comment" in label or "komentar" in label:
                    comments_count = int_or_none(b.get_text(" ", strip=True))
                if "repost" in label or "bagikan" in label or "reshare" in label:
                    reshares_count = int_or_none(b.get_text(" ", strip=True))

            # Media
            media_urls = []
            for m in card.select("img, video"):
                src = m.get("src")
                if src and not src.startswith("data:image"):
                    media_urls.append(src)

            now_iso = datetime.now(timezone.utc).isoformat()

            posts.append({
                "company": company_hint,
                "post_id": activity_id,
                "post_permalink": permalink,
                "posted_at_utc": posted_at_iso,
                "text_raw": text_raw or "",
                "hashtags": hashtags,
                "media_urls": media_urls,
                "external_links": [],
                "reactions_count": reactions_count,
                "comments_count": comments_count,
                "reshares_count": reshares_count,
                "evidence_snapshot_path": html_path,
                "crawl_timestamp_utc": now_iso,
            })
        except Exception:
            logger.debug(f"Skipped card in {html_path}", exc_info=True)
            continue

    return posts


def to_row(d: dict) -> dict:
    """Convert a post dict to a flat CSV row with dedupe hash."""
    import re

    text_clean = re.sub(r"https?://\S+", " ", d.get("text_raw") or "")
    text_clean = re.sub(r"\s+", " ", text_clean).strip().lower()

    posted_at = d.get("posted_at_utc")
    craw_at = d.get("crawl_timestamp_utc")

    sha = _make_dedupe_hash(
        d.get("company", ""),
        posted_at or craw_at,
        text_clean,
    )

    def _join_if_list(val):
        if isinstance(val, list):
            return ",".join(val)
        return val or ""

    return {
        "company": d.get("company"),
        "post_id": d.get("post_id"),
        "post_permalink": d.get("post_permalink"),
        "posted_at_utc": posted_at,
        "text_raw": d.get("text_raw") or "",
        "text_clean": text_clean,
        "hashtags": _join_if_list(d.get("hashtags", [])),
        "media_urls": _join_if_list(d.get("media_urls", [])),
        "external_links": _join_if_list(d.get("external_links", [])),
        "reactions_count": d.get("reactions_count"),
        "comments_count": d.get("comments_count"),
        "reshares_count": d.get("reshares_count"),
        "evidence_snapshot_path": d.get("evidence_snapshot_path"),
        "crawl_timestamp_utc": d.get("crawl_timestamp_utc"),
        "dedupe_hash": sha,
        "notes": "",
    }


def extract_pipeline(
    input_path: str | Path,
    output_dir: str | Path = "data",
    exclude_hiring: bool = True,
    company_override: str | None = None,
) -> dict:
    """Run full extraction pipeline: HTML -> raw JSON -> clean CSV info.

    Returns dict with keys: raw_path, clean_path, total_posts, companies
    """
    import pandas as pd

    input_path = Path(input_path)
    output_dir = Path(output_dir)

    # Find HTML files
    if input_path.is_dir():
        html_files = list_html_files(input_path)
    else:
        html_files = [input_path]

    if not html_files:
        logger.warning(f"No HTML files found in {input_path}")
        return {"raw_path": None, "clean_path": None, "total_posts": 0, "companies": []}

    # Extract from each file
    all_posts = []
    for hp in html_files:
        posts = extract_posts_from_html(hp, company_override=company_override)
        all_posts.extend(posts)
        logger.info(f"  {hp.name}: {len(posts)} posts")

    # Filter hiring
    if exclude_hiring:
        before = len(all_posts)
        all_posts = [p for p in all_posts if not looks_like_hiring(p.get("text_raw"))]
        logger.info(f"Hiring filter: {before - len(all_posts)} removed, {len(all_posts)} remain")

    # Timestamp
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    # Save raw JSON
    raw_path = output_dir / "raw" / f"{ts}_offline_raw.json"
    save_json(all_posts, raw_path)

    # Convert to rows and deduplicate
    rows = [to_row(p) for p in all_posts]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["posted_at_utc"] = pd.to_datetime(df["posted_at_utc"], errors="coerce", utc=True)
        df = (
            df.sort_values(["posted_at_utc", "company", "post_id"], na_position="last")
            .drop_duplicates(subset=["dedupe_hash"])
            .reset_index(drop=True)
        )

    # Save clean CSV
    clean_dir = output_dir / "clean" if "clean" not in str(output_dir) else output_dir
    if "clean" not in str(clean_dir):
        clean_dir = output_dir / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_path = clean_dir / f"{ts}_offline_clean.csv"
    save_csv(df, clean_path)

    companies = sorted(df["company"].unique().tolist()) if not df.empty else []

    return {
        "raw_path": str(raw_path),
        "clean_path": str(clean_path),
        "total_posts": len(df),
        "companies": companies,
    }
