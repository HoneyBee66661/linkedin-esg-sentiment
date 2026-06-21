# -*- coding: utf-8 -*-
"""
Helper script: Extract LinkedIn cookies from Chrome, then save them.
Run this after Chrome is started with --remote-debugging-port=9222
"""
from playwright.sync_api import sync_playwright
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import sys

# Skip if there's a "--go" flag
if "--go" not in sys.argv:
    print("=" * 60)
    print("Langkah-langkah:")
    print("1. Tutup Chrome yang sedang berjalan")
    print('2. Buka CMD baru dan jalankan:')
    print()
    print('   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\Users\\REY\\chrome-esg-profile"')
    print()
    print("3. Di Chrome baru, login ke linkedin.com")
    print("4. Kembali ke terminal ini dan ketik:")
    print("   python scripts/scrape_vale.py --go")
    print("=" * 60)
    sys.exit(0)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    print(f"Connected! Contexts: {len(browser.contexts)}")

    context = browser.contexts[0]
    page = context.new_page()
    page.goto("https://www.linkedin.com/feed/", timeout=15000)
    print(f"URL: {page.url}")

    if "feed" in page.url or "checkpoint" in page.url:
        print("OK! Logged in to LinkedIn.")

        # Save cookies for future headless use
        cookie_path = Path("data/linkedin_cookies.json")
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        cookies = context.cookies()
        li_cookies = [c for c in cookies if "linkedin.com" in str(c.get("domain", ""))]
        with open(cookie_path, "w") as f:
            json.dump(li_cookies, f, indent=2)
        print(f"Saved {len(li_cookies)} LinkedIn cookies to {cookie_path}")

        # Scrape Vale posts
        print("\nScraping Vale Indonesia posts...")
        page.goto("https://www.linkedin.com/company/pt-vale-indonesia-tbk/posts/?feedView=all", timeout=30000)
        time.sleep(5)

        prev_count = 0
        for i in range(100):
            posts = page.query_selector_all('[data-urn^="urn:li:activity:"]')
            count = len(posts)
            print(f"Scroll {i+1}: ~{count} posts")

            if count >= 300:
                print("Target 300 posts reached!")
                break
            if i > 3 and count == prev_count:
                print("No more new posts — scroll limit")
                break
            prev_count = count

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2.5)

        # Save HTML
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_dir = Path("data/raw/linkedin_pages")
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / f"vale_{ts}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"\nSaved HTML: {html_path}")
    else:
        print("Not logged in. Login to LinkedIn in the Chrome window first.")

    context.close()
