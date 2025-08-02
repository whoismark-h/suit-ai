#!/usr/bin/env python3
"""
Browser profile crawler with deep crawling capabilities

This tool allows you to:
1. Create and manage browser profiles for authenticated crawling
2. Crawl single pages with saved authentication
3. Perform deep crawls of entire websites using various strategies

Usage Examples:
    # Create a profile
    python3 profile_crawler.py create myprofile
    
    # Crawl a single page
    python3 profile_crawler.py crawl https://example.com --profile myprofile
    
    # Deep crawl with BFS strategy (default)
    python3 profile_crawler.py deep-crawl https://example.com --depth 3 --max-pages 100
    
    # Deep crawl with authentication
    python3 profile_crawler.py deep-crawl https://example.com --profile myprofile --depth 2
    
    # Best-first crawl with keywords
    python3 profile_crawler.py deep-crawl https://docs.example.com --strategy best-first --keywords api tutorial guide
    
    # Pattern-based crawling
    python3 profile_crawler.py deep-crawl https://example.com --patterns "*/docs/*" "*/api/*" --depth 3
    
    # Add delay between requests (recommended for rate limiting)
    python3 profile_crawler.py deep-crawl https://example.com --delay 1.5
    
    # List all profiles
    python3 profile_crawler.py list

Deep Crawling Strategies:
    - bfs (Breadth-First Search): Explores all pages at one depth before moving deeper
    - dfs (Depth-First Search): Follows links deeply before backtracking
    - best-first: Prioritizes pages based on keyword relevance scores

Important Notes:
    - When using profiles (authenticated sessions), crawling is always sequential to avoid browser conflicts
    - Sequential crawling uses session-based approach with a single browser tab
    - Use --delay to add delays between requests to respect rate limits
    - For public crawls without authentication, the built-in deep crawl strategies are used

Results are saved to:
    - Single crawls: crawled_data/
    - Deep crawls: crawled_data/deep_crawl/
"""
import asyncio
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, BrowserProfiler, CacheMode
from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy, 
    BestFirstCrawlingStrategy
)
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter,
    SEOFilter
)
from crawl4ai.deep_crawling.scorers import (
    KeywordRelevanceScorer
)

async def create_profile(name):
    """Create/update a browser profile"""
    profiler = BrowserProfiler()
    print(f"\n🌐 Creating profile '{name}'...")
    print("\n📋 Instructions:")
    print("  1. A browser window will open")
    print("  2. Navigate to your target website and log in")
    print("  3. Make sure you're fully authenticated")
    print("  4. Press 'q' in THIS TERMINAL (not the browser) to save")
    print("\n⏳ Opening browser...\n")
    
    profile_path = await profiler.create_profile(name)
    
    if profile_path:
        print(f"\n✅ Profile saved to: {profile_path}")
        # Profile created successfully
    else:
        print(f"\n❌ Failed to create profile")

async def crawl(url, profile_name):
    """Crawl URL with profile"""
    profiler = BrowserProfiler()
    profile_path = profiler.get_profile_path(profile_name)
    
    if not profile_path:
        print(f"❌ Profile '{profile_name}' not found. Create it first.")
        return
    
    print(f"🔍 Crawling {url}...")
    
    browser_config = BrowserConfig(
        headless=False,
        user_data_dir=profile_path,
        use_managed_browser=True,  # Important for profile persistence
        browser_type="chromium"
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url, config=CrawlerRunConfig(
            page_timeout=60000,  # 60 seconds
            delay_before_return_html=5.0,  # Wait 15 seconds for content to load
            remove_overlay_elements=True,
            scan_full_page=True,
            cache_mode=CacheMode.BYPASS,
            verbose=True
        ))
        
        if result.success:
            # Check if we got login page instead of content
            if "Welcome back!" in result.markdown or "Log In" in result.markdown:
                print(f"⚠️  Got login page instead of authenticated content!")
                print(f"💡 Tips:")
                print(f"   1. Recreate the profile and ensure you're fully logged in")
                print(f"   2. Try navigating to the docs page before pressing 'q'")
                print(f"   3. Check if your session has expired")
            
            # Save content
            Path("crawled_data").mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawled_data/{timestamp}.txt"
            
            content = f"URL: {url}\n{'='*50}\n{result.markdown or result.html}"
            
            with open(filename, 'w') as f:
                f.write(content)
            
            print(f"✅ Saved: {filename} ({len(content)} chars)")
        else:
            print(f"❌ Failed: {result.error_message}")

