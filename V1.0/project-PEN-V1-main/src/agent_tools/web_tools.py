"""
Agent için web search ve scraping tool'ları
"""

import json
import requests
from typing import Optional, Dict, List
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class WebTools:
    """Agent için web araçları"""
    
    def __init__(self, brave_api_key: Optional[str] = None):
        """
        WebTools başlat
        
        Args:
            brave_api_key: Brave Search API key (opsiyonel)
        """
        self.brave_api_key = brave_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_web(self, query: str, limit: int = 5) -> str:
        """
        Web'de arama yap (Brave Search API veya fallback)
        
        Args:
            query: Arama sorgusu
            limit: Maksimum sonuç sayısı
        
        Returns:
            JSON formatında arama sonuçları
        """
        try:
            # Brave Search API varsa kullan
            if self.brave_api_key:
                return self._search_brave(query, limit)
            else:
                # Fallback: DuckDuckGo HTML scraping
                return self._search_duckduckgo(query, limit)
        
        except Exception as e:
            logger.error(f"Web search hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def _search_brave(self, query: str, limit: int) -> str:
        """Brave Search API ile arama"""
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": query,
                "count": limit
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Web sonuçlarını parse et
            for item in data.get('web', {}).get('results', [])[:limit]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'description': item.get('description', ''),
                    'published': item.get('age', '')
                })
            
            result = {
                "status": "success",
                "query": query,
                "total_results": len(results),
                "results": results,
                "source": "brave_search"
            }
            
            logger.info(f"Agent: '{query}' için {len(results)} sonuç bulundu (Brave)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Brave search hatası: {e}")
            # Fallback to DuckDuckGo
            return self._search_duckduckgo(query, limit)
    
    def _search_duckduckgo(self, query: str, limit: int) -> str:
        """DuckDuckGo HTML scraping ile arama (fallback)"""
        try:
            # DuckDuckGo Instant Answer API (ücretsiz, rate limit var)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Abstract (özet cevap)
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', query),
                    'url': data.get('AbstractURL', ''),
                    'description': data.get('Abstract', ''),
                    'source': data.get('AbstractSource', '')
                })
            
            # Related topics
            for topic in data.get('RelatedTopics', [])[:limit-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'url': topic.get('FirstURL', ''),
                        'description': topic.get('Text', ''),
                        'source': 'DuckDuckGo'
                    })
            
            result = {
                "status": "success",
                "query": query,
                "total_results": len(results),
                "results": results,
                "source": "duckduckgo",
                "note": "Ücretsiz API - sınırlı sonuçlar. Brave API key ekleyin."
            }
            
            logger.info(f"Agent: '{query}' için {len(results)} sonuç bulundu (DuckDuckGo)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"DuckDuckGo search hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Arama başarısız: {str(e)}",
                "suggestion": "Brave Search API key ekleyin (.env dosyasına BRAVE_API_KEY)"
            })
    
    def fetch_webpage(self, url: str, max_length: int = 5000) -> str:
        """
        Web sayfasını çek ve içeriğini getir
        
        Args:
            url: Web sayfası URL'i
            max_length: Maksimum içerik uzunluğu
        
        Returns:
            JSON formatında sayfa içeriği
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # HTML'i temizle (basit text extraction)
            from html.parser import HTMLParser
            
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                
                def handle_data(self, data):
                    if data.strip():
                        self.text.append(data.strip())
            
            parser = TextExtractor()
            parser.feed(response.text)
            
            content = ' '.join(parser.text)
            
            # Uzunluk limiti
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            result = {
                "status": "success",
                "url": url,
                "content_length": len(content),
                "content": content,
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.info(f"Agent: Web sayfası çekildi - {url}")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Webpage fetch hatası: {e}")
            return json.dumps({
                "status": "error",
                "url": url,
                "message": str(e)
            })
    
    def get_current_time(self) -> str:
        """
        Güncel tarih ve saat bilgisi
        
        Returns:
            JSON formatında zaman bilgisi
        """
        try:
            now = datetime.now()
            
            result = {
                "status": "success",
                "current_time": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "day_of_week_tr": self._get_turkish_day(now.strftime("%A")),
                "formatted": now.strftime("%d %B %Y, %H:%M"),
                "formatted_tr": self._format_turkish_date(now),
                "timestamp": int(now.timestamp())
            }
            
            logger.info("Agent: Güncel zaman bilgisi alındı")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Time tool hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def _get_turkish_day(self, english_day: str) -> str:
        """İngilizce gün adını Türkçe'ye çevir"""
        days = {
            "Monday": "Pazartesi",
            "Tuesday": "Salı",
            "Wednesday": "Çarşamba",
            "Thursday": "Perşembe",
            "Friday": "Cuma",
            "Saturday": "Cumartesi",
            "Sunday": "Pazar"
        }
        return days.get(english_day, english_day)
    
    def _format_turkish_date(self, dt: datetime) -> str:
        """Tarihi Türkçe formatla"""
        months = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
            5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
            9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        
        day = dt.day
        month = months[dt.month]
        year = dt.year
        time = dt.strftime("%H:%M")
        day_name = self._get_turkish_day(dt.strftime("%A"))
        
        return f"{day} {month} {year} {day_name}, {time}"


def get_web_tools_description() -> str:
    """
    Web tool'larının açıklamasını döndür
    
    Returns:
        Tool açıklamaları
    """
    return """
# Agent Web Tool'ları

## 1. search_web(query, limit=5)
Web'de arama yapar (Brave Search veya DuckDuckGo).

**Parametreler**:
- query: Arama sorgusu (zorunlu)
- limit: Maksimum sonuç sayısı (varsayılan: 5)

**Örnek**:
```python
web_tools.search_web("Python async programming", limit=3)
```

## 2. fetch_webpage(url, max_length=5000)
Web sayfasını çeker ve içeriğini getirir.

**Parametreler**:
- url: Web sayfası URL'i (zorunlu)
- max_length: Maksimum içerik uzunluğu (varsayılan: 5000)

**Örnek**:
```python
web_tools.fetch_webpage("https://example.com/article")
```

## 3. get_current_time()
Güncel tarih ve saat bilgisi.

**Parametreler**: Yok

**Örnek**:
```python
web_tools.get_current_time()
```

## Notlar:
- Brave Search API key varsa daha iyi sonuçlar
- .env dosyasına BRAVE_API_KEY ekleyin
- Fallback olarak DuckDuckGo kullanılır
"""
