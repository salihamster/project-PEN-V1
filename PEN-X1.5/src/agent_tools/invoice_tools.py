"""
Invoice Processing Tools

Tools for parsing invoices from emails, web pages, and images
"""

from typing import Dict, Any, Optional
from ..parsers.html_parser import HTMLEmailParser
from ..parsers.web_scraper import WebScraper
from ..parsers.ocr_parser import OCRParser
from ..utils.logger import get_logger

logger = get_logger(__name__)


def parse_email_html(email_html: str) -> Dict[str, Any]:
    """
    Parse HTML email and extract invoice data
    
    Strategy:
    - If HTML is small (<5000 chars): Return raw HTML for model to process
    - If HTML is large: Use Gemini to extract structured data
    
    Args:
        email_html: HTML content of the email
    
    Returns:
        Dictionary with parsed invoice data, links, and tables
    
    Example:
        result = parse_email_html("<html>...</html>")
        # Returns: {
        #   "is_invoice": true,
        #   "invoice_data": {"total_amount": "149.99", "invoice_number": "INV-001"},
        #   "readable_content": "...",
        #   "html_size": 1234
        # }
    """
    try:
        parser = HTMLEmailParser()
        
        # Check if it's an invoice
        is_invoice = parser.is_invoice_email(email_html)
        
        if not is_invoice:
            return {
                "is_invoice": False,
                "message": "This email does not contain an invoice"
            }
        
        html_size = len(email_html)
        
        # Parse HTML with basic parser
        result = parser.parse_html_email(email_html)
        
        # If HTML is small, return it for model to process directly
        if html_size < 5000:
            return {
                "is_invoice": True,
                "html_size": html_size,
                "strategy": "small_html",
                "message": "HTML is small, model can process directly",
                "invoice_data": result.get('invoice_data', {}),
                "links": result.get('links', []),
                "tables": result.get('tables', []),
                "text_content": result.get('text_content', '')[:1000],
                "raw_html": email_html  # Include raw HTML for model
            }
        
        # If HTML is large, use Gemini to extract structured data
        try:
            import os
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Fallback to basic parsing
                return {
                    "is_invoice": True,
                    "html_size": html_size,
                    "strategy": "basic_parser",
                    "message": "HTML is large but no Gemini API key, using basic parsing",
                    "invoice_data": result.get('invoice_data', {}),
                    "links": result.get('links', []),
                    "tables": result.get('tables', []),
                    "text_content": result.get('text_content', '')[:2000]
                }
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            prompt = f"""Extract invoice/receipt information from this HTML email content and convert to readable format.

HTML Content:
{email_html}

Please extract the following information:
1. Invoice/Receipt number
2. Date
3. Total amount (with currency)
4. Vendor/Company name
5. Product/Service list (if available)
6. Important links (invoice view, download, etc.)

Return response in JSON format:
{{
  "invoice_number": "...",
  "date": "...",
  "total_amount": "...",
  "currency": "TL/USD/EUR",
  "vendor": "...",
  "items": [...],
  "important_links": [...],
  "summary": "Brief summary"
}}"""
            
            response = model.generate_content(prompt)
            
            # Try to parse JSON from response
            import json
            import re
            
            response_text = response.text
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            try:
                gemini_data = json.loads(response_text)
            except:
                # If JSON parsing fails, return as text
                gemini_data = {"raw_response": response_text}
            
            return {
                "is_invoice": True,
                "html_size": html_size,
                "strategy": "gemini_extraction",
                "message": "HTML is large, structured with Gemini",
                "invoice_data": gemini_data,
                "links": result.get('links', []),
                "tables": result.get('tables', [])
            }
            
        except Exception as gemini_error:
            logger.warning(f"Gemini extraction failed: {gemini_error}, falling back to basic parser")
            return {
                "is_invoice": True,
                "html_size": html_size,
                "strategy": "basic_parser_fallback",
                "message": f"Gemini error, using basic parsing: {str(gemini_error)}",
                "invoice_data": result.get('invoice_data', {}),
                "links": result.get('links', []),
                "tables": result.get('tables', []),
                "text_content": result.get('text_content', '')[:2000]
            }
    
    except Exception as e:
        logger.error(f"HTML parsing error: {e}")
        return {
            "error": str(e),
            "message": "Failed to parse HTML"
        }