async def sequential_deep_crawl(url: str,
                               browser_config: BrowserConfig,
                               strategy: str = "bfs",
                               max_depth: int = 2,
                               max_pages: int = 50,
                               keywords: Optional[List[str]] = None,
                               patterns: Optional[List[str]] = None,
                               domain_restrict: bool = True,
                               delay: float = 0):
    """Sequential deep crawl implementation for authenticated sessions"""
    from urllib.parse import urljoin, urlparse
    import re
    
    # Results tracking
    successful_pages = []
    failed_pages = []
    pages_by_depth = {}
    start_time = datetime.now()
    visited_urls = set()
    url_queue = [(url, 0)]  # (url, depth) tuples
    
    # Create session ID for reusing the same browser tab
    session_id = f"deep_crawl_{int(time.time())}"
    
    # Configure crawler for single page
    config = CrawlerRunConfig(
        page_timeout=30000,
        delay_before_return_html=3.0,
        remove_overlay_elements=True,
        scan_full_page=True,
        cache_mode=CacheMode.BYPASS,
        verbose=True,
        session_id=session_id,  # Reuse same tab
        # Extract all links for manual processing
        exclude_external_links=False,
        exclude_social_media_links=True
    )
    
    # Domain for filtering
    base_domain = urlparse(url).netloc if domain_restrict else None
    
    # Compile patterns if provided
    compiled_patterns = []
    if patterns:
        for pattern in patterns:
            # Convert glob patterns to regex
            regex_pattern = pattern.replace('*', '.*')
            compiled_patterns.append(re.compile(regex_pattern))
    
    print(f"\n🕷️ Starting sequential {strategy.upper()} crawl")
    print(f"📊 Settings: depth={max_depth}, max_pages={max_pages}")
    print(f"🌍 Starting URL: {url}\n")
    
    pages_crawled = 0
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            while url_queue and pages_crawled < max_pages:
                current_url, current_depth = url_queue.pop(0)
                
                # Skip if already visited or depth exceeded
                if current_url in visited_urls or current_depth > max_depth:
                    continue
                
                visited_urls.add(current_url)
                
                # Crawl the page
                print(f"\n🔍 Crawling (depth {current_depth}): {current_url}")
                
                try:
                    result = await crawler.arun(current_url, config=config)
                    
                    if result.success:
                        pages_crawled += 1
                        
                        # Create a result object with metadata
                        result.metadata = result.metadata or {}
                        result.metadata['depth'] = current_depth
                        result.metadata['title'] = result.metadata.get('title', 'No title')
                        
                        # Calculate score if using keywords
                        score = 0
                        if keywords and result.markdown:
                            text_lower = result.markdown.lower()
                            for keyword in keywords:
                                score += text_lower.count(keyword.lower())
                            result.metadata['score'] = score
                        
                        process_result(result, successful_pages, failed_pages, pages_by_depth)
                        
                        # Extract links if not at max depth
                        if current_depth < max_depth and result.links:
                            internal_links = result.links.get('internal', [])
                            external_links = result.links.get('external', [])
                            
                            all_links = internal_links
                            if not domain_restrict:
                                all_links.extend(external_links)
                            
                            # Filter and queue links
                            for link_data in all_links:
                                link_url = link_data.get('href', '')
                                if not link_url:
                                    continue
                                
                                # Make absolute URL
                                absolute_url = urljoin(current_url, link_url)
                                
                                # Skip if already visited
                                if absolute_url in visited_urls:
                                    continue
                                
                                # Apply domain filter
                                if domain_restrict and base_domain:
                                    link_domain = urlparse(absolute_url).netloc
                                    if link_domain != base_domain:
                                        continue
                                
                                # Apply pattern filters
                                if compiled_patterns:
                                    matches_pattern = any(p.match(absolute_url) for p in compiled_patterns)
                                    if not matches_pattern:
                                        continue
                                
                                # Add to queue based on strategy
                                if strategy == "bfs":
                                    url_queue.append((absolute_url, current_depth + 1))
                                elif strategy == "dfs":
                                    url_queue.insert(0, (absolute_url, current_depth + 1))
                                elif strategy == "best-first" and keywords:
                                    # For best-first, we'd need to score the link text
                                    link_text = link_data.get('text', '').lower()
                                    link_score = sum(1 for k in keywords if k.lower() in link_text)
                                    # Insert based on score (simplified)
                                    if link_score > 0:
                                        url_queue.insert(0, (absolute_url, current_depth + 1))
                                    else:
                                        url_queue.append((absolute_url, current_depth + 1))
                    else:
                        # Handle failed result
                        failed_result = type('Result', (), {
                            'url': current_url,
                            'success': False,
                            'error_message': result.error_message or 'Unknown error',
                            'metadata': {'depth': current_depth}
                        })()
                        process_result(failed_result, successful_pages, failed_pages, pages_by_depth)
                        
                except Exception as e:
                    print(f"❌ Error crawling {current_url}: {str(e)}")
                    failed_result = type('Result', (), {
                        'url': current_url,
                        'success': False,
                        'error_message': str(e),
                        'metadata': {'depth': current_depth}
                    })()
                    process_result(failed_result, successful_pages, failed_pages, pages_by_depth)
                
                # Add delay between requests
                if delay > 0 and url_queue:
                    print(f"⏳ Waiting {delay}s before next page...")
                    await asyncio.sleep(delay)
                    
        finally:
            # Clean up session
            try:
                await crawler.crawler_strategy.kill_session(session_id)
            except:
                pass
    
    # Save results
    save_deep_crawl_results(successful_pages, failed_pages, pages_by_depth, start_time)
    
    # Print summary
    print_crawl_summary(successful_pages, failed_pages, pages_by_depth, start_time)

