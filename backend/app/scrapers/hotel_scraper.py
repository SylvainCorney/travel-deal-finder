from app.scrapers.base_scraper import BaseScraper
from typing import List, Dict
import re
import random


class HotelScraper(BaseScraper):
    """
    Hotel scraper - Demonstration with Booking.com structure
    NOTE: This is a template - actual selectors need to be updated based on target sites
    """
    
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """
        Scrape hotel deals
        
        search_params should contain:
        - location: str
        - check_in_date: str (YYYY-MM-DD)
        - check_out_date: str (YYYY-MM-DD)
        - hotels: List[str] (optional - specific hotel names)
        """
        location = search_params.get('location', '')
        check_in = search_params.get('check_in_date', '')
        check_out = search_params.get('check_out_date', '')
        target_hotels = search_params.get('hotels', [])
        
        # For demo purposes, generate sample hotel data
        deals = await self._scrape_demo_hotels(search_params)
        
        # Filter by specific hotels if provided
        if target_hotels:
            deals = [d for d in deals if any(hotel.lower() in d['hotel_name'].lower() for hotel in target_hotels)]
        
        return deals
    
    async def _scrape_demo_hotels(self, search_params: Dict) -> List[Dict]:
        """Generate demo hotel data"""
        location = search_params.get('location', 'Cancun')
        
        demo_hotels = [
            {
                'name': 'Grand Fiesta Americana Coral Beach',
                'base_price': 320,
                'rating': 9.1,
                'room_type': 'Deluxe Ocean View',
            },
            {
                'name': 'Nizuc Resort & Spa',
                'base_price': 580,
                'rating': 9.4,
                'room_type': 'Garden Pool Suite',
            },
            {
                'name': 'Marriott Cancun Resort',
                'base_price': 245,
                'rating': 8.3,
                'room_type': 'Ocean View Room',
            },
            {
                'name': 'JW Marriott Cancun',
                'base_price': 395,
                'rating': 8.9,
                'room_type': 'Deluxe Ocean Front',
            },
            {
                'name': 'Fiesta Americana Condesa',
                'base_price': 280,
                'rating': 8.5,
                'room_type': 'Superior Ocean View',
            },
            {
                'name': 'Live Aqua Beach Resort',
                'base_price': 425,
                'rating': 9.0,
                'room_type': 'Premium Room',
            },
            {
                'name': 'Paradisus Cancun',
                'base_price': 360,
                'rating': 8.7,
                'room_type': 'Junior Suite',
            },
            {
                'name': 'Dreams Sands Cancun',
                'base_price': 315,
                'rating': 8.4,
                'room_type': 'Preferred Club Ocean View',
            },
        ]
        
        deals = []
        for hotel in demo_hotels:
            price_variation = random.randint(-50, 100)
            
            # Create unique URL for each hotel
            hotel_slug = hotel['name'].lower().replace(' ', '-')
            url = f"https://www.booking.com/hotel/mx/{hotel_slug}.html"
            
            deal = {
                'deal_type': 'hotel',
                'name': hotel['name'],
                'hotel_name': hotel['name'],
                'price': hotel['base_price'] + price_variation,
                'currency': 'USD',
                'hotel_rating': hotel['rating'],
                'location': location,
                'check_in_date': search_params.get('check_in_date'),
                'check_out_date': search_params.get('check_out_date'),
                'url': url,
                'source': 'Booking.com (Demo)',
                'room_type': hotel['room_type'],
            }
            deals.append(deal)
        
        return deals
    
    def _build_booking_url(self, location: str, check_in: str, check_out: str) -> str:
        """Build Booking.com search URL"""
        # Simplified URL construction - adjust as needed
        base_url = "https://www.booking.com/searchresults.html"
        params = f"?ss={location.replace(' ', '+')}&checkin={check_in}&checkout={check_out}"
        return base_url + params
    
    async def _extract_hotel_data(self, card, search_params: Dict) -> Dict:
        """Extract data from a hotel card element"""
        try:
            # These selectors are examples - update based on actual site structure
            name_elem = await card.query_selector('[data-testid="title"]')
            price_elem = await card.query_selector('[data-testid="price-and-discounted-price"]')
            rating_elem = await card.query_selector('[data-testid="review-score"]')
            
            name = await name_elem.inner_text() if name_elem else "Unknown Hotel"
            price_text = await price_elem.inner_text() if price_elem else "0"
            rating_text = await rating_elem.inner_text() if rating_elem else "0"
            
            # Extract numeric price
            price = self._extract_price(price_text)
            rating = self._extract_rating(rating_text)
            
            # Get URL
            link_elem = await card.query_selector('a[data-testid="title-link"]')
            url = await link_elem.get_attribute('href') if link_elem else ""
            if url and not url.startswith('http'):
                url = f"https://www.booking.com{url}"
            
            return {
                'deal_type': 'hotel',
                'name': name,
                'hotel_name': name,
                'price': price,
                'currency': 'USD',
                'hotel_rating': rating,
                'location': search_params.get('location'),
                'check_in_date': search_params.get('check_in_date'),
                'check_out_date': search_params.get('check_out_date'),
                'url': url,
                'source': 'Booking.com',
                'room_type': 'Standard Room',  # Could extract from card if available
            }
        except Exception as e:
            print(f"Error extracting hotel data: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        try:
            # Remove currency symbols and commas
            numbers = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.0
    
    def _extract_rating(self, rating_text: str) -> float:
        """Extract numeric rating from text"""
        try:
            numbers = re.findall(r'\d+\.?\d*', rating_text)
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.0


class HotelScraperFactory:
    """Factory to create scrapers for different hotel sites"""
    
    @staticmethod
    def create_scraper(source: str) -> HotelScraper:
        """Create appropriate scraper based on source"""
        # For now, return the generic scraper
        # In the future, create specialized scrapers for each site
        return HotelScraper()
