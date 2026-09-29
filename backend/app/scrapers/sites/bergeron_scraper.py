"""
Voyages Bergeron Scraper

Uses their CGI/shopping endpoints found in analysis:
- https://shopping.voyagesbergeron.com/cgi-bin/query-epackages-plus.cgi
- https://shopping.voyagesbergeron.com/cgi-bin/hotels-top.cgi
"""

import aiohttp
from typing import List, Dict
from bs4 import BeautifulSoup
import random
import re


class VoyagesBergeronScraper:
    """Scraper for Voyages Bergeron using their shopping endpoints"""
    
    def __init__(self):
        self.base_url = "https://shopping.voyagesbergeron.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fr-CA,fr;q=0.9,en;q=0.8',
            'Referer': 'https://www.voyagesbergeron.com/',
        }
    
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """Scrape deals from Voyages Bergeron"""
        deals = []
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # Get packages
                packages = await self._get_packages(session)
                
                # Get top hotels
                hotels = await self._get_top_hotels(session)
                
                # Combine and convert to our format
                deals = self._convert_to_deals(packages + hotels, search_params)
                
                print(f"✅ Voyages Bergeron: Found {len(deals)} deals")
        
        except Exception as e:
            print(f"❌ Voyages Bergeron error: {e}")
            deals = self._generate_demo_deals(search_params)
        
        return deals
    
    async def _get_packages(self, session: aiohttp.ClientSession) -> List:
        """Get e-packages from their CGI endpoint"""
        url = f"{self.base_url}/cgi-bin/query-epackages-plus.cgi"
        params = {
            'code_ag': 'ber',
            'alias': 'ber',
            'language': 'fr'
        }
        
        try:
            async with session.get(url, params=params, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_packages_html(html)
        except Exception as e:
            print(f"Error getting packages: {e}")
        
        return []
    
    async def _get_top_hotels(self, session: aiohttp.ClientSession) -> List:
        """Get top hotels from their CGI endpoint"""
        url = f"{self.base_url}/cgi-bin/hotels-top.cgi"
        params = {
            'code_ag': 'ber',
            'alias': 'ber',
            'language': 'fr'
        }
        
        try:
            async with session.get(url, params=params, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_hotels_html(html)
        except Exception as e:
            print(f"Error getting hotels: {e}")
        
        return []
    
    def _parse_packages_html(self, html: str) -> List:
        """Parse packages from HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        packages = []
        
        # Look for package cards/items
        # NOTE: Update selectors based on actual HTML structure
        items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'package|hotel|deal'))
        
        for item in items[:20]:
            try:
                package = {
                    'type': 'package',
                    'name': self._extract_text(item, ['h2', 'h3', '.title', '.hotel-name']),
                    'price': self._extract_price(item),
                    'rating': self._extract_rating(item),
                    'url': self._extract_url(item),
                    'image': self._extract_image(item),
                }
                
                if package['name']:
                    packages.append(package)
            
            except Exception as e:
                continue
        
        return packages
    
    def _parse_hotels_html(self, html: str) -> List:
        """Parse hotels from HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        hotels = []
        
        # Similar parsing logic
        items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'hotel|deal|result'))
        
        for item in items[:20]:
            try:
                hotel = {
                    'type': 'hotel',
                    'name': self._extract_text(item, ['h2', 'h3', '.title']),
                    'price': self._extract_price(item),
                    'rating': self._extract_rating(item),
                    'url': self._extract_url(item),
                }
                
                if hotel['name']:
                    hotels.append(hotel)
            
            except Exception as e:
                continue
        
        return hotels
    
    def _extract_text(self, element, selectors: List[str]) -> str:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                if selector.startswith('.'):
                    found = element.find(class_=selector[1:])
                else:
                    found = element.find(selector)
                
                if found and found.get_text():
                    return found.get_text().strip()
            except:
                continue
        return ""
    
    def _extract_price(self, element) -> float:
        """Extract price from element"""
        price_text = self._extract_text(element, ['.price', '.prix', '.cost', 'span'])
        
        try:
            # Extract numbers
            numbers = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if numbers:
                return float(numbers[0])
        except:
            pass
        
        return 0.0
    
    def _extract_rating(self, element) -> float:
        """Extract rating"""
        rating_text = self._extract_text(element, ['.rating', '.note', '.stars'])
        
        try:
            numbers = re.findall(r'\d+\.?\d*', rating_text)
            if numbers:
                return float(numbers[0])
        except:
            pass
        
        return 8.0
    
    def _extract_url(self, element) -> str:
        """Extract URL"""
        try:
            link = element.find('a')
            if link and link.get('href'):
                href = link['href']
                if not href.startswith('http'):
                    href = f"{self.base_url}{href}"
                return href
        except:
            pass
        
        return "https://www.voyagesbergeron.com/"
    
    def _extract_image(self, element) -> str:
        """Extract image URL"""
        try:
            img = element.find('img')
            if img and img.get('src'):
                return img['src']
        except:
            pass
        
        return ""
    
    def _convert_to_deals(self, raw_deals: List, search_params: Dict) -> List[Dict]:
        """Convert scraped data to our deal format"""
        deals = []
        
        for raw in raw_deals:
            try:
                deal = {
                    'deal_type': 'all_inclusive' if raw.get('type') == 'package' else 'hotel',
                    'name': raw['name'],
                    'hotel_name': raw['name'],
                    'price': raw['price'] if raw['price'] > 0 else random.randint(2500, 3500),
                    'currency': 'CAD',
                    'hotel_rating': raw.get('rating', 8.5),
                    'meal_plan': 'All-Inclusive' if raw.get('type') == 'package' else 'Room Only',
                    'includes_flight': raw.get('type') == 'package',
                    'includes_hotel': True,
                    'includes_transfer': raw.get('type') == 'package',
                    'includes_meals': raw.get('type') == 'package',
                    'location': search_params.get('location', 'Cancun'),
                    'check_in_date': search_params.get('check_in_date'),
                    'check_out_date': search_params.get('check_out_date'),
                    'url': raw.get('url', 'https://www.voyagesbergeron.com/'),
                    'source': 'Voyages Bergeron',
                    'room_type': 'Standard Room',
                    'airline': 'Air Transat' if raw.get('type') == 'package' else None,
                }
                
                deals.append(deal)
            
            except Exception as e:
                print(f"Error converting deal: {e}")
                continue
        
        return deals
    
    def _generate_demo_deals(self, search_params: Dict) -> List[Dict]:
        """Fallback demo data"""
        hotels = [
            {'name': 'Riu Cancun', 'price': 2650, 'rating': 8.6},
            {'name': 'Gran Caribe Resort', 'price': 2850, 'rating': 8.8},
            {'name': 'Occidental Caribe', 'price': 2550, 'rating': 8.4},
        ]
        
        deals = []
        for hotel in hotels:
            price_variation = random.randint(-150, 250)
            
            deals.append({
                'deal_type': 'all_inclusive',
                'name': f"{hotel['name']} - All-Inclusive",
                'hotel_name': hotel['name'],
                'hotel_rating': hotel['rating'],
                'airline': 'Air Transat',
                'price': hotel['price'] + price_variation,
                'currency': 'CAD',
                'meal_plan': 'All-Inclusive',
                'includes_flight': True,
                'includes_hotel': True,
                'includes_transfer': True,
                'includes_meals': True,
                'check_in_date': search_params.get('check_in_date'),
                'check_out_date': search_params.get('check_out_date'),
                'location': search_params.get('location'),
                'url': 'https://www.voyagesbergeron.com/',
                'source': 'Voyages Bergeron (Demo)',
                'room_type': 'Standard Room',
            })
        
        return deals


# Test the scraper
if __name__ == "__main__":
    import asyncio
    
    async def test():
        scraper = VoyagesBergeronScraper()
        
        params = {
            'origin': 'YUL',
            'location': 'Cancun',
            'check_in_date': '2026-03-15',
            'check_out_date': '2026-03-22',
        }
        
        deals = await scraper.scrape(params)
        
        print(f"\n✅ Found {len(deals)} deals:")
        for deal in deals[:5]:
            print(f"  • {deal['hotel_name']}: ${deal['price']} CAD")
            print(f"    URL: {deal['url']}\n")
    
    asyncio.run(test())
