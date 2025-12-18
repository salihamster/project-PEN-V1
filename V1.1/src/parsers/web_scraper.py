"""
Web Scraper for Invoice Links

Safely follows and scrapes invoice/receipt pages
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import time


class WebScraper:
    """Safe web scraper for invoice/receipt pages"""
    
    def __init__(self):
        self.trusted_domains = [
            'google.com',
            'github.com',
            'stripe.com',
            'paypal.com',
            'aws.amazon.com',
            'azure.microsoft.com',
            'digitalocean.com',
            'heroku.com',
            'vercel.com',
            'netlify.com',
            'cloudflare.com',
            'anthropic.com',
            'openai.com',
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.timeout = 10  # seconds
    
    def is_safe_domain(self, url: str) -> bool:
        """Check if domain is in trusted list"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check exact match or subdomain
            for trusted in self.trusted_domains:
                if domain == trusted or domain.endswith('.' + trusted):
                    return True
            
            return False
        except:
            return False
    
    def scrape_invoice_page(self, url: str, require_trust: bool = True) -> Optional[Dict[str, Any]]:
        """
        Scrape invoice/receipt page
        
        Args:
            url: URL to scrape
            require_trust: If True, only scrape trusted domains
            
        Returns:
            Dictionary with scraped data or None if failed
        """
        # Security check
        if require_trust and not self.is_safe_domain(url):
            return {
                'error': 'untrusted_domain',
                'message': f'Domain not in trusted list: {urlparse(url).netloc}',
                'url': url
            }
        
        try:
            # Make request
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data
            result = {
                'url': url,
                'status': 'success',
                'title': self._extract_title(soup),
                'text_content': self._extract_text(soup),
                'invoice_data': self._extract_invoice_data(soup),
                'tables': self._extract_tables(soup),
                'download_links': self._extract_download_links(soup)
            }
            
            return result
            
        except requests.Timeout:
            return {
                'error': 'timeout',
                'message': f'Request timed out after {self.timeout}s',
                'url': url
            }
        except requests.RequestException as e:
            return {
                'error': 'request_failed',
                'message': str(e),
                'url': url
            }
        except Exception as e:
            return {
                'error': 'parsing_failed',
                'message': str(e),
                'url': url
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title = soup.find('title')
        return title.get_text(strip=True) if title else ''
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        return soup.get_text(separator='\n', strip=True)
    
    def _extract_invoice_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract invoice-specific data"""
        import re
        
        text = soup.get_text()
        data = {}
        
        # Extract total amount
        total_patterns = [
            r'total[:\s]*\$?([0-9,]+\.?\d*)',
            r'amount[:\s]*\$?([0-9,]+\.?\d*)',
            r'toplam[:\s]*([0-9,]+\.?\d*)\s*(?:TL|₺)',
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['total'] = match.group(1)
                break
        
        # Extract date
        date_patterns = [
            r'date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'tarih[:\s]*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['date'] = match.group(1)
                break
        
        return data
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """Extract table data"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = []
            for row in table.find_all('tr'):
                row_data = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if row_data:
                    table_data.append(row_data)
            if table_data:
                tables.append(table_data)
        
        return tables
    
    def _extract_download_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract PDF/document download links"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True)
            
            # Check if it's a document link
            if any(ext in href.lower() for ext in ['.pdf', '.doc', '.xls', '.csv']):
                links.append({
                    'text': text,
                    'url': href,
                    'type': 'document'
                })
            elif any(keyword in text.lower() for keyword in ['download', 'indir', 'pdf']):
                links.append({
                    'text': text,
                    'url': href,
                    'type': 'download'
                })
        
        return links
    
    def add_trusted_domain(self, domain: str):
        """Add a domain to trusted list"""
        if domain not in self.trusted_domains:
            self.trusted_domains.append(domain.lower())
    
    def remove_trusted_domain(self, domain: str):
        """Remove a domain from trusted list"""
        if domain in self.trusted_domains:
            self.trusted_domains.remove(domain.lower())
