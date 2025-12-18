"""
OCR Parser for Image/PDF Invoices

Extracts text from images and PDFs using OCR
"""

from typing import Dict, Any, Optional, List
import os
from pathlib import Path


class OCRParser:
    """OCR parser for extracting text from images and PDFs"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp']
        self.ocr_available = self._check_ocr_availability()
    
    def _check_ocr_availability(self) -> bool:
        """Check if OCR libraries are available"""
        try:
            import pytesseract
            from PIL import Image
            return True
        except ImportError:
            return False
    
    def extract_text_from_image(self, image_path: str, lang: str = 'eng+tur') -> Optional[Dict[str, Any]]:
        """
        Extract text from image using OCR
        
        Args:
            image_path: Path to image file
            lang: OCR language (default: English + Turkish) - 'eng+tur' for English and Turkish
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.ocr_available:
            return {
                'error': 'ocr_not_available',
                'message': 'OCR libraries not installed. Install: pip install pytesseract pillow',
                'install_guide': 'Also install Tesseract: https://github.com/tesseract-ocr/tesseract'
            }
        
        try:
            import pytesseract
            from PIL import Image
            
            # Open image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang)
            
            # Extract data with confidence
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            
            result = {
                'status': 'success',
                'text': text,
                'confidence': self._calculate_average_confidence(data),
                'word_count': len(text.split()),
                'invoice_data': self._extract_invoice_data_from_text(text)
            }
            
            return result
            
        except FileNotFoundError:
            return {
                'error': 'file_not_found',
                'message': f'Image file not found: {image_path}'
            }
        except Exception as e:
            return {
                'error': 'ocr_failed',
                'message': str(e)
            }
    
    def extract_text_from_pdf(self, pdf_path: str, lang: str = 'eng+tur') -> Optional[Dict[str, Any]]:
        """
        Extract text from PDF (including scanned PDFs)
        
        Args:
            pdf_path: Path to PDF file
            lang: OCR language - 'eng+tur' for English and Turkish
            
        Returns:
            Dictionary with extracted text
        """
        if not self.ocr_available:
            return {
                'error': 'ocr_not_available',
                'message': 'OCR libraries not installed'
            }
        
        try:
            import pytesseract
            from PIL import Image
            import pdf2image
            
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path)
            
            # Extract text from each page
            all_text = []
            total_confidence = 0
            
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang=lang)
                data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
                
                all_text.append({
                    'page': i + 1,
                    'text': text,
                    'confidence': self._calculate_average_confidence(data)
                })
                
                total_confidence += all_text[-1]['confidence']
            
            combined_text = '\n\n'.join([page['text'] for page in all_text])
            
            result = {
                'status': 'success',
                'pages': len(images),
                'text': combined_text,
                'page_data': all_text,
                'average_confidence': total_confidence / len(images) if images else 0,
                'invoice_data': self._extract_invoice_data_from_text(combined_text)
            }
            
            return result
            
        except ImportError:
            return {
                'error': 'pdf_library_missing',
                'message': 'PDF processing library not installed. Install: pip install pdf2image'
            }
        except Exception as e:
            return {
                'error': 'pdf_ocr_failed',
                'message': str(e)
            }
    
    def _calculate_average_confidence(self, ocr_data: Dict) -> float:
        """Calculate average OCR confidence"""
        confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
        return sum(confidences) / len(confidences) if confidences else 0
    
    def _extract_invoice_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract invoice data from OCR text"""
        import re
        
        data = {}
        
        # Extract total amount
        total_patterns = [
            r'toplam[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',  # Turkish: toplam (total)
            r'total[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',
            r'tutar[:\s]*([0-9.,]+)\s*(?:TL|₺|USD|\$|EUR|€)',  # Turkish: tutar (amount)
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['total_amount'] = match.group(1)
                break
        
        # Extract invoice number
        invoice_patterns = [
            r'fatura\s*(?:no|numarası)[:\s]*([A-Z0-9\-]+)',  # Turkish: fatura (invoice), numarası (number)
            r'invoice\s*(?:no|number)[:\s]*([A-Z0-9\-]+)',
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['invoice_number'] = match.group(1)
                break
        
        # Extract date
        date_patterns = [
            r'tarih[:\s]*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})',  # Turkish: tarih (date)
            r'date[:\s]*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['date'] = match.group(1)
                break
        
        return data
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported"""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_formats