def scrape_invoice_url(url: str, require_trust: bool = True) -> Dict[str, Any]:
    """
    Scrape invoice/receipt page from URL
    
    Args:
        url: URL to scrape
        require_trust: Only scrape trusted domains (default: True)
    
    Returns:
        Dictionary with scraped invoice data
    
    Example:
        result = scrape_invoice_url("https://stripe.com/invoices/inv_123")
        # Returns: {
        #   "status": "success",
        #   "invoice_data": {"total": "49.99"},
        #   "download_links": [...]
        # }
    """
    try:
        scraper = WebScraper()
        
        # Check if domain is safe
        if require_trust and not scraper.is_safe_domain(url):
            return {
                "error": "untrusted_domain",
                "message": f"This domain is not in the trusted list: {url}",
                "suggestion": "To add to trusted domains: add_trusted_domain(domain)"
            }
        
        # Scrape page
        result = scraper.scrape_invoice_page(url, require_trust=require_trust)
        
        return result
    
    except Exception as e:
        logger.error(f"Web scraping error: {e}")
        return {
            "error": str(e),
            "message": "Failed to scrape web page"
        }


def extract_text_from_image(image_path: str, lang: str = "eng+tur") -> Dict[str, Any]:
    """
    Extract text from invoice image using OCR
    
    Args:
        image_path: Path to image file (jpg, png, pdf)
        lang: OCR language (default: "eng+tur" for English + Turkish)
    
    Returns:
        Dictionary with extracted text and invoice data
    
    Example:
        result = extract_text_from_image("invoice.jpg")
        # Returns: {
        #   "status": "success",
        #   "text": "Toplam: 299.99 TL...",
        #   "invoice_data": {"total_amount": "299.99"},
        #   "confidence": 92.5
        # }
    """
    try:
        ocr = OCRParser()
        
        # Check if OCR is available
        if not ocr.ocr_available:
            return {
                "error": "ocr_not_available",
                "message": "OCR libraries not installed",
                "install_guide": "To install: pip install pytesseract pillow pdf2image"
            }
        
        # Check file format
        if not ocr.is_supported_format(image_path):
            return {
                "error": "unsupported_format",
                "message": f"Unsupported file format: {image_path}",
                "supported_formats": ocr.supported_formats
            }
        
        # Extract text
        if image_path.lower().endswith('.pdf'):
            result = ocr.extract_text_from_pdf(image_path, lang=lang)
        else:
            result = ocr.extract_text_from_image(image_path, lang=lang)
        
        return result
    
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return {
            "error": str(e),
            "message": "Failed to extract text from image"
        }


def add_trusted_domain(domain: str) -> Dict[str, Any]:
    """
    Add a domain to trusted list for web scraping
    
    Args:
        domain: Domain to add (e.g., "example.com")
    
    Returns:
        Success message
    
    Example:
        result = add_trusted_domain("mycompany.com")
        # Returns: {"status": "success", "message": "Domain eklendi"}
    """
    try:
        scraper = WebScraper()
        scraper.add_trusted_domain(domain)
        
        return {
            "status": "success",
            "message": f"'{domain}' added to trusted domain list",
            "trusted_domains": scraper.trusted_domains
        }
    
    except Exception as e:
        logger.error(f"Add domain error: {e}")
        return {
            "error": str(e),
            "message": "Failed to add domain"
        }


def get_trusted_domains() -> Dict[str, Any]:
    """
    Get list of trusted domains for web scraping
    
    Returns:
        List of trusted domains
    
    Example:
        result = get_trusted_domains()
        # Returns: {"domains": ["stripe.com", "paypal.com", ...]}
    """
    try:
        scraper = WebScraper()
        
        return {
            "status": "success",
            "domains": scraper.trusted_domains,
            "count": len(scraper.trusted_domains)
        }
    
    except Exception as e:
        logger.error(f"Get domains error: {e}")
        return {
            "error": str(e),
            "message": "Failed to get domain list"
        }
