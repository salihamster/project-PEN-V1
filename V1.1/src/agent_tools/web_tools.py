"""
Web search and scraping tools for the agent
"""

import json
import requests
from typing import Optional, Dict, List
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class WebTools:
    """Web tools for the agent"""
    
    def __init__(self, brave_api_key: Optional[str] = None):
        """
        Initialize WebTools
        
        Args:
            brave_api_key: Brave Search API key (optional)
        """
        self.brave_api_key = brave_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_web(self, query: str, limit: int = 5) -> str:
        """
        Search the web (Brave Search API or fallback)
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            Search results in JSON format
        """
        try:
            # Ensure limit is an integer
            try:
                limit = int(limit) if limit is not None else 5
            except (ValueError, TypeError):
                limit = 5
            
            # Brave Search API varsa kullan
            if self.brave_api_key:
                return self._search_brave(query, limit)
            else:
                # Fallback: DuckDuckGo HTML scraping
                return self._search_duckduckgo(query, limit)
        
        except Exception as e:
            logger.error(f"Web search error: {e}")
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
            
            # Parse web results
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
            
            logger.info(f"Agent: Found {len(results)} results for '{query}' (Brave)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Brave search error: {e}")
            # Fallback to DuckDuckGo
            return self._search_duckduckgo(query, limit)
    
    def _search_duckduckgo(self, query: str, limit: int) -> str:
        """DuckDuckGo search via HTML scraping (fallback)"""
        try:
            # DuckDuckGo Instant Answer API (free, rate limited)
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
            
            # Abstract (summary answer)
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
                "note": "Free API - limited results. Add Brave API key for better results."
            }
            
            logger.info(f"Agent: Found {len(results)} results for '{query}' (DuckDuckGo)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Search failed: {str(e)}",
                "suggestion": "Add Brave Search API key to .env file (BRAVE_API_KEY)"
            })
    
    def fetch_webpage(self, url: str, max_length: int = 5000) -> str:
        """
        Fetch webpage and get its content
        
        Args:
            url: Web page URL
            max_length: Maximum content length
        
        Returns:
            Page content in JSON format
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
            
            logger.info(f"Agent: Webpage fetched - {url}")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Webpage fetch error: {e}")
            return json.dumps({
                "status": "error",
                "url": url,
                "message": str(e)
            })
    
    def get_current_time(self) -> str:
        """
        Get current date and time
        
        Returns:
            Time information in JSON format
        """
        try:
            now = datetime.now()
            
            result = {
                "status": "success",
                "current_time": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "formatted": now.strftime("%d %B %Y, %H:%M"),
                "timestamp": int(now.timestamp())
            }
            
            logger.info("Agent: Current time retrieved")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Time tool error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })


def get_web_tools_description() -> str:
    """
    Get description of web tools
    
    Returns:
        Tool descriptions
    """
    return """
# Agent Web Tools

## 1. search_web(query, limit=5)
Searches the web (Brave Search or DuckDuckGo).

**Parameters**:
- query: Search query (required)
- limit: Maximum number of results (default: 5)

**Example**:
```python
web_tools.search_web("Python async programming", limit=3)
```

## 2. fetch_webpage(url, max_length=5000)
Fetches webpage and returns its content.

**Parameters**:
- url: Web page URL (required)
- max_length: Maximum content length (default: 5000)

**Example**:
```python
web_tools.fetch_webpage("https://example.com/article")
```

## 3. get_current_time()
Gets current date and time.

**Parameters**: None

**Example**:
```python
web_tools.get_current_time()
```

## Notes:
- Better results with Brave Search API key
- Add BRAVE_API_KEY to .env file
- Falls back to DuckDuckGo if no API key
"""
