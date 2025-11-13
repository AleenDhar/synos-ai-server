"""
Browser Research Tool for DeepAgents
Performs web research with visible browser automation and markdown extraction
ASYNC VERSION - Works with DeepAgents async server
"""

from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import random
import json
import os
from datetime import datetime
from markdownify import markdownify as md
from bs4 import BeautifulSoup


class BrowserResearchTool:
    """Manages browser sessions and research operations"""
    
    def __init__(self):
        self.session_file = "browser_session.json"
        self.output_dir = "research_output"
        
    def clean_html_for_markdown(self, html: str) -> str:
        """Clean HTML before converting to markdown"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
            tag.decompose()
        
        # Remove common ad and tracking elements
        for element in soup.select('.advertisement, .ad, .ads, .sidebar, .cookie-banner, .popup, .modal'):
            element.decompose()
        
        # Remove elements by common class patterns
        for element in soup.find_all(class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['ad-', 'ads-', 'advertisement', 'promo', 'sponsored']
        )):
            element.decompose()
        
        return str(soup)
    
    def convert_to_markdown(self, html: str, url: str, title: str) -> str:
        """Convert HTML to clean markdown"""
        cleaned_html = self.clean_html_for_markdown(html)
        
        markdown = md(
            cleaned_html,
            heading_style='ATX',
            bullets='-',
            code_language_callback=lambda el: el.get('class', [''])[0].replace('language-', '') if el.has_attr('class') else None,
            strip=['span', 'font', 'div']
        )
        
        # Add metadata header
        header = f"""# {title}

