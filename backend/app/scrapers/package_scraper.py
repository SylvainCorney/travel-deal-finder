from app.scrapers.base_scraper import BaseScraper
from typing import List, Dict
import random
import asyncio


class MultiSitePackageScraper(BaseScraper):
    """
    Multi-site package scraper for Canadian travel sites
    Supports: Sunwing, Air Transat, TripVoyage, VoyagesARabais, Bergeron, TripCentral, etc.
    """
    
    def __init__(self, site: str = "all"):
        super().__init__()
        self.site = site
        
        # Define all supported sites
        self.sites = {
            "sunwing": {
                "url": "https://www.sunwing.ca/vacations",
                "name": "Sunwing",
                "scraper": self._scrape_sunwing
            },
            "airtransat": {
                "url": "https://www.airtransat.com/en-CA/vacations",
                "name": "Air Transat",
                "scraper": self._scrape_airtransat
            },
            "tripvoyage": {
                "url": "https://www.tripvoyage.ca/",
                "name": "TripVoyage",
                "scraper": self._scrape_tripvoyage
            },
            "voyagesarabais": {
                "url": "https://voyagesarabais.com/",
                "name": "Voyages à Rabais",
                "scraper": self._scrape_voyagesarabais
            },
            "bergeron": {
                "url": "https://www.voyagesbergeron.com/",
                "name": "Voyages Bergeron",
                "scraper": self._scrape_bergeron
            },
            "destination": {
                "url": "https://www.voyagesdestination.com/",
                "name": "Voyages Destination",
                "scraper": self._scrape_destination
            },
            "tripcentral": {
                "url": "https://www.tripcentral.ca",
                "name": "Trip Central",
                "scraper": self._scrape_tripcentral
            },
            "kayak": {
                "url": "https://www.ca.kayak.com/",
                "name": "KAYAK",
                "scraper": self._scrape_kayak
            },
        }
    
    async def setup(self, headless: bool = True):
        """Enhanced setup with anti-detection measures"""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        
        # Use stealth mode settings
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Random but realistic viewport sizes
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
        ]
        
        context = await self.browser.new_context(
            user_agent=self.user_agent.random,
            viewport=random.choice(viewports),
            locale='en-CA',
            timezone_id='America/Toronto',
            # Add extra headers to look more human
            extra_http_headers={
                'Accept-Language': 'en-CA,en-US;q=0.9,en;q=0.8,fr;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        self.page = await context.new_page()
        
        # Inject anti-detection scripts
        await self.page.add_init_script("""
            // Overwrite the `plugins` property to use a custom getter.
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Overwrite the `plugins` property to use a custom getter.
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Overwrite the `languages` property to use a custom getter.
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-CA', 'en-US', 'en', 'fr'],
            });
            
            // Pass the Chrome Test
            window.chrome = {
                runtime: {},
            };
        """)
        
        # Only block certain resources, not all images (some sites need them)
        await self.page.route("**/*.{woff,woff2,ttf}", lambda route: route.abort())
    
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """Scrape deals from multiple sites"""
        all_deals = []
        target_hotels = search_params.get('hotels', [])
        sources = search_params.get('sources', [])
        
        # Determine which sites to scrape
        sites_to_scrape = []
        if self.site == "all":
            # Prioritize Canadian package sites for all-inclusive
            if 'all_inclusive' in sources or 'packages' in sources:
                sites_to_scrape = ["sunwing", "airtransat", "tripvoyage", "voyagesarabais", 
                                   "bergeron", "destination", "tripcentral"]
        else:
            sites_to_scrape = [self.site]
        
        # Scrape each site with delays between requests
        for site_key in sites_to_scrape:
            if site_key in self.sites:
                try:
                    site_deals = await self.sites[site_key]["scraper"](search_params)
                    all_deals.extend(site_deals)
                    
                    # Random delay between sites to avoid rate limiting
                    await self.random_delay(2000, 5000)
                    
                except Exception as e:
                    print(f"Error scraping {self.sites[site_key]['name']}: {e}")
                    continue
        
        # Filter by specific hotels if provided
        if target_hotels:
            all_deals = [d for d in all_deals if any(hotel.lower() in d.get('hotel_name', '').lower() 
                                                      for hotel in target_hotels)]
        
        return all_deals
    
    # ============= SITE-SPECIFIC SCRAPERS =============
    
    async def _scrape_sunwing(self, search_params: Dict) -> List[Dict]:
        """Scrape Sunwing packages"""
        # For now, return demo data
        # TODO: Implement actual scraping when ready
        return await self._generate_sunwing_demo_data(search_params)
    
    async def _scrape_airtransat(self, search_params: Dict) -> List[Dict]:
        """Scrape Air Transat packages"""
        # For now, return demo data
        # TODO: Implement actual scraping when ready
        return await self._generate_airtransat_demo_data(search_params)
    
    async def _scrape_tripvoyage(self, search_params: Dict) -> List[Dict]:
        """Scrape TripVoyage packages"""
        # TODO: Implement actual scraping
        return []
    
    async def _scrape_voyagesarabais(self, search_params: Dict) -> List[Dict]:
        """Scrape Voyages à Rabais packages"""
        # TODO: Implement actual scraping
        return []
    
    async def _scrape_bergeron(self, search_params: Dict) -> List[Dict]:
        """Scrape Voyages Bergeron packages"""
        # TODO: Implement actual scraping
        return []
    
    async def _scrape_destination(self, search_params: Dict) -> List[Dict]:
        """Scrape Voyages Destination packages"""
        # TODO: Implement actual scraping
        return []
    
    async def _scrape_tripcentral(self, search_params: Dict) -> List[Dict]:
        """Scrape Trip Central packages"""
        # TODO: Implement actual scraping
        return []
    
    async def _scrape_kayak(self, search_params: Dict) -> List[Dict]:
        """Scrape KAYAK packages"""
        # TODO: Implement actual scraping
        return []
    
    # ============= DEMO DATA GENERATORS =============
    
    async def _generate_sunwing_demo_data(self, search_params: Dict) -> List[Dict]:
        """Generate demo Sunwing package data"""
        destination = search_params.get('location', 'Cancun')
        
        packages = [
            {
                'hotel_name': 'Riu Palace Peninsula',
                'hotel_rating': 8.9,
                'base_price': 2850,
                'room_type': 'Junior Suite Ocean View',
            },
            {
                'hotel_name': 'Breathless Riviera Cancun',
                'hotel_rating': 8.7,
                'base_price': 2915,
                'room_type': 'Xhale Club Master Suite',
            },
            {
                'hotel_name': 'Riu Dunamar',
                'hotel_rating': 8.6,
                'base_price': 2650,
                'room_type': 'Junior Suite',
            },
        ]
        
        deals = []
        for pkg in packages:
            price_variation = random.randint(-200, 300)
            hotel_slug = pkg['hotel_name'].lower().replace(' ', '-')
            
            deal = {
                'deal_type': 'all_inclusive',
                'name': f"{pkg['hotel_name']} - All-Inclusive",
                'hotel_name': pkg['hotel_name'],
                'hotel_rating': pkg['hotel_rating'],
                'room_type': pkg['room_type'],
                'airline': 'Sunwing/Air Transat',
                'price': pkg['base_price'] + price_variation,
                'currency': 'CAD',
                'meal_plan': 'All-Inclusive',
                'includes_flight': True,
                'includes_hotel': True,
                'includes_transfer': True,
                'includes_meals': True,
                'check_in_date': search_params.get('check_in_date'),
                'check_out_date': search_params.get('check_out_date'),
                'location': destination,
                'url': f"https://www.sunwing.ca/vacations/package/{hotel_slug}-cancun",
                'source': 'Sunwing (Demo)',
                'departure_time': '07:30 AM',
                'arrival_time': '12:00 PM',
            }
            deals.append(deal)
        
        return deals
    
    async def _generate_airtransat_demo_data(self, search_params: Dict) -> List[Dict]:
        """Generate demo Air Transat package data"""
        destination = search_params.get('location', 'Cancun')
        
        packages = [
            {
                'hotel_name': 'Excellence Playa Mujeres',
                'hotel_rating': 9.2,
                'base_price': 3400,
                'room_type': 'Excellence Club Suite',
            },
            {
                'hotel_name': 'Atelier Playa Mujeres',
                'hotel_rating': 9.0,
                'base_price': 3100,
                'room_type': 'Rooftop Terrace Suite',
            },
        ]
        
        deals = []
        for pkg in packages:
            price_variation = random.randint(-200, 300)
            hotel_slug = pkg['hotel_name'].lower().replace(' ', '-')
            
            deal = {
                'deal_type': 'all_inclusive',
                'name': f"{pkg['hotel_name']} - All-Inclusive",
                'hotel_name': pkg['hotel_name'],
                'hotel_rating': pkg['hotel_rating'],
                'room_type': pkg['room_type'],
                'airline': 'Air Transat',
                'price': pkg['base_price'] + price_variation,
                'currency': 'CAD',
                'meal_plan': 'All-Inclusive',
                'includes_flight': True,
                'includes_hotel': True,
                'includes_transfer': True,
                'includes_meals': True,
                'check_in_date': search_params.get('check_in_date'),
                'check_out_date': search_params.get('check_out_date'),
                'location': destination,
                'url': f"https://www.airtransat.com/en-CA/vacations/hotel/{hotel_slug}",
                'source': 'Air Transat (Demo)',
                'departure_time': '08:00 AM',
                'arrival_time': '12:30 PM',
            }
            deals.append(deal)
        
        return deals


class PackageScraperFactory:
    """Factory to create package scrapers"""
    
    @staticmethod
    def create_scraper(source: str = "all") -> BaseScraper:
        """
        Create appropriate scraper based on source
        
        Args:
            source: "all", "sunwing", "airtransat", "tripvoyage", etc.
        """
        return MultiSitePackageScraper(site=source)