async def deep_crawl(url: str, 
                    profile_name: Optional[str] = None,
                    strategy: str = "bfs",
                    max_depth: int = 2,
                    max_pages: int = 50,
                    keywords: Optional[List[str]] = None,
                    patterns: Optional[List[str]] = None,
                    domain_restrict: bool = True,
                    stream: bool = True,
                    delay: float = 0):
    """Deep crawl a website using specified strategy"""
    
    # Configure browser
    browser_config = BrowserConfig(
        headless=False,
        use_managed_browser=True,
        browser_type="chromium"
    )
    
    # If profile specified, load it and force sequential mode
    if profile_name:
        profiler = BrowserProfiler()
        profile_path = profiler.get_profile_path(profile_name)
        
        if not profile_path:
            print(f"❌ Profile '{profile_name}' not found. Create it first.")
            return
        
        browser_config.user_data_dir = profile_path
        print(f"🔐 Using profile: {profile_name}")
        print("⚠️  Using sequential crawling for authenticated session")
        
        # When using profiles, we'll implement custom sequential crawling
        return await sequential_deep_crawl(
            url=url,
            browser_config=browser_config,
            strategy=strategy,
            max_depth=max_depth,
            max_pages=max_pages,
            keywords=keywords,
            patterns=patterns,
            domain_restrict=domain_restrict,
            delay=delay
        )
    
    # Configure filters
    filters = []
    
    # Domain filter
    if domain_restrict:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        filters.append(DomainFilter(allowed_domains=[domain]))
        print(f"🌐 Restricting to domain: {domain}")
    
    # URL pattern filter
    if patterns:
        filters.append(URLPatternFilter(patterns))
        print(f"🎯 URL patterns: {patterns}")
    
    # Content type filter - HTML only
    filters.append(ContentTypeFilter(allowed_types=["text/html", "application/xhtml+xml"]))
    
    filter_chain = FilterChain(filters) if filters else None
    
    # Configure scorer for best-first strategy
    url_scorer = None
    if strategy == "best-first" and keywords:
        url_scorer = KeywordRelevanceScorer(keywords=keywords, weight=1.0)
        print(f"🔍 Keywords for scoring: {keywords}")
    
    # Create strategy
    strategy_map = {
        "bfs": BFSDeepCrawlStrategy,
        "dfs": DFSDeepCrawlStrategy,
        "best-first": BestFirstCrawlingStrategy
    }
    
    if strategy not in strategy_map:
        print(f"❌ Unknown strategy: {strategy}")
        return
    
    strategy_class = strategy_map[strategy]
    deep_strategy = strategy_class(
        max_depth=max_depth,
        include_external=not domain_restrict,
        max_pages=max_pages,
        filter_chain=filter_chain,
        url_scorer=url_scorer
    )
    
    print(f"\n🕷️ Starting {strategy.upper()} deep crawl")
    print(f"📊 Settings: depth={max_depth}, max_pages={max_pages}")
    print(f"🌍 Starting URL: {url}\n")
    
    # Configure crawler
    config = CrawlerRunConfig(
        deep_crawl_strategy=deep_strategy,
        page_timeout=30000,  # 30 seconds per page
        delay_before_return_html=3.0,
        remove_overlay_elements=True,
        scan_full_page=True,
        cache_mode=CacheMode.BYPASS,
        stream=stream,
        verbose=True
    )
    
    # Results tracking
    successful_pages = []
    failed_pages = []
    pages_by_depth = {}
    start_time = datetime.now()
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Force sequential processing when using profiles to avoid browser conflicts
        if profile_name:
            print("⚠️  Using sequential crawling for authenticated session")
            stream = False
            
        if stream:
            # Streaming mode - process results as they come
            async for result in await crawler.arun(url, config=config):
                process_result(result, successful_pages, failed_pages, pages_by_depth)
                if delay > 0:
                    await asyncio.sleep(delay)
        else:
            # Batch mode - get all results at once
            results = await crawler.arun(url, config=config)
            # Check if results is a list or single result
            if not isinstance(results, list):
                results = [results]
            
            for i, result in enumerate(results):
                process_result(result, successful_pages, failed_pages, pages_by_depth)
                
                # Add delay between pages (except after the last one)
                if delay > 0 and i < len(results) - 1:
                    print(f"⏳ Waiting {delay}s before next page...")
                    await asyncio.sleep(delay)
    
    # Save results
    save_deep_crawl_results(successful_pages, failed_pages, pages_by_depth, start_time)
    
    # Print summary
    print_crawl_summary(successful_pages, failed_pages, pages_by_depth, start_time)

