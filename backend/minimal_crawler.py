#!/usr/bin/env python3
"""
Minimal browser profile crawler with deep crawling

Usage:
    # Create a profile
    python3 minimal_crawler.py create myprofile
    
    # Deep crawl with profile
    python3 minimal_crawler.py crawl https://example.com --profile myprofile
    
    # Deep crawl without profile
    python3 minimal_crawler.py crawl https://example.com
    
    # List profiles
    python3 minimal_crawler.py list
"""
import asyncio
import sys
import os
import re
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, BrowserProfiler, CacheMode

def sanitize_filename(url):
    """Convert URL to safe filename"""
    # Remove protocol
    filename = re.sub(r'^https?://', '', url)
    # Replace special characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Limit length
    return filename[:200]

async def create_profile(name):
    """Create a browser profile"""
    profiler = BrowserProfiler()
    print(f"\n🌐 Creating profile '{name}'...")
    print("📋 Log in to your sites, then press 'q' to save")
    
    profile_path = await profiler.create_profile(name)
    
    if profile_path:
        print(f"✅ Profile saved: {profile_path}")
    else:
        print("❌ Failed to create profile")

async def deep_crawl(url, profile_name=None, max_depth=2, max_pages=50, delay=1):
    """Simple deep crawl"""
    # Setup browser
    browser_config = BrowserConfig(
        headless=False,
        use_managed_browser=True,
        browser_type="chromium"
    )
    
    # Load profile if specified
    if profile_name:
        profiler = BrowserProfiler()
        profile_path = profiler.get_profile_path(profile_name)
        
        if not profile_path:
            print(f"❌ Profile '{profile_name}' not found")
            return
        
        browser_config.user_data_dir = profile_path
        print(f"🔐 Using profile: {profile_name}")
    
    # Create output directory
    output_dir = Path("crawled_data") / (profile_name or "no_profile")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track visited URLs
    visited = set()
    queue = [(url, 0)]  # (url, depth)
    pages_crawled = 0
    base_domain = urlparse(url).netloc
    
    # Session for reusing browser tab
    session_id = f"crawl_{int(time.time())}"
    
    config = CrawlerRunConfig(
        page_timeout=60000,  # Increase timeout for SPAs
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        verbose=False,
        # Wait for content to load
        delay_before_return_html=5.0,
        # Ensure links are extracted
        exclude_external_links=False,
        exclude_internal_links=False
    )
    
    print(f"\n🕷️ Starting crawl: {url}")
    print(f"📊 Max depth: {max_depth}, Max pages: {max_pages}\n")
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            while queue and pages_crawled < max_pages:
                current_url, depth = queue.pop(0)
                
                # Skip if visited or too deep
                if current_url in visited or depth > max_depth:
                    continue
                
                visited.add(current_url)
                pages_crawled += 1
                
                print(f"[{pages_crawled}/{max_pages}] Depth {depth}: {current_url}")
                
                try:
                    # Crawl page
                    result = await crawler.arun(current_url, config=config)
                    
                    if result.success:
                        # Check if we got a loading page or actual content
                        content_text = result.markdown or result.html or "No content"
                        is_loading_page = any(phrase in content_text for phrase in [
                            "Loading", "loading", "Please wait", "app.component.ts",
                            "ClickUp is best experienced using our mobile app"
                        ])
                        
                        if is_loading_page:
                            print(f"  ⚠️  Got loading/mobile page, content may be incomplete")
                        
                        # Save content
                        filename = sanitize_filename(current_url) + ".txt"
                        filepath = output_dir / filename
                        
                        content = f"URL: {current_url}\n"
                        content += f"Crawled: {datetime.now()}\n"
                        content += f"{'='*50}\n"
                        content += content_text
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Extract links for next level
                        if depth < max_depth:
                            # Always extract links from HTML using BeautifulSoup
                            if hasattr(result, 'html') and result.html:
                                try:
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(result.html, 'html.parser')
                                    links_found = 0
                                    unique_links = set()
                                    
                                    # Look for regular links
                                    for link in soup.find_all('a', href=True):
                                        href = link['href'].strip()
                                        # Skip empty, anchor-only, or javascript links
                                        if not href or href.startswith('#') or href.startswith('javascript:'):
                                            continue
                                        
                                        # Make absolute URL
                                        absolute_url = urljoin(current_url, href)
                                        
                                        # Normalize URL (remove fragment, trailing slash)
                                        parsed = urlparse(absolute_url)
                                        normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                        if parsed.query:
                                            normalized_url += f"?{parsed.query}"
                                        
                                        # Check if same domain and not visited
                                        if parsed.netloc == base_domain and normalized_url not in visited and normalized_url not in unique_links:
                                            unique_links.add(normalized_url)
                                            queue.append((normalized_url, depth + 1))
                                            links_found += 1
                                    
                                    # For SPAs like ClickUp, also look for common navigation patterns
                                    if "clickup" in base_domain.lower() and links_found == 0:
                                        # Try to find ClickUp navigation elements
                                        nav_patterns = [
                                            ("div[data-test*='nav']", "data-href"),
                                            ("div[role='navigation'] a", "href"),
                                            ("a[href*='/v/']", "href"),  # ClickUp view links
                                            ("a[href*='/t/']", "href"),  # ClickUp task links
                                            ("a[href*='/docs/']", "href"),  # ClickUp docs links
                                        ]
                                        
                                        for selector, attr in nav_patterns:
                                            elements = soup.select(selector)
                                            for elem in elements:
                                                href = elem.get(attr, "").strip()
                                                if href and not href.startswith('#'):
                                                    absolute_url = urljoin(current_url, href)
                                                    parsed = urlparse(absolute_url)
                                                    normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                                    
                                                    if parsed.netloc == base_domain and normalized_url not in visited:
                                                        unique_links.add(normalized_url)
                                                        queue.append((normalized_url, depth + 1))
                                                        links_found += 1
                                    
                                    if links_found > 0:
                                        print(f"  📎 Found {links_found} new links")
                                except Exception as e:
                                    print(f"  ⚠️  Error extracting links: {str(e)}")
                    
                    else:
                        print(f"  ❌ Failed: {result.error_message}")
                        
                except Exception as e:
                    print(f"  ❌ Error: {str(e)}")
                
                # Delay between requests
                if delay > 0 and queue:
                    await asyncio.sleep(delay)
                    
        finally:
            # Clean up session
            try:
                await crawler.crawler_strategy.kill_session(session_id)
            except:
                pass
    
    print(f"\n✅ Crawled {pages_crawled} pages")
    print(f"💾 Saved to: {output_dir}")

