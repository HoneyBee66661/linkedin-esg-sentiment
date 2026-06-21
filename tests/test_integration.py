# -*- coding: utf-8 -*-
"""Integration tests: end-to-end pipeline."""
import pytest
from pathlib import Path
from src.extract import extract_pipeline
from src.quality_gate import quality_gate_and_normalize
from src.io_utils import load_csv


@pytest.fixture
def multi_company_html(tmp_path):
    """Two HTML files for different companies."""
    html1 = """<!DOCTYPE html>
<html><head><title>(7) PT Vale Indonesia Tbk | LinkedIn</title></head>
<body>
<article data-urn="urn:li:activity:1001">
    <div class="update-components-text"><span>ESG post about reclamation</span></div>
    <time datetime="2025-10-01T08:00:00.000Z"></time>
    <span data-test-reactions-count>10</span>
</article>
<article data-urn="urn:li:activity:1002">
    <div class="update-components-text"><span>Hiring opening for engineer</span></div>
    <time datetime="2025-10-02T09:00:00.000Z"></time>
</article>
</body></html>"""

    html2 = """<!DOCTYPE html>
<html><head><title>PT Freeport Indonesia | LinkedIn</title></head>
<body>
<article data-urn="urn:li:activity:2001">
    <div class="update-components-text"><span>Community development program</span></div>
    <time datetime="2025-10-03T10:00:00.000Z"></time>
    <span data-test-reactions-count>25</span>
</article>
</body></html>"""

    f1 = tmp_path / "vale.html"
    f2 = tmp_path / "freeport.html"
    f1.write_text(html1, encoding="utf-8")
    f2.write_text(html2, encoding="utf-8")
    return tmp_path


class TestIntegration:
    def test_multi_company_pipeline(self, multi_company_html):
        """End-to-end: extract -> process for 2 companies."""
        output_dir = multi_company_html / "output"

        # Extract
        result = extract_pipeline(
            input_path=multi_company_html,
            output_dir=output_dir,
            exclude_hiring=True,
        )

        # Should have 2 posts (1 hiring filtered out from Vale)
        assert result["total_posts"] == 2
        companies = set(result["companies"])
        assert "Vale Indonesia" in companies
        assert "Freeport Indonesia" in companies

        # Load clean CSV and apply quality gate
        clean_df = load_csv(result["clean_path"])
        processed = quality_gate_and_normalize(clean_df)

        assert len(processed) == 2
        assert "company_norm" in processed.columns
        assert "document_id" in processed.columns
        assert "word_count" in processed.columns

    def test_raw_json_schema(self, multi_company_html):
        """Verify raw JSON output has correct schema."""
        output_dir = multi_company_html / "output2"
        result = extract_pipeline(
            multi_company_html, output_dir, exclude_hiring=False
        )

        import json
        with open(result["raw_path"], "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        assert len(raw_data) >= 2  # all posts including hiring
        for post in raw_data:
            assert "company" in post
            assert "post_id" in post
            assert "text_raw" in post
            assert "posted_at_utc" in post
            assert "crawl_timestamp_utc" in post

    def test_csv_columns(self, multi_company_html):
        """Verify clean CSV has expected columns."""
        output_dir = multi_company_html / "output3"
        result = extract_pipeline(
            multi_company_html, output_dir, exclude_hiring=False
        )

        df = load_csv(result["clean_path"])
        expected_cols = {
            "company", "post_id", "post_permalink", "posted_at_utc",
            "text_raw", "text_clean", "dedupe_hash",
        }
        assert expected_cols.issubset(set(df.columns))
