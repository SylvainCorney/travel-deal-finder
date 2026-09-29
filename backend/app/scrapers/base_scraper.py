from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, Browser
from typing import List, Dict
import asyncio
from fake_useragent import UserAgent


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
        self.user_agent = UserAgent()
    
    async def setup(self, headless: bool = True):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        context = await self.browser.new_context(
            user_agent=self.user_agent.random,
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()
        
        # Block images and unnecessary resources for faster scraping
        await self.page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", 
                             lambda route: route.abort())
    
    async def cleanup(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    async def random_delay(self, min_ms: int = 1000, max_ms: int = 3000):
        """Add random delay to mimic human behavior"""
        import random
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    @abstractmethod
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """
        Scrape deals based on search parameters
        Must be implemented by child classes
        """
        pass
    
    async def safe_scrape(self, search_params: Dict) -> List[Dict]:
        """Wrapper with error handling"""
        try:
            await self.setup()
            results = await self.scrape(search_params)
            return results
        except Exception as e:
            print(f"Scraping error: {str(e)}")
            return []
        finally:
            await self.cleanup()