def list_profiles():
    """List all profiles"""
    profiler = BrowserProfiler()
    profiles = profiler.list_profiles()
    
    if not profiles:
        print("No profiles found.")
    else:
        print("\n📁 Profiles:")
        for p in profiles:
            print(f"  • {p['name']}")

# Main
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Minimal browser profile crawler")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create profile
    create_parser = subparsers.add_parser('create', help='Create profile')
    create_parser.add_argument('name', help='Profile name')
    
    # Crawl
    crawl_parser = subparsers.add_parser('crawl', help='Deep crawl')
    crawl_parser.add_argument('url', help='Starting URL')
    crawl_parser.add_argument('--profile', help='Profile to use')
    crawl_parser.add_argument('--depth', type=int, default=2, help='Max depth (default: 2)')
    crawl_parser.add_argument('--max-pages', type=int, default=50, help='Max pages (default: 50)')
    crawl_parser.add_argument('--delay', type=float, default=1, help='Delay between pages (default: 1)')
    
    # List profiles
    list_parser = subparsers.add_parser('list', help='List profiles')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        asyncio.run(create_profile(args.name))
    
    elif args.command == 'crawl':
        asyncio.run(deep_crawl(
            args.url,
            profile_name=args.profile,
            max_depth=args.depth,
            max_pages=args.max_pages,
            delay=args.delay
        ))
    
    elif args.command == 'list':
        list_profiles()
    
    else:
        parser.print_help()