def process_result(result, successful_pages, failed_pages, pages_by_depth):
    """Process a single crawl result"""
    # Safely get depth from metadata
    depth = 0
    if hasattr(result, 'metadata') and result.metadata:
        depth = result.metadata.get("depth", 0)
    elif hasattr(result, 'depth'):
        depth = result.depth
    elif isinstance(result, dict) and 'metadata' in result:
        depth = result['metadata'].get('depth', 0)
    elif isinstance(result, dict) and 'depth' in result:
        depth = result['depth']
    
    # Safely check success status
    is_success = False
    if hasattr(result, 'success'):
        is_success = result.success
    elif isinstance(result, dict) and 'success' in result:
        is_success = result['success']
    else:
        # If we can't determine success, assume it's successful if we have content
        is_success = bool(getattr(result, 'html', None) or getattr(result, 'markdown', None))
    
    if is_success:
        successful_pages.append(result)
        
        # Track by depth
        if depth not in pages_by_depth:
            pages_by_depth[depth] = []
        
        # Safely get URL, title, and score
        url = getattr(result, 'url', 'Unknown URL')
        title = 'No title'
        score = 0
        
        if hasattr(result, 'metadata') and result.metadata:
            title = result.metadata.get('title', 'No title')
            score = result.metadata.get('score', 0)
        elif isinstance(result, dict):
            if 'metadata' in result:
                title = result['metadata'].get('title', 'No title')
                score = result['metadata'].get('score', 0)
            url = result.get('url', url)
            title = result.get('title', title)
            score = result.get('score', score)
        
        pages_by_depth[depth].append({
            'url': url,
            'title': title,
            'score': score
        })
        
        print(f"✅ Depth {depth} | Score: {score:.2f} | {url}")
    else:
        # Get error details safely
        url = getattr(result, 'url', 'Unknown URL')
        error_msg = getattr(result, 'error_message', 'Unknown error')
        
        if isinstance(result, dict):
            url = result.get('url', url)
            error_msg = result.get('error_message', error_msg)
        
        failed_pages.append({
            'url': url,
            'error': error_msg,
            'depth': depth
        })
        print(f"❌ Failed: {url} - {error_msg}")

