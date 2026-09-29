"""
Real Sunwing Scraper Implementation

This replaces the demo data with actual web scraping from Sunwing.ca
"""

from app.scrapers.base_scraper import BaseScraper
from typing import List, Dict
import random
import asyncio
import re
from datetime import datetime


class SunwingRealScraper(BaseScraper):
    """Real Sunwing scraper - scrapes actual data from sunwing.ca"""
    
    async def scrape(self, search_params: Dict) -> List[Dict]:
        """Scrape real Sunwing packages"""
        deals = []
        
        try:
            # Step 1: Build search URL
            url = self._build_sunwing_url(search_params)
            print(f"Navigating to Sunwing: {url}")
            
            # Step 2: Navigate to search page
            await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
            print("Page loaded, waiting for results...")
            
            # Step 3: Wait for results or detect if we need to interact with form
            try:
                # Try to wait for results (adjust selector based on actual site)
                await self.page.wait_for_selector('.hotel-card, .package-card, .result-item', timeout=10000)
                print("Results found!")
            except Exception as e:
                print(f"No results found or different structure: {e}")
                # If no results, try to find and interact with search form
                await self._interact_with_search_form(search_params)
            
            # Step 4: Extract deals
            deals = await self._extract_sunwing_deals(search_params)
            print(f"Extracted {len(deals)} deals from Sunwing")
            
        except Exception as e:
            print(f"Error scraping Sunwing (falling back to demo): {e}")
            # Fallback to demo data if scraping fails
            deals = await self._generate_demo_data(search_params)
        
        return deals
    
    def _build_sunwing_url(self, params: Dict) -> str:
        """
        Build Sunwing search URL
        
        Note: This is a simplified version. The actual URL structure may be different.
        You'll need to inspect Sunwing's actual search URLs.
        """
        base_url = "https://www.sunwing.ca/search"
        
        # Convert location to airport code if needed
        destination = params.get('location', 'Cancun')
        origin = params.get('origin', 'YUL')
        
        # Format dates (Sunwing might use different format)
        departure_date = params.get('check_in_date', '')
        return_date = params.get('check_out_date', '')
        
        # Build query string (adjust based on actual Sunwing URL structure)
        # You'll need to inspect the actual URLs Sunwing uses
        from urllib.parse import urlencode
        query_params = {
            'origin': origin,
            'destination': destination,
            'departureDate': departure_date,
            'returnDate': return_date,
            'adults': '2',
            'children': '0',
        }
        
        return f"{base_url}?{urlencode(query_params)}"
    
    async def _interact_with_search_form(self, params: Dict):
        """Fill and submit search form if needed"""
        try:
            # Look for origin input
            origin_input = await self.page.query_selector('input[name*="origin"], input[placeholder*="From"]')
            if origin_input:
                await origin_input.fill(params.get('origin', 'Montreal'))
                await self.random_delay(500, 1000)
            
            # Look for destination input
            dest_input = await self.page.query_selector('input[name*="destination"], input[placeholder*="To"]')
            if dest_input:
                await dest_input.fill(params.get('location', 'Cancun'))
                await self.random_delay(500, 1000)
            
            # Look for date inputs
            depart_input = await self.page.query_selector('input[name*="departure"], input[type="date"]')
            if depart_input:
                await depart_input.fill(params.get('check_in_date', ''))
                await self.random_delay(500, 1000)
            
            # Submit form
            submit_btn = await self.page.query_selector('button[type="submit"], button:has-text("Search")')
            if submit_btn:
                await submit_btn.click()
                await self.page.wait_for_load_state("networkidle", timeout=20000)
        
        except Exception as e:
            print(f"Error interacting with search form: {e}")
    
    async def _extract_sunwing_deals(self, params: Dict) -> List[Dict]:
        """Extract deals from Sunwing results page"""
        deals = []
        
        # Common selectors to try (you'll need to verify these)
        possible_selectors = [
            '.hotel-card',
            '.package-card', 
            '.result-item',
            '[data-hotel]',
            '.search-result',
            'article.hotel',
        ]
        
        cards = []
        for selector in possible_selectors:
            cards = await self.page.query_selector_all(selector)
            if cards:
                print(f"Found {len(cards)} cards using selector: {selector}")
                break
        
        if not cards:
            print("No cards found with any selector")
            return []
        
        # Extract data from each card
        for i, card in enumerate(cards[:20]):  # Limit to 20 results
            try:
                deal = await self._extract_deal_from_card(card, params)
                if deal:
                    deals.append(deal)
            except Exception as e:
                print(f"Error extracting deal {i}: {e}")
                continue
        
        return deals
    
    async def _extract_deal_from_card(self, card, params: Dict) -> Dict:
        """Extract deal information from a single card"""
        try:
            # Try different selectors for hotel name
            hotel_name = await self._try_extract_text(card, [
                '.hotel-name',
                '.property-name',
                'h2',
                'h3',
                '[data-hotel-name]'
            ]) or "Unknown Hotel"
            
            # Try to extract price
            price_text = await self._try_extract_text(card, [
                '.price',
                '.total-price',
                '[data-price]',
                '.price-value'
            ]) or "0"
            
            price = self._extract_number(price_text)
            
            # Try to extract rating
            rating_text = await self._try_extract_text(card, [
                '.rating',
                '.star-rating',
                '[data-rating]'
            ]) or "8.0"
            
            rating = self._extract_rating(rating_text)
            
            # Try to extract room type
            room_type = await self._try_extract_text(card, [
                '.room-type',
                '.accommodation-type'
            ]) or "Standard Room"
            
            # Try to get URL
            url = await self._try_extract_link(card) or f"https://www.sunwing.ca/hotels/{hotel_name.lower().replace(' ', '-')}"
            
            return {
                'deal_type': 'all_inclusive',
                'name': f"{hotel_name} - All-Inclusive",
                'hotel_name': hotel_name,
                'hotel_rating': rating,
                'room_type': room_type,
                'airline': 'Sunwing',
                'price': price,
                'currency': 'CAD',
                'meal_plan': 'All-Inclusive',
                'includes_flight': True,
                'includes_hotel': True,
                'includes_transfer': True,
                'includes_meals': True,
                'check_in_date': params.get('check_in_date'),
                'check_out_date': params.get('check_out_date'),
                'location': params.get('location'),
                'url': url,
                'source': 'Sunwing',  # No "(Demo)" label!
                'departure_time': '07:30 AM',
                'arrival_time': '12:00 PM',
            }
        
        except Exception as e:
            print(f"Error extracting deal data: {e}")
            return None
    
    async def _try_extract_text(self, element, selectors: List[str]) -> str:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                elem = await element.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return ""
    
    async def _try_extract_link(self, element) -> str:
        """Try to extract link from card"""
        try:
            link = await element.query_selector('a')
            if link:
                href = await link.get_attribute('href')
                if href:
                    if not href.startswith('http'):
                        href = f"https://www.sunwing.ca{href}"
                    return href
        except:
            pass
        return ""
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        try:
            # Remove currency symbols, commas, etc.
            numbers = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.0
    
    def _extract_rating(self, text: str) -> float:
        """Extract rating from text"""
        try:
            numbers = re.findall(r'\d+\.?\d*', text)
            if numbers:
                rating = float(numbers[0])
                # Normalize to 0-10 scale if needed
                if rating > 10:
                    rating = rating / 10
                return min(rating, 10.0)
        except:
            pass
        return 8.0
    
    async def _generate_demo_data(self, params: Dict) -> List[Dict]:
        """Fallback demo data if scraping fails"""
        destination = params.get('location', 'Cancun')
        
        packages = [
            {'hotel_name': 'Riu Palace Peninsula', 'hotel_rating': 8.9, 'base_price': 2850, 'room_type': 'Junior Suite Ocean View'},
            {'hotel_name': 'Breathless Riviera Cancun', 'hotel_rating': 8.7, 'base_price': 2915, 'room_type': 'Xhale Club Master Suite'},
            {'hotel_name': 'Riu Dunamar', 'hotel_rating': 8.6, 'base_price': 2650, 'room_type': 'Junior Suite'},
        ]
        
        deals = []
        for pkg in packages:
            price_variation = random.randint(-200, 300)
            hotel_slug = pkg['hotel_name'].lower().replace(' ', '-')
            
            deals.append({
                'deal_type': 'all_inclusive',
                'name': f"{pkg['hotel_name']} - All-Inclusive",
                'hotel_name': pkg['hotel_name'],
                'hotel_rating': pkg['hotel_rating'],
                'room_type': pkg['room_type'],
                'airline': 'Sunwing',
                'price': pkg['base_price'] + price_variation,
                'currency': 'CAD',
                'meal_plan': 'All-Inclusive',
                'includes_flight': True,
                'includes_hotel': True,
                'includes_transfer': True,
                'includes_meals': True,
                'check_in_date': params.get('check_in_date'),
                'check_out_date': params.get('check_out_date'),
                'location': destination,
                'url': f"https://www.sunwing.ca/vacations/package/{hotel_slug}-cancun",
                'source': 'Sunwing (Demo - Scraping Failed)',
                'departure_time': '07:30 AM',
                'arrival_time': '12:00 PM',
            })
        
        return deals


# How to test this scraper
if __name__ == "__main__":
    import asyncio
    
    async def test():
        scraper = SunwingRealScraper()
        
        test_params = {
            'origin': 'YUL',
            'location': 'Cancun',
            'check_in_date': '2026-03-15',
            'check_out_date': '2026-03-22',
        }
        
        # Run with visible browser to see what happens
        await scraper.setup(headless=False)
        deals = await scraper.scrape(test_params)
        
        print(f"\n\nFound {len(deals)} deals:")
        for deal in deals:
            print(f"  - {deal['hotel_name']}: ${deal['price']} CAD")
            print(f"    Source: {deal['source']}")
            print(f"    URL: {deal['url']}\n")
        
        await scraper.cleanup()
    
    asyncio.run(test())
