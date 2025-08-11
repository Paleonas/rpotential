import re
import urllib.parse
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import json
from .base_scraper import BaseScraper
from .alternative_search import AlternativeSearch

class GlassdoorScraper(BaseScraper):
    """Scraper for Glassdoor reviews and posts"""
    
    def __init__(self):
        super().__init__('glassdoor')
        self.base_url = 'https://www.glassdoor.com'
        
        # Glassdoor specific headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
    
    def scrape(self, search_query: Optional[str] = None) -> List[Dict]:
        """Scrape Glassdoor for reviews mentioning our keywords"""
        results = []
        
        # Focus on Salesforce company reviews
        companies_to_check = ['Salesforce', 'Sierra AI', 'Sierra.AI']
        
        for company in companies_to_check:
            print(f"Searching Glassdoor for {company} reviews...")
            results.extend(self._scrape_company_reviews_alternative(company))
        
        # Also search for general mentions
        if not search_query:
            keywords_to_search = ['Marc Benioff', 'Agentforce', 'Bret Taylor']
            for keyword in keywords_to_search:
                results.extend(self._scrape_mentions_alternative(keyword))
        else:
            results.extend(self._scrape_mentions_alternative(search_query))
        
        # Save results to database
        if results:
            self.save_results(results)
        
        return results
    
    def _scrape_company_reviews_alternative(self, company: str) -> List[Dict]:
        """Scrape company reviews via alternative search engines"""
        results = []
        
        # Build search query for Glassdoor reviews
        search_query = f'site:glassdoor.com/Reviews "{company}" review employee'
        
        # Get proxy if available
        proxy_dict = self._get_proxy_for_request()
        
        # Use alternative search
        searcher = AlternativeSearch(proxy_dict)
        search_results = searcher.search_all(search_query, num_results=30)
        
        # Parse search results
        for result in search_results:
            url = result['url']
            
            if 'glassdoor.com' not in url or '/Reviews/' not in url:
                continue
            
            title = result['title']
            snippet = result['snippet']
            
            # Check if snippet contains our keywords or is relevant
            keywords_found = self._extract_keywords(snippet)
            if not keywords_found and company.lower() not in snippet.lower():
                continue
            
            # Try to extract review metadata from snippet
            rating = self._extract_rating_from_snippet(snippet)
            date = self._extract_date_from_snippet(snippet)
            
            results.append({
                'platform': self.platform,
                'post_type': 'review',
                'url': url,
                'author': 'Anonymous Employee',  # Glassdoor reviews are usually anonymous
                'author_title': self._extract_job_title_from_snippet(snippet),
                'content': snippet,
                'timestamp': date,
                'keywords_found': keywords_found or [company],
                'likes': None,
                'comments': None,
                'shares': None,
                'company': company,
                'location': None,
                'is_verified': True,  # Glassdoor verifies employees
                'rating': rating
            })
        
        print(f"Found {len(results)} Glassdoor reviews for {company}")
        return results
    
    def _scrape_mentions_alternative(self, keyword: str) -> List[Dict]:
        """Scrape general mentions via alternative search engines"""
        results = []
        
        # Build search query
        search_query = f'site:glassdoor.com "{keyword}"'
        
        # Get proxy if available
        proxy_dict = self._get_proxy_for_request()
        
        # Use alternative search
        searcher = AlternativeSearch(proxy_dict)
        search_results = searcher.search_all(search_query, num_results=20)
        
        # Parse search results
        for result in search_results:
            url = result['url']
            
            if 'glassdoor.com' not in url:
                continue
            
            title = result['title']
            snippet = result['snippet']
            
            # Check if snippet contains our keywords
            keywords_found = self._extract_keywords(snippet)
            if not keywords_found:
                continue
            
            # Determine post type
            if '/Reviews/' in url:
                post_type = 'review'
            elif '/Interview/' in url:
                post_type = 'interview'
            elif '/Salary/' in url:
                post_type = 'salary'
            else:
                post_type = 'post'
            
            results.append({
                'platform': self.platform,
                'post_type': post_type,
                'url': url,
                'author': 'Glassdoor User',
                'author_title': None,
                'content': snippet,
                'timestamp': None,
                'keywords_found': keywords_found,
                'likes': None,
                'comments': None,
                'shares': None,
                'company': self._extract_company_from_url(url),
                'location': None,
                'is_verified': False
            })
        
        return results
    
    def _extract_rating_from_snippet(self, snippet: str) -> Optional[float]:
        """Extract rating from review snippet"""
        # Look for patterns like "4.5 stars" or "Rating: 4.5"
        patterns = [
            r'(\d+\.?\d*)\s*stars?',
            r'Rating:\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)/5'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                try:
                    rating = float(match.group(1))
                    if 0 <= rating <= 5:
                        return rating
                except ValueError:
                    pass
        
        return None
    
    def _extract_date_from_snippet(self, snippet: str) -> Optional[datetime]:
        """Extract date from review snippet"""
        # Look for date patterns
        patterns = [
            r'(\w+\s+\d+,\s+\d{4})',  # Jan 1, 2024
            r'(\d+/\d+/\d{4})',        # 01/01/2024
            r'(\d{4}-\d{2}-\d{2})'     # 2024-01-01
        ]
        
        for pattern in patterns:
            match = re.search(pattern, snippet)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _extract_job_title_from_snippet(self, snippet: str) -> Optional[str]:
        """Extract job title from review snippet"""
        # Look for patterns like "Current Employee - Software Engineer"
        patterns = [
            r'(?:Current|Former)\s+Employee\s*-\s*([^,\n]+)',
            r'(?:I work|worked)\s+as\s+(?:a|an)\s+([^,\n]+)',
            r'Position:\s*([^,\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_company_from_url(self, url: str) -> Optional[str]:
        """Extract company name from Glassdoor URL"""
        # Pattern: /Reviews/Company-Name-Reviews-E12345.htm
        match = re.search(r'/Reviews/([^-]+)-Reviews-E\d+', url)
        if match:
            return match.group(1).replace('-', ' ')
        
        return None
    
    def parse_post(self, post_element) -> Optional[Dict]:
        """Parse individual Glassdoor post element"""
        # This would be implemented if we had direct access to Glassdoor HTML
        # For now, this is handled in the scraping methods above
        pass