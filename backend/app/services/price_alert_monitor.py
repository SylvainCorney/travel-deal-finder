"""
Price Alert Monitor Service

Background service that checks active price alerts and sends notifications
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.database.base import AsyncSessionLocal
from app.models.price_alert import PriceAlert
from app.models.deal import Deal
from app.scrapers.package_scraper import PackageScraperFactory


class PriceAlertMonitor:
    """Monitor and trigger price alerts"""
    
    def __init__(self):
        self.check_interval = 3600  # Check every hour (in seconds)
        self.running = False
    
    async def start(self):
        """Start the monitoring service"""
        self.running = True
        print("🔔 Price Alert Monitor started")
        
        while self.running:
            try:
                await self.check_all_alerts()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Error in price alert monitor: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def stop(self):
        """Stop the monitoring service"""
        self.running = False
        print("🔔 Price Alert Monitor stopped")
    
    async def check_all_alerts(self):
        """Check all active price alerts"""
        print(f"\n🔍 Checking price alerts at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        async with AsyncSessionLocal() as db:
            # Get all active alerts that haven't been triggered
            result = await db.execute(
                select(PriceAlert).where(
                    and_(
                        PriceAlert.is_active == True,
                        PriceAlert.notification_sent == False
                    )
                )
            )
            alerts = result.scalars().all()
            
            print(f"📊 Found {len(alerts)} active alerts to check")
            
            for alert in alerts:
                try:
                    await self.check_single_alert(alert, db)
                except Exception as e:
                    print(f"❌ Error checking alert {alert.id}: {e}")
            
            await db.commit()
    
    async def check_single_alert(self, alert: PriceAlert, db: AsyncSession):
        """Check a single price alert"""
        print(f"\n  🔎 Checking alert #{alert.id} for {alert.email}")
        print(f"     Hotels: {', '.join(alert.hotel_names)}")
        print(f"     Target: ${alert.target_price} {alert.currency}")
        
        # Build search parameters
        search_params = {
            'location': alert.destination,
            'origin': alert.origin or 'YUL',
            'sources': [alert.deal_type],
            'hotels': alert.hotel_names,
        }
        
        # Use date range if specified, otherwise use next 3 months
        if alert.preferred_check_in_start:
            search_params['check_in_date'] = alert.preferred_check_in_start
            search_params['check_out_date'] = alert.preferred_check_in_end or self._get_week_later(alert.preferred_check_in_start)
        else:
            # Check for deals in the next 3 months
            today = datetime.now()
            search_params['check_in_date'] = (today + timedelta(days=30)).strftime('%Y-%m-%d')
            search_params['check_out_date'] = (today + timedelta(days=37)).strftime('%Y-%m-%d')
        
        # Scrape deals
        try:
            package_scraper = PackageScraperFactory.create_scraper("all")
            deals = await package_scraper.safe_scrape(search_params)
            
            print(f"     Found {len(deals)} matching deals")
            
            # Filter deals matching the alert criteria
            matching_deals = self._filter_matching_deals(deals, alert)
            
            if matching_deals:
                best_deal = min(matching_deals, key=lambda d: d['price'])
                print(f"     💰 Best price: ${best_deal['price']} at {best_deal['hotel_name']}")
                
                # Update last checked info
                alert.last_checked_at = datetime.utcnow()
                alert.last_price_found = best_deal['price']
                
                # Check if price meets criteria
                if best_deal['price'] <= alert.target_price:
                    print(f"     ✅ TRIGGERED! Price below target!")
                    await self.trigger_alert(alert, best_deal, db)
                else:
                    print(f"     ⏳ Not yet - ${best_deal['price']} > ${alert.target_price}")
            else:
                print(f"     ❌ No matching deals found")
                alert.last_checked_at = datetime.utcnow()
        
        except Exception as e:
            print(f"     ❌ Error scraping: {e}")
    
    def _filter_matching_deals(self, deals: List[Dict], alert: PriceAlert) -> List[Dict]:
        """Filter deals that match the alert criteria"""
        matching = []
        
        for deal in deals:
            # Check if hotel name matches
            if any(hotel.lower() in deal.get('hotel_name', '').lower() for hotel in alert.hotel_names):
                matching.append(deal)
        
        return matching
    
    async def trigger_alert(self, alert: PriceAlert, deal: Dict, db: AsyncSession):
        """Trigger an alert and send notification"""
        print(f"     📧 Sending notification to {alert.email}")
        
        # Send email notification
        try:
            await self.send_email_notification(alert, deal)
            
            # Mark alert as triggered
            alert.notification_sent = True
            alert.triggered_at = datetime.utcnow()
            alert.is_active = False  # Deactivate after triggering
            
            print(f"     ✅ Notification sent successfully!")
        
        except Exception as e:
            print(f"     ❌ Failed to send notification: {e}")
    
    async def send_email_notification(self, alert: PriceAlert, deal: Dict):
        """Send email notification (configure your SMTP settings)"""
        
        # Email configuration - UPDATE THESE WITH YOUR SETTINGS
        SMTP_SERVER = "smtp.gmail.com"  # or your SMTP server
        SMTP_PORT = 587
        SMTP_USERNAME = "your-email@gmail.com"  # Your email
        SMTP_PASSWORD = "your-app-password"     # Your app password
        FROM_EMAIL = "alerts@travel-deals.com"
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🎉 Price Alert: {deal['hotel_name']} - ${deal['price']} {alert.currency}"
        msg['From'] = FROM_EMAIL
        msg['To'] = alert.email
        
        # Create HTML email body
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
              <h1 style="color: white; margin: 0;">🎉 Price Alert Triggered!</h1>
            </div>
            
            <div style="padding: 30px; background: #f7fafc;">
              <h2 style="color: #2d3748;">Great news, {alert.name or 'Traveler'}!</h2>
              
              <p style="font-size: 16px; color: #4a5568;">
                The price for <strong>{deal['hotel_name']}</strong> in {alert.destination} 
                has dropped to your target price!
              </p>
              
              <div style="background: white; border-radius: 12px; padding: 25px; margin: 25px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0; color: #667eea;">Deal Details</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Hotel:</td>
                    <td style="padding: 10px 0; font-weight: bold; border-bottom: 1px solid #e2e8f0;">{deal['hotel_name']}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Location:</td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">{deal['location']}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Price:</td>
                    <td style="padding: 10px 0; font-size: 24px; color: #48bb78; font-weight: bold; border-bottom: 1px solid #e2e8f0;">
                      ${deal['price']} {alert.currency}
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Your Target:</td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">${alert.target_price} {alert.currency}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Rating:</td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">⭐ {deal.get('hotel_rating', 'N/A')}/10</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Room Type:</td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">{deal.get('room_type', 'Standard')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096;">Meal Plan:</td>
                    <td style="padding: 10px 0; color: #48bb78; font-weight: bold;">{deal.get('meal_plan', 'All-Inclusive')}</td>
                  </tr>
                </table>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{deal.get('url', '#')}" 
                   style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; 
                          font-weight: bold; font-size: 16px;">
                  View This Deal →
                </a>
              </div>
              
              <p style="color: #718096; font-size: 14px; margin-top: 30px;">
                ⚡ <strong>Act fast!</strong> This price might not last long.
              </p>
              
              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
              
              <p style="color: #a0aec0; font-size: 12px; text-align: center;">
                This alert has been automatically deactivated. You can create new alerts anytime.
              </p>
            </div>
          </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email (COMMENT THIS OUT IF YOU HAVEN'T CONFIGURED SMTP YET)
        # Uncomment when you're ready to send real emails
        """
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        """
        
        # For now, just print the email (for testing)
        print("\n" + "="*60)
        print("EMAIL NOTIFICATION (Not actually sent - configure SMTP first)")
        print("="*60)
        print(f"To: {alert.email}")
        print(f"Subject: {msg['Subject']}")
        print("="*60)
    
    def _get_week_later(self, date_str: str) -> str:
        """Get date one week later"""
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return (date + timedelta(days=7)).strftime('%Y-%m-%d')


# Singleton instance
price_alert_monitor = PriceAlertMonitor()


async def start_price_alert_monitor():
    """Start the price alert monitoring service"""
    await price_alert_monitor.start()


async def stop_price_alert_monitor():
    """Stop the price alert monitoring service"""
    await price_alert_monitor.stop()