def save_deep_crawl_results(successful_pages, failed_pages, pages_by_depth, start_time):
    """Save deep crawl results to files"""
    # Create results directory
    Path("crawled_data/deep_crawl").mkdir(parents=True, exist_ok=True)
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    
    # Save summary
    summary = {
        'start_time': start_time.isoformat(),
        'duration': (datetime.now() - start_time).total_seconds(),
        'total_pages': len(successful_pages),
        'failed_pages': len(failed_pages),
        'pages_by_depth': {str(k): len(v) for k, v in pages_by_depth.items()},
        'depth_details': pages_by_depth,
        'failures': failed_pages
    }
    
    summary_file = f"crawled_data/deep_crawl/{timestamp}_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Save individual page contents
    for i, result in enumerate(successful_pages):
        # Safely get attributes
        depth = 0
        url = 'Unknown URL'
        score = 0
        title = 'No title'
        content_body = "No content"
        
        # Get depth
        if hasattr(result, 'metadata') and result.metadata:
            depth = result.metadata.get("depth", 0)
            score = result.metadata.get('score', 0)
            title = result.metadata.get('title', 'No title')
        elif hasattr(result, 'depth'):
            depth = result.depth
        elif isinstance(result, dict):
            depth = result.get('depth', 0)
            score = result.get('score', 0)
            title = result.get('title', 'No title')
        
        # Get URL
        if hasattr(result, 'url'):
            url = result.url
        elif isinstance(result, dict) and 'url' in result:
            url = result['url']
        
        # Get content
        if hasattr(result, 'markdown') and result.markdown:
            content_body = result.markdown
        elif hasattr(result, 'html') and result.html:
            content_body = result.html
        elif isinstance(result, dict):
            content_body = result.get('markdown') or result.get('html') or "No content"
        
        page_file = f"crawled_data/deep_crawl/{timestamp}_depth{depth}_page{i+1}.txt"
        
        content = f"URL: {url}\n"
        content += f"Depth: {depth}\n"
        content += f"Score: {score:.2f}\n"
        content += f"Title: {title}\n"
        content += f"{'='*50}\n"
        content += content_body
        
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"\n💾 Results saved to: crawled_data/deep_crawl/{timestamp}_*")

