import time
import random
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
from dotenv import load_dotenv
from .proxy_manager import proxy_manager

load_dotenv()

class BaseScraper(ABC):
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.ua = UserAgent()
        self.session = requests.Session()
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', 2))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
        self.use_proxy = os.getenv('USE_PROXY', 'false').lower() == 'true'
        self.proxy_url = os.getenv('PROXY_URL', '')
        
        # Keywords to monitor
        self.keywords = {
            'people': ['Marc Benioff', 'Bret Taylor'],
            'products': ['Agentforce', 'Sierra.AI', 'Sierra AI'],
            'companies': ['Salesforce'],
            'general': ['AI', 'CRM agents', 'artificial intelligence']
        }
        
        # Initialize proxy manager if needed
        if self.use_proxy and not self.proxy_url:
            # Load existing proxies or fetch new ones
            proxy_manager.load_proxies()
            if not proxy_manager.working_proxies:
                print("No saved proxies found. Fetching new proxies...")
                proxy_manager.refresh_proxies()
        
        # Setup session
        self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with headers and proxy"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Use manual proxy if specified
        if self.use_proxy and self.proxy_url:
            self.session.proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
    
    def _get_proxy_for_request(self) -> Optional[Dict]:
        """Get a proxy for the current request"""
        if not self.use_proxy:
            return None
        
        if self.proxy_url:
            # Use manual proxy
            return {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
        else:
            # Use proxy manager
            proxy = proxy_manager.get_proxy()
            if proxy:
                return proxy_manager.get_proxy_dict(proxy)
        
        return None
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        delay = self.rate_limit_delay + random.uniform(0, 1)
        time.sleep(delay)
    
    def _retry_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and proxy rotation"""
        last_proxy = None
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                
                # Get proxy for this request
                proxies = self._get_proxy_for_request()
                
                # Update kwargs with proxy if available
                if proxies:
                    kwargs['proxies'] = proxies
                    kwargs['verify'] = False  # Disable SSL verification for proxies
                    print(f"Using proxy: {list(proxies.values())[0]}")
                
                if method == 'GET':
                    response = self.session.get(url, timeout=self.timeout, **kwargs)
                else:
                    response = self.session.post(url, timeout=self.timeout, **kwargs)
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.ProxyError as e:
                print(f"Proxy error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                # Remove bad proxy if using proxy manager
                if proxies and not self.proxy_url:
                    # Extract proxy info from the proxy dict
                    proxy_url = list(proxies.values())[0]
                    if '://' in proxy_url:
                        proxy_parts = proxy_url.split('://')[1].split(':')
                        if len(proxy_parts) == 2:
                            bad_proxy = {'ip': proxy_parts[0], 'port': proxy_parts[1]}
                            proxy_manager.remove_proxy(bad_proxy)
                            print(f"Removed bad proxy: {proxy_url}")
                
                # Try again with a different proxy
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract monitored keywords from text"""
        found_keywords = []
        text_lower = text.lower()
        
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        # Common date patterns
        patterns = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for pattern in patterns:
            try:
                return datetime.strptime(date_str.strip(), pattern)
            except ValueError:
                continue
        
        # Handle relative dates like "2 days ago"
        if 'ago' in date_str.lower():
            return self._parse_relative_date(date_str)
        
        return None
    
    def _parse_relative_date(self, date_str: str) -> Optional[datetime]:
        """Parse relative dates like '2 days ago'"""
        import re
        from datetime import timedelta
        
        now = datetime.utcnow()
        
        # Extract number and unit
        match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', date_str.lower())
        if not match:
            return None
        
        num = int(match.group(1))
        unit = match.group(2)
        
        if unit in ['second', 'seconds']:
            return now - timedelta(seconds=num)
        elif unit in ['minute', 'minutes']:
            return now - timedelta(minutes=num)
        elif unit in ['hour', 'hours']:
            return now - timedelta(hours=num)
        elif unit in ['day', 'days']:
            return now - timedelta(days=num)
        elif unit in ['week', 'weeks']:
            return now - timedelta(weeks=num)
        elif unit in ['month', 'months']:
            return now - timedelta(days=num * 30)  # Approximate
        elif unit in ['year', 'years']:
            return now - timedelta(days=num * 365)  # Approximate
        
        return None
    
    def get_page_content(self, url: str, use_js: bool = False) -> Optional[str]:
        """Get page content"""
        if use_js:
            print("JavaScript rendering not available in this version")
            return None
        else:
            response = self._retry_request(url)
            return response.text if response else None
    
    @abstractmethod
    def scrape(self, search_query: Optional[str] = None) -> List[Dict]:
        """Main scraping method to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def parse_post(self, post_element) -> Optional[Dict]:
        """Parse individual post/review element"""
        pass
    
    def save_results(self, results: List[Dict]) -> int:
        """Save scraped results to database"""
        from models.database import SessionLocal, ScrapedPost, Keyword
        
        db = SessionLocal()
        saved_count = 0
        
        try:
            for result in results:
                # Check if post already exists
                existing = db.query(ScrapedPost).filter_by(url=result.get('url')).first()
                if existing:
                    continue
                
                # Create new post
                post = ScrapedPost(
                    platform=self.platform,
                    post_type=result.get('post_type'),
                    url=result.get('url'),
                    author=result.get('author'),
                    author_title=result.get('author_title'),
                    content=result.get('content'),
                    timestamp=result.get('timestamp'),
                    keywords_found=json.dumps(result.get('keywords_found', [])),
                    likes=result.get('likes'),
                    comments=result.get('comments'),
                    shares=result.get('shares'),
                    company=result.get('company'),
                    location=result.get('location'),
                    is_verified=result.get('is_verified', False)
                )
                
                db.add(post)
                saved_count += 1
                
                # Update keyword counts
                for keyword in result.get('keywords_found', []):
                    kw = db.query(Keyword).filter_by(keyword=keyword).first()
                    if kw:
                        kw.total_mentions += 1
                        kw.last_seen = datetime.utcnow()
                    else:
                        kw = Keyword(
                            keyword=keyword,
                            category=self._get_keyword_category(keyword),
                            total_mentions=1,
                            last_seen=datetime.utcnow()
                        )
                        db.add(kw)
            
            db.commit()
            print(f"Saved {saved_count} new posts from {self.platform}")
            
        except Exception as e:
            print(f"Error saving results: {e}")
            db.rollback()
            
        finally:
            db.close()
        
        return saved_count
    
    def _get_keyword_category(self, keyword: str) -> str:
        """Get category for a keyword"""
        for category, keywords in self.keywords.items():
            if keyword in keywords:
                return category
        return 'general'