# -*- coding: utf-8 -*-
"""
LinkedIn Playwright Stealth Scraper for ESG Company Posts.

Scrapes LinkedIn company posts for multiple mining companies,
saves full HTML pages that can be processed by the existing pipeline.

Usage:
    python -m src.linkedin_scraper --companies vale,freeport
    python -m src.linkedin_scraper --all --months 12
    python -m src.linkedin_scraper --cookie cookie.json
"""
import os
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser

logger = logging.getLogger(__name__)

# ── Target Companies ────────────────────────────────────────────────
# LinkedIn company slugs and display names
COMPANIES = {
    "vale": {
        "slug": "pt-vale-indonesia-tbk",
        "name": "PT Vale Indonesia Tbk",
    },
    "freeport": {
        "slug": "pt-freeport-indonesia",
        "name": "PT Freeport Indonesia",
    },
    "adaro": {
        "slug": "pt-adaro-energy",
        "name": "PT Adaro Energy",
    },
    "bukit-asam": {
        "slug": "pt-bukit-asam",
        "name": "PT Bukit Asam",
    },
    "antam": {
        "slug": "pt-antam",
        "name": "PT ANTAM",
    },
}

DEFAULT_OUTPUT = Path("data/raw/linkedin_pages")


def get_posts_url(slug: str) -> str:
    """Build LinkedIn company posts page URL."""
    return f"https://www.linkedin.com/company/{slug}/posts/?feedView=all"


def parse_relative_date(text: str) -> Optional[datetime]:
    """
    Parse LinkedIn relative dates like '2d', '1w', '3mo', '1y' into absolute dates.
    Returns datetime or None if unparseable.
    """
    if not text:
        return None
    text = text.strip().lower()
    now = datetime.now(timezone.utc)

    try:
        if "min" in text or "now" in text or "just" in text:
            return now
        if "h" in text and not any(c in text for c in "d wmo y"):
            val = int(text.replace("h", "").replace(" ", ""))
            return now
        if "d" in text:
            val = int(text.replace("d", "").replace(" ", ""))
            return datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - __import__('datetime').timedelta(days=val)
        if "w" in text:
            val = int(text.replace("w", "").replace(" ", ""))
            return now - __import__('datetime').timedelta(weeks=val)
        if "mo" in text:
            val = int(text.replace("mo", "").replace(" ", ""))
            month = now.month - val
            year = now.year
            while month < 1:
                month += 12
                year -= 1
            return datetime(year, month, 1, tzinfo=timezone.utc)
        if "y" in text:
            val = int(text.replace("y", "").replace(" ", ""))
            return datetime(now.year - val, now.month, 1, tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None
    return None


def apply_stealth(page: Page):
    """Apply playwright-stealth evasions."""
    try:
        from playwright_stealth.stealth import Stealth
        s = Stealth()
        s.apply_stealth_sync(page)
        logger.info("✅ Playwright stealth applied")
    except (ImportError, AttributeError) as e:
        logger.warning(f"playwright-stealth not available ({e}) — running with manual evasions")
        # Apply minimal evasions manually
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)


def load_cookies(context, cookie_path: Optional[Path] = None):
    """Load saved cookies for LinkedIn session."""
    cookie_file = cookie_path or Path("data/linkedin_cookies.json")
    if cookie_file.exists():
        with open(cookie_file) as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        logger.info(f"Loaded {len(cookies)} cookies from {cookie_file}")
        return True
    return False


def save_cookies(context, cookie_path: Optional[Path] = None):
    """Save cookies after successful login."""
    cookie_file = cookie_path or Path("data/linkedin_cookies.json")
    cookie_file.parent.mkdir(parents=True, exist_ok=True)
    cookies = context.cookies()
    with open(cookie_file, "w") as f:
        json.dump(cookies, f, indent=2)
    logger.info(f"Saved {len(cookies)} cookies to {cookie_file}")


def login_interactive(page: Page, email: str = "", password: str = ""):
    """
    Interactive login — if credentials provided, auto-fill.
    Otherwise, wait for user to login manually.
    """
    page.goto("https://www.linkedin.com/login", timeout=60000)

    if email and password:
        page.fill("#username", email)
        page.fill("#password", password)
        page.click('button[type="submit"]')
        time.sleep(5)
    else:
        print("\n⚠️  No credentials provided.")
        print("Please login to LinkedIn manually in the browser window.")
        print("Waiting up to 120 seconds for login...")
        page.wait_for_url("**/feed/**", timeout=120000)

    # Check if login succeeded
    if "feed" in page.url or "checkpoint" in page.url:
        logger.info(f"Login status: {page.url}")
        return True
    else:
        logger.warning(f"Login may have failed. Current URL: {page.url}")
        return False


def scroll_posts(page: Page, target_posts: int = 200, max_scrolls: int = 100):
    """
    Scroll the posts page to load more content.
    Returns estimated number of posts loaded.
    """
    post_count = 0
    for i in range(max_scrolls):
        # Count visible posts
        prev_count = post_count
        try:
            posts = page.query_selector_all('[data-urn^="urn:li:activity:"]')
            post_count = len(posts)
        except Exception:
            posts = []

        logger.info(f"Scroll {i+1}/{max_scrolls}: ~{post_count} posts loaded")

        if post_count >= target_posts:
            logger.info(f"Reached target of {target_posts} posts")
            break

        if post_count == prev_count and i > 3:
            # No new posts loaded — might be at the end
            logger.info("No new posts — reached scroll limit")
            break

        # Scroll down smoothly
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2.0 + __import__('random').uniform(0.5, 1.5))

        # Occasionally scroll up a bit to look human
        if i % 5 == 4:
            page.evaluate("window.scrollBy(0, -300)")
            time.sleep(1)

    return post_count


