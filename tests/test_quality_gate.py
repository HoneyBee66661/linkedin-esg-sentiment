# -*- coding: utf-8 -*-
"""Tests for src.quality_gate module."""
import pandas as pd
import pytest
from datetime import datetime, timezone
from src.quality_gate import sanitize_text, norm_company, quality_gate_and_normalize


class TestSanitizeText:
    def test_remove_nbsp(self):
        assert sanitize_text("hello\u00a0world") == "hello world"

    def test_remove_zwsp(self):
        assert sanitize_text("hello\u200bworld") == "helloworld"

    def test_collapse_whitespace(self):
        assert sanitize_text("hello    world") == "hello world"

    def test_none(self):
        assert sanitize_text(None) == ""

    def test_trim(self):
        assert sanitize_text("  hello  ") == "hello"


class TestNormCompany:
    def test_vale(self):
        assert norm_company("(7) PT Vale Indonesia Tbk: Posts") == "Vale Indonesia"

    def test_freeport(self):
        assert norm_company("Freeport Indonesia") == "Freeport Indonesia"

    def test_unknown(self):
        assert norm_company("") == "unknown"
        assert norm_company(None) == "unknown"

    def test_case_insensitive(self):
        assert norm_company("pt vale indonesia tbk") == "Vale Indonesia"


class TestQualityGate:
    def test_empty_df(self):
        df = pd.DataFrame()
        result = quality_gate_and_normalize(df)
        assert result.empty

    def test_basic_pipeline(self):
        df = pd.DataFrame({
            "company": ["(7) PT Vale Indonesia Tbk: Posts"],
            "post_id": ["123"],
            "text_raw": ["  hello\u00a0world  "],
            "text_clean": ["hello world"],
            "media_urls": [""],
            "posted_at_utc": ["2025-10-21 10:17:29+00:00"],
            "crawl_timestamp_utc": [datetime.now(timezone.utc).isoformat()],
            "reactions_count": [5],
            "comments_count": [None],
            "reshares_count": [None],
        })
        result = quality_gate_and_normalize(df)
        assert not result.empty
        assert result["company_norm"].iloc[0] == "Vale Indonesia"
        assert result["word_count"].iloc[0] == 2
        assert result["has_media"].iloc[0] == "N"
        assert result["comments_count"].iloc[0] == 0
        assert "document_id" in result.columns
        assert "month" in result.columns

    def test_timestamp_fallback(self):
        df = pd.DataFrame({
            "company": ["Vale"],
            "post_id": ["456"],
            "text_raw": ["test post"],
            "text_clean": ["test post"],
            "media_urls": [""],
            "posted_at_utc": [None],
            "crawl_timestamp_utc": ["2025-10-21T10:17:29+00:00"],
            "reactions_count": [0],
            "comments_count": [0],
            "reshares_count": [0],
        })
        result = quality_gate_and_normalize(df)
        assert result["posted_at_utc"].iloc[0] is not pd.NaT
