#!/usr/bin/env python3
"""
Ultra-simple browser profile crawler
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, BrowserProfiler, CacheMode

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
    if len(sys.argv) < 2:
        print("Usage:\n  --create NAME\n  --crawl URL --profile NAME\n  --list")
        sys.exit(1)
    
    if sys.argv[1] == "--create" and len(sys.argv) == 3:
        asyncio.run(create_profile(sys.argv[2]))
    
    elif sys.argv[1] == "--crawl" and len(sys.argv) == 5 and sys.argv[3] == "--profile":
        asyncio.run(crawl(sys.argv[2], sys.argv[4]))
    
    elif sys.argv[1] == "--list":
        list_profiles()
    
    elif sys.argv[1] == "--verify" and len(sys.argv) >= 3:
        print("Verify command not implemented yet.")
    
    else:
        print("Invalid command. See usage.")