def print_crawl_summary(successful_pages, failed_pages, pages_by_depth, start_time):
    """Print crawl summary statistics"""
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\n{'='*50}")
    print(f"📊 CRAWL SUMMARY")
    print(f"{'='*50}")
    print(f"⏱️  Duration: {duration:.2f} seconds")
    print(f"✅ Successful: {len(successful_pages)} pages")
    print(f"❌ Failed: {len(failed_pages)} pages")
    
    # Depth distribution
    print(f"\n📐 Pages by depth:")
    for depth in sorted(pages_by_depth.keys()):
        pages = pages_by_depth[depth]
        print(f"   Depth {depth}: {len(pages)} pages")
        
        # Show top scored pages at this depth
        if any(p.get('score', 0) > 0 for p in pages):
            top_pages = sorted(pages, key=lambda x: x.get('score', 0), reverse=True)[:3]
            for page in top_pages:
                if page.get('score', 0) > 0:
                    print(f"      → {page['title'][:50]}... (score: {page['score']:.2f})")
    
    # Failure analysis
    if failed_pages:
        print(f"\n❌ Failures by depth:")
        failure_by_depth = {}
        for failure in failed_pages:
            depth = failure['depth']
            failure_by_depth[depth] = failure_by_depth.get(depth, 0) + 1
        
        for depth, count in sorted(failure_by_depth.items()):
            print(f"   Depth {depth}: {count} failures")
    
    # Performance metrics
    if successful_pages:
        avg_time = duration / len(successful_pages)
        print(f"\n⚡ Performance: {avg_time:.2f} seconds/page average")

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
    
    parser = argparse.ArgumentParser(description="Browser profile crawler with deep crawling capabilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create profile command
    create_parser = subparsers.add_parser('create', help='Create a browser profile')
    create_parser.add_argument('name', help='Profile name')
    
    # Single page crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl a single page')
    crawl_parser.add_argument('url', help='URL to crawl')
    crawl_parser.add_argument('--profile', required=True, help='Profile name to use')
    
    # Deep crawl command
    deep_parser = subparsers.add_parser('deep-crawl', help='Deep crawl a website')
    deep_parser.add_argument('url', help='Starting URL')
    deep_parser.add_argument('--profile', help='Profile name to use (optional)')
    deep_parser.add_argument('--strategy', choices=['bfs', 'dfs', 'best-first'], 
                           default='bfs', help='Crawling strategy (default: bfs)')
    deep_parser.add_argument('--depth', type=int, default=2, 
                           help='Maximum crawl depth (default: 2)')
    deep_parser.add_argument('--max-pages', type=int, default=50,
                           help='Maximum pages to crawl (default: 50)')
    deep_parser.add_argument('--keywords', nargs='+',
                           help='Keywords for relevance scoring (best-first strategy)')
    deep_parser.add_argument('--patterns', nargs='+',
                           help='URL patterns to include (e.g., */docs/* */api/*)')
    deep_parser.add_argument('--no-domain-restrict', action='store_true',
                           help='Allow crawling external domains')
    deep_parser.add_argument('--batch', action='store_true',
                           help='Use batch mode instead of streaming')
    deep_parser.add_argument('--delay', type=float, default=0,
                           help='Delay between requests in seconds (default: 0)')
    
    # List profiles command
    list_parser = subparsers.add_parser('list', help='List all profiles')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        asyncio.run(create_profile(args.name))
    
    elif args.command == 'crawl':
        asyncio.run(crawl(args.url, args.profile))
    
    elif args.command == 'deep-crawl':
        asyncio.run(deep_crawl(
            url=args.url,
            profile_name=args.profile,
            strategy=args.strategy,
            max_depth=args.depth,
            max_pages=args.max_pages,
            keywords=args.keywords,
            patterns=args.patterns,
            domain_restrict=not args.no_domain_restrict,
            stream=not args.batch,
            delay=args.delay
        ))
    
    elif args.command == 'list':
        list_profiles()
    
    else:
        parser.print_help()