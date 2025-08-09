#!/usr/bin/env python3
"""
Simple Saudi Laws Crawler for Qanoniah.com
Extracts legal documents with authentication support
"""

import asyncio
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, BrowserProfiler, CacheMode


class SimpleSaudiCrawler:
    """Simple crawler for Saudi laws from Qanoniah.com"""
    
    def __init__(self, profile_name: str = "qanoniah"):
        self.profile_name = profile_name
        self.base_url = "https://qanoniah.com"
        self.output_dir = Path(__file__).parent / "qanoniah_documents"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_profile(self):
        """Create browser profile for authentication"""
        profiler = BrowserProfiler()
        print(f"\n🌐 Creating profile '{self.profile_name}'...")
        print("\n📋 Instructions:")
        print("  1. Browser will open to qanoniah.com")
        print("  2. Log in to your account")
        print("  3. Navigate to a document page")
        print("  4. Press 'q' in terminal to save profile")
        print("\n⏳ Opening browser...\n")
        
        profile_path = await profiler.create_profile(self.profile_name)
        
        if profile_path:
            print(f"\n✅ Profile saved: {profile_path}")
            return True
        else:
            print(f"\n❌ Failed to create profile")
            return False
    
    def get_browser_config(self):
        """Get browser configuration with authentication"""
        profiler = BrowserProfiler()
        profile_path = profiler.get_profile_path(self.profile_name)
        
        if not profile_path:
            print(f"❌ Profile '{self.profile_name}' not found. Run with 'create-profile' first.")
            return None
        
        return BrowserConfig(
            headless=False,
            user_data_dir=profile_path,
            use_managed_browser=True,
            browser_type="chromium"
        )
    
    def extract_document_links(self, html: str):
        """Extract document links with /File/{id} pattern"""
        soup = BeautifulSoup(html, 'html.parser')
        document_links = []
        
        # Find all links matching /File/ pattern
        file_pattern = re.compile(r'/File/[\w-]+')
        links = soup.find_all('a', href=file_pattern)
        
        for link in links:
            doc_url = urljoin(self.base_url, link.get('href'))
            doc_title = link.get_text(strip=True) or "Untitled"
            document_links.append((doc_url, doc_title))
        
        return document_links
    
    async def process_document(self, crawler, url: str, title: str, doc_number: int):
        """Process a single document"""
        print(f"\n[{doc_number}] Processing: {title[:60]}...")
        print(f"    URL: {url}")
        
        # Extract document ID from URL for folder name
        doc_id = re.search(r'/File/([\w-]+)', url)
        doc_id = doc_id.group(1) if doc_id else f"doc_{doc_number}"
        doc_folder = self.output_dir / doc_id
        doc_folder.mkdir(exist_ok=True)
        
        # JavaScript to click Reading Mode button
        js_click_reading = """
        (async function() {
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Find Reading Mode button
            const buttons = document.querySelectorAll('button');
            const readingButton = Array.from(buttons).find(btn => {
                const text = (btn.textContent || '').toLowerCase();
                return text.includes('reading') && text.includes('mode');
            });
            
            if (readingButton) {
                readingButton.click();
                await new Promise(resolve => setTimeout(resolve, 5000));
                return { clicked: true };
            }
            
            return { clicked: false };
        })();
        """
        
        config = CrawlerRunConfig(
            page_timeout=15000,
            delay_before_return_html=2.0,
            js_code=js_click_reading,
            wait_until="domcontentloaded",
            cache_mode=CacheMode.BYPASS,
            scan_full_page=True,
            verbose=False
        )
        
        try:
            result = await crawler.arun(url, config=config)
            
            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Extract content
                content = soup.get_text(separator='\n', strip=True)
                
                # Save as markdown
                md_file = doc_folder / "content.md"
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"**Source URL**: {url}\n")
                    f.write(f"**Extracted**: {datetime.now().isoformat()}\n\n")
                    f.write("---\n\n")
                    f.write(content)
                
                print(f"    ✅ Saved to: {doc_folder.name}/content.md")
                return True
            else:
                print(f"    ❌ Failed to load page")
                return False
                
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            return False
    
    async def crawl(self, max_documents: int = 10):
        """Main crawl function"""
        browser_config = self.get_browser_config()
        if not browser_config:
            return
        
        # Starting URL for Laws/Regulations section
        start_url = "https://qanoniah.com/en/Search?type=all&page=1&main=O4NEx2DAnjroaD795zM0BKV83"
        
        print(f"\n🚀 Starting crawler")
        print(f"📄 Max documents: {max_documents}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🌍 Starting URL: {start_url}\n")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Load search page
            print("📄 Loading search page...")
            
            # JavaScript to wait for content and find links
            js_find_links = """
            (async function() {
                // Wait for dynamic content to load
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Find all links
                const links = document.querySelectorAll('a[href]');
                const fileLinks = [];
                
                links.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href && href.includes('/File/')) {
                        fileLinks.push({
                            url: href,
                            text: link.textContent.trim()
                        });
                    }
                });
                
                // Also try to find links in Vue components
                const vueLinks = document.querySelectorAll('[data-v-] a');
                vueLinks.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href && href.includes('/File/')) {
                        fileLinks.push({
                            url: href,
                            text: link.textContent.trim()
                        });
                    }
                });
                
                return {
                    fileLinksCount: fileLinks.length,
                    fileLinks: fileLinks.slice(0, 5), // First 5 for debugging
                    totalLinks: links.length,
                    pageTitle: document.title
                };
            })();
            """
            
            config = CrawlerRunConfig(
                page_timeout=30000,
                delay_before_return_html=2.0,
                js_code=js_find_links,
                wait_until="domcontentloaded",
                cache_mode=CacheMode.BYPASS,
                verbose=False
            )
            
            try:
                result = await crawler.arun(start_url, config=config)
                
                if result.success:
                    # Save HTML for debugging
                    debug_file = self.output_dir / "debug_search_page.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(result.html)
                    print(f"   Debug: Saved search page HTML to {debug_file.name}")
                    
                    # Check JavaScript results
                    if hasattr(result, 'js_execution_result') and result.js_execution_result:
                        js_result = result.js_execution_result
                        print(f"   Debug: Page title: {js_result.get('pageTitle', 'Unknown')}")
                        print(f"   Debug: Total links on page: {js_result.get('totalLinks', 0)}")
                        print(f"   Debug: File links found by JS: {js_result.get('fileLinksCount', 0)}")
                        if js_result.get('fileLinks'):
                            print("   Debug: Sample links:")
                            for link in js_result['fileLinks'][:3]:
                                print(f"     - {link['text'][:50]}: {link['url']}")
                    
                    # Extract document links
                    document_links = self.extract_document_links(result.html)
                    print(f"✅ Found {len(document_links)} documents\n")
                    
                    # Process documents up to max_documents
                    documents_to_process = min(len(document_links), max_documents)
                    successful = 0
                    
                    for i, (doc_url, doc_title) in enumerate(document_links[:documents_to_process], 1):
                        success = await self.process_document(
                            crawler, doc_url, doc_title, i
                        )
                        if success:
                            successful += 1
                        
                        # Small delay between documents
                        if i < documents_to_process:
                            await asyncio.sleep(2)
                    
                    print(f"\n✅ Crawl complete!")
                    print(f"   Processed: {successful}/{documents_to_process} documents")
                    print(f"   Output: {self.output_dir}")
                    
                else:
                    print(f"❌ Failed to load search page: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                    
            except Exception as e:
                print(f"❌ Error during crawl: {str(e)}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Saudi Laws Crawler")
    parser.add_argument('command', nargs='?', default='crawl', 
                       choices=['crawl', 'create-profile'],
                       help='Command to run (default: crawl)')
    parser.add_argument('--max-documents', type=int, default=10,
                       help='Maximum documents to process (default: 10)')
    
    args = parser.parse_args()
    
    crawler = SimpleSaudiCrawler()
    
    if args.command == 'create-profile':
        await crawler.create_profile()
    else:  # crawl
        await crawler.crawl(max_documents=args.max_documents)


if __name__ == "__main__":
    asyncio.run(main())