**URL:** {url}
**Extracted:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
        return header + markdown
    
    async def save_session(self, context) -> str:
        """Save browser session state"""
        try:
            await context.storage_state(path=self.session_file)
            return f"Session saved to {self.session_file}"
        except Exception as e:
            return f"Error saving session: {str(e)}"
    
    async def scrape_with_browser(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000,
        use_session: bool = False,
        rate_limit_delay: float = 2.0,
        headless: bool = False
    ) -> Dict[str, Any]:
        """Scrape a single page with browser (visible or headless)"""
        
        async with async_playwright() as p:
            # Launch browser with configurable headless mode
            browser = await p.chromium.launch(
                headless=headless,  # Configurable: False = visible, True = headless
                slow_mo=0 if headless else 500  # Fast in headless, slow in visible mode
            )
            
            # Create context with or without session
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            if use_session:
                try:
                    if os.path.exists(self.session_file):
                        context_options['storage_state'] = self.session_file
                except Exception as e:
                    print(f"Could not load session: {e}")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            try:
                # Navigate to page
                print(f"Navigating to: {url}")
                response = await page.goto(url, timeout=timeout, wait_until='networkidle')
                
                if not response:
                    return {
                        'success': False,
                        'error': 'No response received',
                        'url': url
                    }
                
                if response.status >= 400:
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}',
                        'url': url
                    }
                
                # Wait for specific selector if provided
                if wait_for_selector:
                    print(f"Waiting for selector: {wait_for_selector}")
                    await page.wait_for_selector(wait_for_selector, timeout=timeout)
                
                # Add small delay to ensure page is fully loaded
                await asyncio.sleep(2)
                
                # Extract content
                title = await page.title()
                html = await page.content()
                final_url = page.url
                
                # Convert to markdown
                markdown = self.convert_to_markdown(html, final_url, title)
                
                # Save to file
                os.makedirs(self.output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
                filename = f"{self.output_dir}/{timestamp}_{safe_title}.md"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
                # Rate limiting
                if rate_limit_delay > 0:
                    delay = rate_limit_delay + random.uniform(0, 1)
                    print(f"Rate limiting: waiting {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                
                return {
                    'success': True,
                    'url': final_url,
                    'title': title,
                    'markdown': markdown,
                    'filename': filename,
                    'length': len(markdown)
                }
                
            except PlaywrightTimeoutError:
                return {
                    'success': False,
                    'error': 'Page load timeout',
                    'url': url
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'url': url
                }
            finally:
                # Keep browser open for a moment to see results
                await asyncio.sleep(2)
                await browser.close()


# Initialize the tool
_browser_tool = BrowserResearchTool()


@tool
async def browser_research(
    url: str,
    wait_for_selector: Optional[str] = None,
    use_session: bool = False,
    headless: bool = False
) -> str:
    """
    Research a website using browser automation and extract content as markdown.
    
    Args:
        url: The URL to visit and extract content from
        wait_for_selector: Optional CSS selector to wait for before extracting (e.g., ".main-content", "#article")
        use_session: Whether to use saved browser session for authenticated content
        headless: Whether to run browser in headless mode (True) or visible mode (False)
    
    Returns:
        Extracted content in markdown format with metadata
    """
    result = await _browser_tool.scrape_with_browser(
        url=url,
        wait_for_selector=wait_for_selector,
        use_session=use_session,
        headless=headless
    )
    
    if result['success']:
        return f"""Successfully extracted content from: {result['title']}

URL: {result['url']}
Saved to: {result['filename']}
Content length: {result['length']} characters

Preview:
{result['markdown'][:1000]}...

Full content saved to file for detailed analysis."""
    else:
        return f"Error extracting from {url}: {result['error']}"


@tool
async def browser_research_multiple(
    urls: List[str],
    wait_for_selector: Optional[str] = None,
    use_session: bool = False,
    rate_limit_delay: float = 3.0,
    headless: bool = False
) -> str:
    """
    Research multiple websites using browser automation.
    
    Args:
        urls: List of URLs to visit and extract content from
        wait_for_selector: Optional CSS selector to wait for on each page
        use_session: Whether to use saved browser session
        rate_limit_delay: Delay between requests in seconds (default: 3.0)
        headless: Whether to run browser in headless mode (True) or visible mode (False)
    
    Returns:
        Summary of all extracted content
    """
    results = []
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls):
        print(f"\n--- Processing {i+1}/{len(urls)}: {url} ---")
        
        result = await _browser_tool.scrape_with_browser(
            url=url,
            wait_for_selector=wait_for_selector,
            use_session=use_session,
            rate_limit_delay=rate_limit_delay if i < len(urls) - 1 else 0,
            headless=headless
        )
        
        results.append(result)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
    
    # Create summary
    summary = f"""Browser Research Complete
========================

Total URLs: {len(urls)}
Successful: {successful}
Failed: {failed}

Results:
"""
    
    for i, result in enumerate(results, 1):
        if result['success']:
            summary += f"\n{i}. ✓ {result['title']}"
            summary += f"\n   URL: {result['url']}"
            summary += f"\n   Saved: {result['filename']}"
            summary += f"\n   Length: {result['length']} characters"
        else:
            summary += f"\n{i}. ✗ {result['url']}"
            summary += f"\n   Error: {result['error']}"
    
    return summary


@tool
async def save_browser_session() -> str:
    """
    Save current browser session for reuse with authenticated content.
    Opens a browser for you to manually log in to a website.
    After login, the session is saved for future automated access.
    
    Returns:
        Status message about session save
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("MANUAL LOGIN SESSION")
        print("="*60)
        print("\nInstructions:")
        print("1. A browser window will open")
        print("2. Navigate to the website you want to log in to")
        print("3. Complete the login process")
        print("4. When done, close the browser window")
        print("5. The session will be saved automatically")
        print("\n" + "="*60 + "\n")
        
        # Navigate to a neutral page
        await page.goto("https://www.google.com")
        
        # Wait for user to complete login and close browser
        try:
            # This will keep browser open until manually closed
            await page.wait_for_timeout(300000)  # 5 minutes max
        except:
            pass
        
        # Save session before closing
        result = await _browser_tool.save_session(context)
        await browser.close()
        
        return result


@tool
async def browser_interactive_research(
    initial_url: str,
    task_description: str,
    manual_interaction_time: int = 60
) -> str:
    """
    Open a browser for interactive research where you can see and control the browser.
    Useful for complex sites requiring navigation, form filling, or interaction.
    
    Args:
        initial_url: Starting URL to load
        task_description: Description of what research to perform
        manual_interaction_time: How long to keep browser open for interaction (seconds)
    
    Returns:
        Extracted content after interaction period
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print(f"\n{'='*60}")
        print(f"INTERACTIVE RESEARCH SESSION")
        print(f"{'='*60}")
        print(f"Task: {task_description}")
        print(f"Starting URL: {initial_url}")
        print(f"Browser will stay open for {manual_interaction_time} seconds")
        print(f"Navigate, click, and interact as needed")
        print(f"{'='*60}\n")
        
        try:
            # Load initial page
            await page.goto(initial_url, wait_until='networkidle')
            
            # Wait for manual interaction
            await asyncio.sleep(manual_interaction_time)
            
            # Extract final content
            title = await page.title()
            html = await page.content()
            final_url = page.url
            
            # Convert to markdown
            markdown = _browser_tool.convert_to_markdown(html, final_url, title)
            
            # Save
            os.makedirs(_browser_tool.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{_browser_tool.output_dir}/{timestamp}_interactive.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            return f"""Interactive Research Complete

Task: {task_description}
Final URL: {final_url}
Title: {title}
Saved to: {filename}

Content preview:
{markdown[:1000]}...
"""
        
        except Exception as e:
            return f"Error during interactive research: {str(e)}"
        finally:
            await browser.close()