"""
HTML Email Parser

Extracts structured data from HTML emails (invoices, receipts, etc.)
"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class HTMLEmailParser:
    """Parse HTML emails and extract structured data"""
    
    def __init__(self):
        self.invoice_patterns = {
            'total': [
                r'toplam[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',  # Turkish: toplam
                r'total[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',
                r'tutar[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',  # Turkish: tutar (amount)
                r'amount[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',
            ],
            'invoice_number': [
                r'fatura\s*(?:no|numarası)[:\s]*([A-Z0-9\-]+)',  # Turkish: fatura (invoice), numarası (number)
                r'invoice\s*(?:no|number)[:\s]*([A-Z0-9\-]+)',
                r'makbuz\s*(?:no|numarası)[:\s]*([A-Z0-9\-]+)',  # Turkish: makbuz (receipt)
                r'receipt\s*(?:no|number)[:\s]*([A-Z0-9\-]+)',
            ],
            'date': [
                r'tarih[:\s]*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})',  # Turkish: tarih (date)
                r'date[:\s]*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})',
            ],
            'vendor': [
                r'satıcı[:\s]*([^\n<]+)',  # Turkish: satıcı (vendor)
                r'vendor[:\s]*([^\n<]+)',
                r'from[:\s]*([^\n<]+)',
            ]
        }
    
    def parse_html_email(self, html_content: str) -> Dict[str, Any]:
        """
        Parse HTML email and extract structured data
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dictionary with extracted data
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Extract structured data
        result = {
            'text_content': text,
            'invoice_data': self._extract_invoice_data(text, soup),
            'links': self._extract_links(soup),
            'tables': self._extract_tables(soup),
            'metadata': self._extract_metadata(soup)
        }
        
        return result
    
    def _extract_invoice_data(self, text: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract invoice/receipt data from text"""
        data = {}
        
        # Extract total amount
        for pattern in self.invoice_patterns['total']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['total_amount'] = match.group(1)
                break
        
        # Extract invoice number
        for pattern in self.invoice_patterns['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['invoice_number'] = match.group(1)
                break
        
        # Extract date
        for pattern in self.invoice_patterns['date']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['date'] = match.group(1)
                break
        
        # Extract vendor
        for pattern in self.invoice_patterns['vendor']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['vendor'] = match.group(1).strip()
                break
        
        return data
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links from HTML"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            link_text = a_tag.get_text(strip=True)
            href = a_tag['href']
            
            # Classify link type
            link_type = 'other'
            if any(keyword in link_text.lower() for keyword in ['fatura', 'invoice', 'makbuz', 'receipt']):  # Turkish: fatura, makbuz
                link_type = 'invoice'
            elif any(keyword in link_text.lower() for keyword in ['görüntüle', 'view', 'download', 'indir']):  # Turkish: görüntüle (view), indir (download)
                link_type = 'document'
            
            links.append({
                'text': link_text,
                'url': href,
                'type': link_type
            })
        
        return links
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """Extract table data from HTML"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = []
            
            for row in table.find_all('tr'):
                row_data = []
                for cell in row.find_all(['td', 'th']):
                    row_data.append(cell.get_text(strip=True))
                if row_data:
                    table_data.append(row_data)
            
            if table_data:
                tables.append(table_data)
        
        return tables
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Extract title
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text(strip=True)
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def is_invoice_email(self, html_content: str) -> bool:
        """Check if email is likely an invoice/receipt"""
        text = BeautifulSoup(html_content, 'html.parser').get_text().lower()
        
        invoice_keywords = [
            'fatura', 'invoice', 'makbuz', 'receipt',  # Turkish: fatura, makbuz
            'ödeme', 'payment', 'tutar', 'amount',  # Turkish: ödeme (payment), tutar (amount)
            'toplam', 'total', 'ücret', 'charge'  # Turkish: toplam (total), ücret (charge)
        ]
        
        return any(keyword in text for keyword in invoice_keywords)
