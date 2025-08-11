"""
Alternative search engines to avoid Google's rate limiting
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse
import time
import random

class AlternativeSearch:
    """Use alternative search engines to find content"""
    
    def __init__(self, proxy_dict=None):
        self.proxy_dict = proxy_dict
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def search_duckduckgo(self, query: str, num_results: int = 30) -> List[Dict]:
        """Search using DuckDuckGo HTML version"""
        results = []
        
        # DuckDuckGo HTML search
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        try:
            kwargs = {'headers': self.headers, 'timeout': 30}
            if self.proxy_dict:
                kwargs['proxies'] = self.proxy_dict
                kwargs['verify'] = False
            
            response = requests.get(url, **kwargs)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find search results
                for result in soup.find_all('div', class_='result'):
                    link_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if link_elem:
                        results.append({
                            'url': link_elem.get('href', ''),
                            'title': link_elem.text.strip(),
                            'snippet': snippet_elem.text.strip() if snippet_elem else ''
                        })
                        
                        if len(results) >= num_results:
                            break
                
                print(f"Found {len(results)} results from DuckDuckGo")
            else:
                print(f"DuckDuckGo returned status code: {response.status_code}")
                
        except Exception as e:
            print(f"Error searching DuckDuckGo: {e}")
        
        return results
    
    def search_searx(self, query: str, num_results: int = 30) -> List[Dict]:
        """Search using public Searx instances"""
        results = []
        
        # List of public Searx instances
        searx_instances = [
            'https://searx.be',
            'https://search.sapti.me',
            'https://searx.tiekoetter.com',
            'https://searx.work'
        ]
        
        # Try different instances
        for instance in searx_instances:
            try:
                url = f"{instance}/search?q={urllib.parse.quote(query)}&format=json"
                
                kwargs = {'headers': self.headers, 'timeout': 15}
                if self.proxy_dict:
                    kwargs['proxies'] = self.proxy_dict
                    kwargs['verify'] = False
                
                response = requests.get(url, **kwargs)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for result in data.get('results', [])[:num_results]:
                        results.append({
                            'url': result.get('url', ''),
                            'title': result.get('title', ''),
                            'snippet': result.get('content', '')
                        })
                    
                    if results:
                        print(f"Found {len(results)} results from Searx ({instance})")
                        break
                        
            except Exception as e:
                print(f"Error with Searx instance {instance}: {e}")
                continue
        
        return results
    
    def search_startpage(self, query: str, num_results: int = 30) -> List[Dict]:
        """Search using Startpage (Google results without tracking)"""
        results = []
        
        url = f"https://www.startpage.com/do/search?q={urllib.parse.quote(query)}"
        
        try:
            kwargs = {'headers': self.headers, 'timeout': 30}
            if self.proxy_dict:
                kwargs['proxies'] = self.proxy_dict
                kwargs['verify'] = False
            
            response = requests.get(url, **kwargs)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find search results
                for result in soup.find_all('div', class_='w-gl__result'):
                    link_elem = result.find('a', class_='w-gl__result-title')
                    snippet_elem = result.find('p', class_='w-gl__description')
                    
                    if link_elem:
                        results.append({
                            'url': link_elem.get('href', ''),
                            'title': link_elem.text.strip(),
                            'snippet': snippet_elem.text.strip() if snippet_elem else ''
                        })
                        
                        if len(results) >= num_results:
                            break
                
                print(f"Found {len(results)} results from Startpage")
                
        except Exception as e:
            print(f"Error searching Startpage: {e}")
        
        return results
    
    def search_all(self, query: str, num_results: int = 30) -> List[Dict]:
        """Search using all available search engines"""
        all_results = []
        
        # Try each search engine
        print(f"Searching for: {query}")
        
        # DuckDuckGo
        print("Trying DuckDuckGo...")
        results = self.search_duckduckgo(query, num_results)
        all_results.extend(results)
        time.sleep(random.uniform(1, 3))
        
        # If we don't have enough results, try Searx
        if len(all_results) < num_results:
            print("Trying Searx...")
            results = self.search_searx(query, num_results - len(all_results))
            all_results.extend(results)
            time.sleep(random.uniform(1, 3))
        
        # If still not enough, try Startpage
        if len(all_results) < num_results:
            print("Trying Startpage...")
            results = self.search_startpage(query, num_results - len(all_results))
            all_results.extend(results)
        
        # Remove duplicates based on URL
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            url = result['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results