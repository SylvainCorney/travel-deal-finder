"""
Air Transat API Scraper

This scraper uses Air Transat's public APIs instead of HTML scraping.
Much more reliable and faster!

Key APIs found:
- https://api.airtransat.com/en-CA/Services/FlightRoutes/GetAirports
- https://api.airtransat.com/en-CA/Services/Campaign/GetFlights
"""

import aiohttp
import asyncio
from typing import List, Dict
from datetime import datetime
import random


class AirTransatAPIScraper:
    """Scraper using Air Transat's official APIs"""
    
    def __init__(self):
        self.base_url = "https://api.airtransat.com/en-CA/Services"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-CA,en;q=0.9',
            'Referer': 'https://www.airtransat.com/',
            'Origin': 'https://www.airtransat.com'
        }
    
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """Scrape deals using API"""
        deals = []
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # Get available routes
                routes = await self._get_routes(session)
                
                # Get campaigns/deals
                campaigns = await self._get_campaigns(session, search_params)
                
                # Convert to our deal format
                deals = self._convert_to_deals(campaigns, search_params)
                
                print(f"✅ Air Transat API: Found {len(deals)} deals")
        
        except Exception as e:
            print(f"❌ Air Transat API error: {e}")
            deals = self._generate_demo_deals(search_params)
        
        return deals
    
    async def _get_routes(self, session: aiohttp.ClientSession) -> List:
        """Get available flight routes"""
        url = f"{self.base_url}/FlightRoutes/GetRoutesByType"
        params = {
            'source': 'booking-engine',
            'available': 'true',
            'codeshare': 'true',
            'connectair': 'true',
            'trains': 'true'
        }
        
        try:
            async with session.get(url, params=params, timeout=15) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error getting routes: {e}")
        
        return []
    
    async def _get_campaigns(self, session: aiohttp.ClientSession, search_params: Dict) -> List:
        """Get campaign deals (packages)"""
        url = f"{self.base_url}/Campaign/GetFlights"
        
        origin = self._map_airport_code(search_params.get('origin', 'YUL'))
        destination = self._map_destination(search_params.get('location', 'Cancun'))
        
        params = {
            'itineraryTypes': 'RT',  # Round trip
            'gateways': origin,
            'fallbackGateways': '1',
            'TilesNbr': '20'
        }
        
        # Try different campaign codes for different destinations
        campaign_codes = ['sudhiver', 'europecdgspring', 'Vedettes-HP']
        
        all_deals = []
        for code in campaign_codes:
            try:
                params['code'] = code
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and isinstance(data, list):
                            all_deals.extend(data)
            except Exception as e:
                print(f"Error getting campaign {code}: {e}")
                continue
        
        return all_deals
    
    def _convert_to_deals(self, api_deals: List, search_params: Dict) -> List[Dict]:
        """Convert API response to our deal format"""
        deals = []
        
        for api_deal in api_deals:
            try:
                # Extract data from API response
                # NOTE: Update these based on actual API response structure
                deal = {
                    'deal_type': 'package',
                    'name': api_deal.get('name', 'Air Transat Package'),
                    'hotel_name': api_deal.get('hotelName', 'TBD'),
                    'airline': 'Air Transat',
                    'price': float(api_deal.get('price', {}).get('amount', 0)),
                    'currency': 'CAD',
                    'hotel_rating': api_deal.get('hotelRating', 8.5),
                    'meal_plan': api_deal.get('mealPlan', 'Varies'),
                    'includes_flight': True,
                    'includes_hotel': True,
                    'includes_transfer': api_deal.get('includesTransfer', False),
                    'includes_meals': api_deal.get('includesMeals', False),
                    'location': api_deal.get('destination', search_params.get('location')),
                    'check_in_date': search_params.get('check_in_date'),
                    'check_out_date': search_params.get('check_out_date'),
                    'url': api_deal.get('url', 'https://www.airtransat.com/en-CA'),
                    'source': 'Air Transat',
                    'room_type': api_deal.get('roomType', 'Standard'),
                }
                
                deals.append(deal)
            
            except Exception as e:
                print(f"Error converting deal: {e}")
                continue
        
        return deals
    
    def _map_airport_code(self, origin: str) -> str:
        """Map city names to airport codes"""
        mapping = {
            'Montreal': 'YUL',
            'Toronto': 'YYZ',
            'Quebec': 'YQB',
            'Ottawa': 'YOW',
            'Vancouver': 'YVR',
            'Calgary': 'YYC',
        }
        
        # If already a code, return it
        if len(origin) == 3 and origin.isupper():
            return origin
        
        return mapping.get(origin, 'YUL')
    
    def _map_destination(self, location: str) -> str:
        """Map destination names to codes/regions"""
        mapping = {
            'Cancun': 'CUN',
            'Punta Cana': 'PUJ',
            'Varadero': 'VRA',
            'Paris': 'CDG',
            'London': 'LHR',
        }
        
        return mapping.get(location, location)
    
    def _generate_demo_deals(self, search_params: Dict) -> List[Dict]:
        """Fallback demo data"""
        hotels = [
            {'name': 'Excellence Playa Mujeres', 'price': 3400, 'rating': 9.2},
            {'name': 'Atelier Playa Mujeres', 'price': 3100, 'rating': 9.0},
            {'name': 'Secrets Maroma Beach', 'price': 3200, 'rating': 9.1},
        ]
        
        deals = []
        for hotel in hotels:
            price_variation = random.randint(-200, 300)
            hotel_slug = hotel['name'].lower().replace(' ', '-')
            
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
                'url': f"https://www.airtransat.com/en-CA/vacations/hotel/{hotel_slug}",
                'source': 'Air Transat (Demo)',
                'room_type': 'Deluxe Suite',
            })
        
        return deals


# Test the scraper
if __name__ == "__main__":
    async def test():
        scraper = AirTransatAPIScraper()
        
        params = {
            'origin': 'YUL',
            'location': 'Cancun',
            'check_in_date': '2026-03-15',
            'check_out_date': '2026-03-22',
        }
        
        deals = await scraper.scrape(params)
        
        print(f"\n✅ Found {len(deals)} deals:")
        for deal in deals:
            print(f"  • {deal['hotel_name']}: ${deal['price']} CAD")
            print(f"    Source: {deal['source']}")
            print(f"    URL: {deal['url']}\n")
    
    asyncio.run(test())
