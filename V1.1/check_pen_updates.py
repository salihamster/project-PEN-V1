"""
Check for PEN project updates from emails and L4 memory
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.storage.data_manager import DataManager
from src.agent_tools.email_tools import EmailTools

print("=" * 70)
print("📧 Checking for Project PEN Updates")
print("=" * 70)

# Initialize tools
data_manager = DataManager()
email_tools = EmailTools(data_manager)

# Calculate date range (last 30 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

print(f"\n📅 Searching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print("-" * 70)

# Search for PEN-related emails
print("\n1. Searching for 'PEN' in emails...")
result = email_tools.search_emails(
    subject="PEN",
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d'),
    limit=20
)

data = json.loads(result)

if data.get('status') == 'success':
    emails = data.get('emails', [])
    print(f"✅ Found {len(emails)} emails about PEN")
    
    if emails:
        print("\n📨 Recent PEN-related emails:")
        for i, email in enumerate(emails[:10], 1):
            print(f"\n{i}. From: {email.get('from', 'Unknown')}")
            print(f"   Subject: {email.get('subject', 'No subject')}")
            print(f"   Date: {email.get('timestamp', 'Unknown')[:10]}")
            
            # Get full content of first few emails
            if i <= 3:
                email_id = email.get('id')
                if email_id:
                    content_result = email_tools.get_email_content(email_id=email_id)
                    content_data = json.loads(content_result)
                    
                    if content_data.get('status') == 'success':
                        body = content_data.get('body', '')
                        # Show first 200 characters
                        preview = body[:200] + "..." if len(body) > 200 else body
                        print(f"   Preview: {preview}")
else:
    print(f"❌ Error: {data.get('message')}")

# Also search for "project" and "version"
print("\n\n2. Searching for 'version' or 'update' in emails...")
result2 = email_tools.search_emails(
    subject="version",
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d'),
    limit=10
)

data2 = json.loads(result2)
if data2.get('status') == 'success':
    emails2 = data2.get('emails', [])
    print(f"✅ Found {len(emails2)} emails about versions/updates")
    
    if emails2:
        print("\n📨 Version-related emails:")
        for i, email in enumerate(emails2[:5], 1):
            print(f"\n{i}. From: {email.get('from', 'Unknown')}")
            print(f"   Subject: {email.get('subject', 'No subject')}")
            print(f"   Date: {email.get('timestamp', 'Unknown')[:10]}")

print("\n" + "=" * 70)
print("✅ Email check completed")
print("=" * 70)
