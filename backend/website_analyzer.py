"""
Travel Website Analyzer

This tool helps analyze travel websites to understand:
1. How their search works (URL structure, forms, APIs)
2. What selectors to use for extracting data
3. If they have anti-bot measures
4. If they use APIs we can leverage
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime, timedelta


class WebsiteAnalyzer:
    """Analyze travel website structure"""
    
    SITES = {
        'sunwing': 'https://www.sunwing.ca/',
        'airtransat': 'https://www.airtransat.com/en-CA',
        'tripvoyage': 'https://www.tripvoyage.ca/',
        'voyagesarabais': 'https://voyagesarabais.com/',
        'bergeron': 'https://www.voyagesbergeron.com/',
        'destination': 'https://www.voyagesdestination.com/',
        'tripcentral': 'https://www.tripcentral.ca',
        'kayak': 'https://www.ca.kayak.com/',
    }
    
    def __init__(self):
        self.results = {}
    
    async def analyze_all(self):
        """Analyze all travel sites"""
        print("🔍 Travel Website Analyzer")
        print("=" * 60)
        print()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            for site_name, url in self.SITES.items():
                print(f"\n{'='*60}")
                print(f"Analyzing: {site_name.upper()}")
                print(f"URL: {url}")
                print(f"{'='*60}\n")
                
                try:
                    result = await self.analyze_site(browser, site_name, url)
                    self.results[site_name] = result
                    
                    # Save results after each site
                    self.save_results()
                    
                except Exception as e:
                    print(f"❌ Error analyzing {site_name}: {e}")
                    self.results[site_name] = {'error': str(e)}
            
            await browser.close()
        
        print("\n" + "="*60)
        print("✅ Analysis Complete!")
        print(f"Results saved to: travel_sites_analysis.json")
        print("="*60)
    
    async def analyze_site(self, browser, site_name, url):
        """Analyze a single website"""
        page = await browser.new_page()
        
        # Track network requests to find APIs
        api_requests = []
        
        def handle_request(request):
            if any(keyword in request.url.lower() for keyword in ['api', 'search', 'package', 'hotel', 'flight']):
                api_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'type': request.resource_type
                })
        
        page.on('request', handle_request)
        
        result = {
            'url': url,
            'analyzed_at': datetime.now().isoformat(),
            'homepage': {},
            'search_analysis': {},
            'api_calls': [],
            'recommendations': []
        }
        
        try:
            # Load homepage
            print("  📄 Loading homepage...")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            await asyncio.sleep(3)  # Wait for dynamic content
            
            result['homepage'] = {
                'status': response.status,
                'title': await page.title(),
                'url': page.url,
                'has_redirect': page.url != url
            }
            
            print(f"     Status: {response.status}")
            print(f"     Title: {await page.title()}")
            
            # Look for search forms
            print("  🔎 Looking for search forms...")
            search_indicators = await self.find_search_elements(page)
            result['search_analysis'] = search_indicators
            
            # Take screenshot
            screenshot_path = f"/tmp/{site_name}_homepage.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"     📸 Screenshot: {screenshot_path}")
            
            # Analyze API calls
            await asyncio.sleep(2)
            result['api_calls'] = api_requests[:10]  # First 10 API calls
            
            if api_requests:
                print(f"     🔌 Found {len(api_requests)} API calls")
                for api in api_requests[:3]:
                    print(f"        - {api['method']} {api['url'][:80]}...")
            
            # Generate recommendations
            result['recommendations'] = self.generate_recommendations(result)
            
            print("\n  💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"     • {rec}")
        
        except Exception as e:
            print(f"     ❌ Error: {e}")
            result['error'] = str(e)
        
        finally:
            await page.close()
        
        return result
    
    async def find_search_elements(self, page):
        """Find search-related elements on the page"""
        indicators = {
            'has_origin_input': False,
            'has_destination_input': False,
            'has_date_inputs': False,
            'has_search_button': False,
            'found_selectors': []
        }
        
        # Common selectors for travel search
        selectors_to_try = {
            'origin': [
                'input[name*="origin"]',
                'input[placeholder*="From"]',
                'input[placeholder*="Departure"]',
                '#origin',
                '.origin-input'
            ],
            'destination': [
                'input[name*="destination"]',
                'input[placeholder*="To"]',
                'input[placeholder*="Where"]',
                '#destination',
                '.destination-input'
            ],
            'date': [
                'input[type="date"]',
                'input[name*="date"]',
                'input[placeholder*="Date"]',
                '.date-picker'
            ],
            'search_button': [
                'button[type="submit"]',
                'button:has-text("Search")',
                'button:has-text("Find")',
                '.search-button'
            ]
        }
        
        for field_type, selectors in selectors_to_try.items():
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        indicators[f'has_{field_type}_input'] = True
                        indicators['found_selectors'].append({
                            'type': field_type,
                            'selector': selector
                        })
                        break
                except:
                    pass
        
        return indicators
    
    def generate_recommendations(self, result):
        """Generate scraping recommendations based on analysis"""
        recommendations = []
        
        # Check for API calls
        if result['api_calls']:
            recommendations.append("✅ Site uses APIs - consider using API endpoints directly instead of HTML scraping")
            
            json_apis = [api for api in result['api_calls'] if 'json' in api['url'].lower() or api['type'] == 'fetch']
            if json_apis:
                recommendations.append(f"🎯 Found {len(json_apis)} JSON API calls - highly recommended approach")
        
        # Check for search elements
        if result['search_analysis'].get('has_search_button'):
            recommendations.append("✅ Found search form - can automate form submission")
        else:
            recommendations.append("⚠️ No obvious search form - might use dynamic JavaScript or require specific URL structure")
        
        # Check for React/Vue/Angular
        if result['homepage'].get('title') and any(framework in result['homepage']['title'].lower() for framework in ['react', 'vue', 'angular']):
            recommendations.append("⚠️ Modern JS framework detected - will need to wait for dynamic content")
        
        return recommendations
    
    def save_results(self):
        """Save analysis results to JSON"""
        with open('travel_sites_analysis.json', 'w') as f:
            json.dump(self.results, f, indent=2)
    
    async def quick_test_search(self, site_name):
        """Quick test of a specific site's search"""
        print(f"\n🧪 Quick Search Test: {site_name.upper()}")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            url = self.SITES.get(site_name)
            if not url:
                print(f"❌ Unknown site: {site_name}")
                return
            
            print(f"1. Opening {url}")
            await page.goto(url, wait_until='domcontentloaded')
            
            print("2. Page loaded - you have 30 seconds to:")
            print("   • Manually perform a search")
            print("   • Look at the URL structure after search")
            print("   • Inspect the result cards")
            print()
            print("   I'll be watching network requests...")
            
            api_calls = []
            page.on('request', lambda req: api_calls.append(req.url) if 'api' in req.url.lower() else None)
            
            # Wait for manual interaction
            await asyncio.sleep(30)
            
            print("\n📊 Analysis:")
            print(f"   Current URL: {page.url}")
            
            if api_calls:
                print(f"\n   Found {len(api_calls)} API calls:")
                for api in api_calls[:5]:
                    print(f"   • {api}")
            
            print("\n   Press ENTER to close browser...")
            input()
            
            await browser.close()


async def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           🔍 TRAVEL WEBSITE ANALYZER 🔍                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

This tool will analyze all Canadian travel sites to help us:
• Understand their structure
• Find API endpoints
• Identify scraping strategies
• Detect anti-bot measures

Choose an option:
1. Analyze ALL sites (takes ~10-15 minutes)
2. Quick test specific site (interactive)
3. Exit

""")
    
    choice = input("Enter choice (1-3): ").strip()
    
    analyzer = WebsiteAnalyzer()
    
    if choice == "1":
        await analyzer.analyze_all()
    elif choice == "2":
        print("\nAvailable sites:")
        for i, site in enumerate(analyzer.SITES.keys(), 1):
            print(f"  {i}. {site}")
        
        site_num = input("\nEnter site number: ").strip()
        try:
            site_name = list(analyzer.SITES.keys())[int(site_num) - 1]
            await analyzer.quick_test_search(site_name)
        except:
            print("Invalid selection")
    else:
        print("Exiting...")


if __name__ == "__main__":
    asyncio.run(main())
