"""
Email Service for sending notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@traveldeals.com')
        self.app_url = os.getenv('APP_URL', 'http://localhost:5173')
        
        # Check if email is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
    
    def send_confirmation_email(self, alert: Dict) -> bool:
        """Send confirmation email when alert is created"""
        
        if not self.is_configured:
            print("📧 Email not configured - skipping confirmation email")
            print(f"   Alert created for: {alert['email']}")
            print(f"   Hotels: {', '.join(alert['hotel_names'])}")
            print(f"   Target: ${alert['target_price']} {alert['currency']}")
            return False
        
        subject = f"✅ Price Alert Created - {', '.join(alert['hotel_names'][:2])}"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
              <h1 style="color: white; margin: 0;">✅ Price Alert Confirmed!</h1>
            </div>
            
            <div style="padding: 30px; background: #f7fafc;">
              <h2 style="color: #2d3748;">Hi{' ' + alert.get('name', '') if alert.get('name') else ''}!</h2>
              
              <p style="font-size: 16px; color: #4a5568;">
                Your price alert has been successfully created. We'll monitor prices and notify you 
                when we find a deal that matches your criteria.
              </p>
              
              <div style="background: white; border-radius: 12px; padding: 25px; margin: 25px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0; color: #667eea;">Alert Details</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Hotels:</td>
                    <td style="padding: 10px 0; font-weight: bold; border-bottom: 1px solid #e2e8f0;">
                      {', '.join(alert['hotel_names'])}
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Destination:</td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">{alert['destination']}</td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Target Price:</td>
                    <td style="padding: 10px 0; font-size: 20px; color: #48bb78; font-weight: bold; border-bottom: 1px solid #e2e8f0;">
                      ${alert['target_price']} {alert['currency']}
                    </td>
                  </tr>
                  {'<tr><td style="padding: 10px 0; color: #718096;">Travel Dates:</td><td style="padding: 10px 0;">' + alert.get('preferred_check_in_start', 'Flexible') + ' to ' + alert.get('preferred_check_in_end', 'Flexible') + '</td></tr>' if alert.get('preferred_check_in_start') else ''}
                </table>
              </div>
              
              <div style="background: #edf2f7; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; color: #2d3748; font-size: 14px;">
                  <strong>💡 What happens next?</strong><br>
                  We check prices every hour. When we find a deal at or below your target price, 
                  you'll receive an email with all the details and a direct booking link.
                </p>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{self.app_url}/alerts" 
                   style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; 
                          font-weight: bold; font-size: 16px;">
                  Manage Your Alerts
                </a>
              </div>
              
              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
              
              <p style="color: #a0aec0; font-size: 12px; text-align: center;">
                You can pause or delete this alert anytime from your 
                <a href="{self.app_url}/alerts" style="color: #667eea;">alerts dashboard</a>.
              </p>
            </div>
          </body>
        </html>
        """
        
        return self._send_email(alert['email'], subject, html_body)
    
    def send_price_drop_alert(self, alert: Dict, deal: Dict) -> bool:
        """Send email when price drops below target"""
        
        if not self.is_configured:
            print("📧 Email not configured - would send price alert:")
            print(f"   To: {alert['email']}")
            print(f"   Deal: {deal['hotel_name']} - ${deal['price']}")
            return False
        
        subject = f"🎉 Price Alert: {deal['hotel_name']} - ${deal['price']} {alert['currency']}"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
              <h1 style="color: white; margin: 0;">🎉 Price Alert Triggered!</h1>
            </div>
            
            <div style="padding: 30px; background: #f7fafc;">
              <h2 style="color: #2d3748;">Great news{', ' + alert.get('name', '') if alert.get('name') else ''}!</h2>
              
              <p style="font-size: 16px; color: #4a5568;">
                The price for <strong>{deal['hotel_name']}</strong> in {alert['destination']} 
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
                      ${deal['price']} {alert['currency']}
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 10px 0; color: #718096; border-bottom: 1px solid #e2e8f0;">Your Target:</td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">${alert['target_price']} {alert['currency']}</td>
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
                This alert has been automatically deactivated. You can create new alerts anytime from your 
                <a href="{self.app_url}/alerts" style="color: #667eea;">alerts dashboard</a>.
              </p>
            </div>
          </body>
        </html>
        """
        
        return self._send_email(alert['email'], subject, html_body)
    
    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Internal method to send email via SMTP"""
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False


# Singleton instance
email_service = EmailService()
