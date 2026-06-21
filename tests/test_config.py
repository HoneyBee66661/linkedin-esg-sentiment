# -*- coding: utf-8 -*-
"""Tests for src.config module."""
import pytest
from src.config import (
    looks_like_hiring,
    categorize_esg,
)
from src.extract import clean_company_name


class TestLooksLikeHiring:
    def test_hiring_keyword_en(self):
        assert looks_like_hiring("We are hiring a new manager")
        assert looks_like_hiring("We're hiring!")
        assert looks_like_hiring("Now hiring engineers")

    def test_hiring_keyword_id(self):
        # These are clearly hiring/job posts
        assert looks_like_hiring("Lowongan pekerjaan tersedia")
        assert looks_like_hiring("Rekrutmen terbuka")
        # New stricter patterns
        assert looks_like_hiring("Membuka lowongan baru")
        assert looks_like_hiring("Buka karir bersama kami")
        assert looks_like_hiring("Open position for manager")

    def test_non_hiring(self):
        assert not looks_like_hiring("")
        assert not looks_like_hiring(None)
        # No hiring keywords present at all
        assert not looks_like_hiring("Regular ESG post about sustainability")
        assert not looks_like_hiring("Community empowerment program")
        assert not looks_like_hiring("Carbon emission reduction")
        assert not looks_like_hiring("Environmental impact report")
        assert not looks_like_hiring("Board of directors meeting results")


class TestCategorizeESG:
    def test_environmental(self):
        assert "E" in categorize_esg("carbon emission reduction")

    def test_social(self):
        assert "S" in categorize_esg("community empowerment program")

    def test_governance(self):
        assert "G" in categorize_esg("board transparency and audit")

    def test_multiple_pillars(self):
        cats = categorize_esg("carbon emission and community health and board governance")
        assert "E" in cats
        assert "S" in cats
        assert "G" in cats

    def test_empty(self):
        assert categorize_esg("") == []
        assert categorize_esg(None) == []


class TestCleanCompanyName:
    def test_remove_prefix(self):
        result = clean_company_name("(7) PT Vale Indonesia Tbk: Posts")
        assert result == "Vale Indonesia"

    def test_remove_suffix(self):
        result = clean_company_name("(3) Freeport Indonesia: Posts")
        assert result == "Freeport Indonesia"

    def test_unknown(self):
        assert clean_company_name("") == "unknown"
        assert clean_company_name(None) == "unknown"

    def test_mapping_exact(self):
        assert clean_company_name("PT Vale Indonesia Tbk") == "Vale Indonesia"
        assert clean_company_name("PT Freeport Indonesia") == "Freeport Indonesia"