def scrape_company_posts(
    browser: Browser,
    slug: str,
    company_name: str,
    output_dir: Path,
    email: str = "",
    password: str = "",
    cookie_path: Optional[Path] = None,
    target_posts: int = 200,
    headless: bool = False,
) -> Optional[Path]:
    """
    Scrape all posts for a single company and save HTML.

    Returns path to saved HTML file, or None if failed.
    """
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        locale="en-US",
    )

    page = context.new_page()
    apply_stealth(page)

    # Load saved cookies first
    cookies_loaded = load_cookies(context, cookie_path)

    if not cookies_loaded:
        # Need to login
        login_interactive(page, email, password)
        save_cookies(context, cookie_path)
    else:
        # Go to feed first to validate cookies
        page.goto("https://www.linkedin.com/feed/", timeout=30000)
        time.sleep(3)
        if "checkpoint" in page.url or "login" in page.url:
            logger.warning("Cookies expired — re-logging in")
            login_interactive(page, email, password)
            save_cookies(context, cookie_path)

    # Navigate to company posts
    url = get_posts_url(slug)
    logger.info(f"Navigating to {url}")
    page.goto(url, timeout=60000)
    time.sleep(5)

    # Check for "Show all" / "See all posts" buttons
    try:
        show_all = page.query_selector("a:has-text('Show all posts')")
        if show_all:
            show_all.click()
            time.sleep(3)
    except Exception:
        pass

    # Scroll to load posts
    logger.info(f"Scrolling to load up to {target_posts} posts...")
    posts_loaded = scroll_posts(page, target_posts=target_posts)
    logger.info(f"Loaded approximately {posts_loaded} posts")

    # Save HTML
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_name = slug.replace("-", "_")
    html_path = output_dir / f"{safe_name}_{ts}.html"

    html_content = page.content()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Saved HTML ({len(html_content)} bytes) to {html_path}")
    context.close()
    return html_path


def scrape_all_companies(
    companies: list[str],
    output_dir: Path = DEFAULT_OUTPUT,
    email: str = "",
    password: str = "",
    cookie_path: Optional[Path] = None,
    target_posts: int = 200,
    headless: bool = False,
) -> dict[str, Path]:
    """Scrape all specified companies and return {company_slug: html_path}."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        for slug in companies:
            if slug not in COMPANIES:
                logger.warning(f"Unknown company slug: {slug}")
                continue

            info = COMPANIES[slug]
            logger.info(f"\n{'='*60}")
            logger.info(f"Scraping: {info['name']} ({slug})")
            logger.info(f"{'='*60}")

            try:
                html_path = scrape_company_posts(
                    browser=browser,
                    slug=slug,
                    company_name=info["name"],
                    output_dir=output_dir,
                    email=email,
                    password=password,
                    cookie_path=cookie_path,
                    target_posts=target_posts,
                    headless=headless,
                )
                if html_path:
                    results[slug] = html_path
            except Exception as e:
                logger.error(f"Failed to scrape {slug}: {e}")

            # Wait between companies to avoid rate limiting
            time.sleep(5)

        browser.close()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn Scraper for ESG Company Posts (Playwright Stealth)"
    )
    parser.add_argument(
        "--companies", "-c",
        help="Comma-separated company slugs: vale,freeport,adaro,bukit-asam,antam",
    )
    parser.add_argument("--all", action="store_true", help="Scrape all 5 companies")
    parser.add_argument(
        "--output", "-o",
        default=str(DEFAULT_OUTPUT),
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--email", help="LinkedIn email (optional — interactive login if not provided)"
    )
    parser.add_argument(
        "--password", help="LinkedIn password (optional)"
    )
    parser.add_argument(
        "--cookie",
        default="data/linkedin_cookies.json",
        help="Path to cookie file (default: data/linkedin_cookies.json)"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=200,
        help="Target number of posts per company (default: 200)"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run browser in headless mode (default: visible for login)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Determine which companies to scrape
    if args.all:
        slugs = list(COMPANIES.keys())
    elif args.companies:
        slugs = [s.strip() for s in args.companies.split(",")]
    else:
        slugs = ["vale"]  # Default: just Vale

    logger.info(f"Companies to scrape: {slugs}")
    logger.info(f"Target posts per company: {args.target}")
    logger.info(f"Headless mode: {args.headless}")

    cookie_path = Path(args.cookie)
    output_dir = Path(args.output)

    results = scrape_all_companies(
        companies=slugs,
        output_dir=output_dir,
        email=args.email or "",
        password=args.password or "",
        cookie_path=cookie_path,
        target_posts=args.target,
        headless=args.headless,
    )

    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    for slug, path in results.items():
        print(f"  ✓ {COMPANIES[slug]['name']}: {path}")
    print(f"\nNext step: linkedin-esg extract {output_dir}/ --out data/")
    print(f"Or: python -m src.linkedin_scraper --help")


if __name__ == "__main__":
    main()
