from app.scrapers.base_scraper import BaseScraper
from typing import List, Dict
import re


class FlightScraper(BaseScraper):
    """Flight scraper with Canadian airlines support"""
    
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """Scrape flight deals"""
        origin = search_params.get('origin', 'Montreal')
        destination = search_params.get('location', search_params.get('destination', ''))
        departure_date = search_params.get('check_in_date', search_params.get('departure_date', ''))
        return_date = search_params.get('check_out_date', search_params.get('return_date', ''))
        target_airlines = search_params.get('airlines', [])
        
        # Generate demo flight data with Canadian airlines
        deals = await self._scrape_demo_flights(search_params)
        
        # Filter by specific airlines if provided
        if target_airlines:
            deals = [d for d in deals if any(airline.lower() in d['airline'].lower() for airline in target_airlines)]
        
        return deals
    
    async def _scrape_demo_flights(self, search_params: Dict) -> List[Dict]:
        """Create demo flight data with Canadian airlines"""
        origin = search_params.get('origin', 'Montreal')
        destination = search_params.get('location', '')
        
        # Canadian and US airlines
        demo_flights = [
            # Canadian Airlines
            {
                'airline': 'Air Canada',
                'base_price': 520,
                'duration': '4h 45m',
                'stops': 0,
                'departure_time': '07:30 AM',
                'arrival_time': '12:15 PM',
            },
            {
                'airline': 'WestJet',
                'base_price': 480,
                'duration': '5h 10m',
                'stops': 0,
                'departure_time': '09:15 AM',
                'arrival_time': '02:25 PM',
            },
            {
                'airline': 'Air Transat',
                'base_price': 395,
                'duration': '4h 30m',
                'stops': 0,
                'departure_time': '11:00 AM',
                'arrival_time': '03:30 PM',
            },
            {
                'airline': 'Sunwing',
                'base_price': 425,
                'duration': '4h 50m',
                'stops': 0,
                'departure_time': '06:00 AM',
                'arrival_time': '10:50 AM',
            },
            {
                'airline': 'Air Canada Rouge',
                'base_price': 465,
                'duration': '5h 00m',
                'stops': 0,
                'departure_time': '01:00 PM',
                'arrival_time': '06:00 PM',
            },
            # US Airlines
            {
                'airline': 'American Airlines',
                'base_price': 450,
                'duration': '5h 30m',
                'stops': 1,
                'departure_time': '08:00 AM',
                'arrival_time': '01:30 PM',
            },
            {
                'airline': 'Delta',
                'base_price': 425,
                'duration': '6h 15m',
                'stops': 1,
                'departure_time': '10:30 AM',
                'arrival_time': '04:45 PM',
            },
            {
                'airline': 'United',
                'base_price': 480,
                'duration': '5h 45m',
                'stops': 1,
                'departure_time': '02:00 PM',
                'arrival_time': '07:45 PM',
            },
            {
                'airline': 'Southwest',
                'base_price': 390,
                'duration': '7h 20m',
                'stops': 2,
                'departure_time': '06:00 AM',
                'arrival_time': '01:20 PM',
            },
            {
                'airline': 'JetBlue',
                'base_price': 410,
                'duration': '6h 10m',
                'stops': 1,
                'departure_time': '12:00 PM',
                'arrival_time': '06:10 PM',
            },
        ]
        
        deals = []
        for flight in demo_flights:
            import random
            price_variation = random.randint(-50, 100)
            
            deal = {
                'deal_type': 'flight',
                'name': f"{flight['airline']} - {origin} to {destination}",
                'airline': flight['airline'],
                'price': flight['base_price'] + price_variation,
                'currency': 'CAD' if flight['airline'] in ['Air Canada', 'WestJet', 'Air Transat', 'Sunwing', 'Air Canada Rouge'] else 'USD',
                'departure_time': flight['departure_time'],
                'arrival_time': flight['arrival_time'],
                'duration': flight['duration'],
                'stops': flight['stops'],
                'check_in_date': search_params.get('check_in_date'),
                'check_out_date': search_params.get('check_out_date'),
                'location': destination,
                'url': f"https://www.google.com/travel/flights",
                'source': 'Google Flights (Demo)',
            }
            deals.append(deal)
        
        return deals


class FlightScraperFactory:
    """Factory to create scrapers for different flight sites"""
    
    @staticmethod
    def create_scraper(source: str) -> FlightScraper:
        """Create appropriate scraper based on source"""
        return FlightScraper()
