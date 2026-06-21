# -*- coding: utf-8 -*-
"""Tests for src.extract module."""
import json
import pytest
from pathlib import Path
from src.extract import (
    extract_posts_from_html,
    to_row,
    clean_company_name,
    extract_pipeline,
)


@pytest.fixture
def sample_html(tmp_path):
    """Create a minimal fake LinkedIn HTML file for testing."""
    html_content = """<!DOCTYPE html>
<html>
<head><title>(7) PT Vale Indonesia Tbk: Posts | LinkedIn</title></head>
<body>
<article data-urn="urn:li:activity:7386231328050032641">
    <div class="update-components-text">
        <span>ESG sustainability post about carbon emissions</span>
    </div>
    <time datetime="2025-10-15T08:00:00.000Z"></time>
    <span data-test-reactions-count>42 reactions</span>
    <button aria-label="Comment">3 comments</button>
    <button aria-label="Repost">1 repost</button>
</article>
<article data-urn="urn:li:activity:7385947890613067776">
    <div class="update-components-text">
        <span>We are hiring! Join our team</span>
    </div>
    <time datetime="2025-10-16T09:00:00.000Z"></time>
</article>
</body>
</html>"""
    path = tmp_path / "vale_1.html"
    path.write_text(html_content, encoding="utf-8")
    return path


class TestExtractPosts:
    def test_extract_basic(self, sample_html):
        posts = extract_posts_from_html(str(sample_html))
        assert len(posts) == 2
        assert posts[0]["company"] == "Vale Indonesia"
        assert posts[0]["post_id"] == "7386231328050032641"

    def test_extract_with_company_override(self, sample_html):
        posts = extract_posts_from_html(str(sample_html), company_override="Vale Indonesia")
        assert posts[0]["company"] == "Vale Indonesia"

    def test_engagement_counts(self, sample_html):
        posts = extract_posts_from_html(str(sample_html))
        p = posts[0]
        assert p["reactions_count"] == 42
        assert p["comments_count"] == 3
        assert p["reshares_count"] == 1

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            extract_posts_from_html("nonexistent.html")


class TestToRow:
    def test_basic_row(self):
        post = {
            "company": "Vale Indonesia",
            "post_id": "12345",
            "post_permalink": "https://linkedin.com/feed/update/urn:li:activity:12345",
            "posted_at_utc": "2025-10-15T08:00:00.000Z",
            "text_raw": "ESG post about sustainability",
            "hashtags": ["#ESG", "#sustainability"],
            "media_urls": ["https://example.com/img.jpg"],
            "external_links": [],
            "reactions_count": 10,
            "comments_count": 2,
            "reshares_count": 1,
            "evidence_snapshot_path": "/tmp/test.html",
            "crawl_timestamp_utc": "2025-10-21T10:17:29+00:00",
        }
        row = to_row(post)
        assert row["company"] == "Vale Indonesia"
        assert row["post_id"] == "12345"
        assert row["hashtags"] == "#ESG,#sustainability"
        assert row["media_urls"] == "https://example.com/img.jpg"
        assert len(row["dedupe_hash"]) == 40  # SHA1 hex

    def test_clean_text_removes_urls(self):
        post = {
            "company": "Test",
            "post_id": "1",
            "posted_at_utc": None,
            "text_raw": "Check https://example.com/page for details",
        }
        row = to_row(post)
        # Also supply missing fields
        row = to_row({
            **post,
            "hashtags": [],
            "media_urls": [],
            "external_links": [],
            "evidence_snapshot_path": "/tmp/test.html",
            "crawl_timestamp_utc": "2025-10-21T10:17:29+00:00",
        })
        assert "https://" not in row["text_clean"]


class TestCleanCompanyName:
    def test_clean_vale(self):
        assert clean_company_name("(7) PT Vale Indonesia Tbk: Posts") == "Vale Indonesia"

    def test_clean_freeport(self):
        assert clean_company_name("(3) Freeport Indonesia") == "Freeport Indonesia"
        assert clean_company_name("Freeport Indonesia") == "Freeport Indonesia"


class TestExtractPipeline:
    def test_pipeline_on_single_file(self, sample_html):
        result = extract_pipeline(
            input_path=sample_html,
            output_dir=sample_html.parent,
            exclude_hiring=True,
        )
        assert result["total_posts"] == 1  # 1 filtered out (hiring)
        assert "Vale Indonesia" in result["companies"]
        assert result["raw_path"] is not None
        assert result["clean_path"] is not None
