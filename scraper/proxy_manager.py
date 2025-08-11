"""
Proxy Manager for handling free proxy rotation
"""

import requests
import random
import time
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import concurrent.futures
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings when using proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxyManager:
    """Manages free proxy rotation for web scraping"""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.last_fetch = None
        self.fetch_interval = timedelta(hours=1)  # Refresh proxy list every hour
        
    def fetch_proxies(self) -> List[Dict]:
        """Fetch free proxies from multiple sources"""
        all_proxies = []
        
        # Source 1: Free Proxy List API
        try:
            print("Fetching proxies from free-proxy-list...")
            proxies = self._fetch_from_free_proxy_list()
            all_proxies.extend(proxies)
        except Exception as e:
            print(f"Error fetching from free-proxy-list: {e}")
        
        # Source 2: ProxyScrape API
        try:
            print("Fetching proxies from ProxyScrape...")
            proxies = self._fetch_from_proxyscrape()
            all_proxies.extend(proxies)
        except Exception as e:
            print(f"Error fetching from ProxyScrape: {e}")
        
        # Source 3: SSLProxies
        try:
            print("Fetching proxies from SSLProxies...")
            proxies = self._fetch_from_sslproxies()
            all_proxies.extend(proxies)
        except Exception as e:
            print(f"Error fetching from SSLProxies: {e}")
        
        # Remove duplicates
        unique_proxies = []
        seen = set()
        for proxy in all_proxies:
            proxy_str = f"{proxy['ip']}:{proxy['port']}"
            if proxy_str not in seen:
                seen.add(proxy_str)
                unique_proxies.append(proxy)
        
        print(f"Fetched {len(unique_proxies)} unique proxies")
        return unique_proxies
    
    def _fetch_from_free_proxy_list(self) -> List[Dict]:
        """Fetch proxies from free-proxy-list.net"""
        proxies = []
        url = "https://www.free-proxy-list.net/"
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the proxy table
            table = soup.find('table', {'id': 'proxylisttable'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows[:50]:  # Limit to 50 proxies
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        proxy = {
                            'ip': cols[0].text.strip(),
                            'port': cols[1].text.strip(),
                            'country': cols[3].text.strip(),
                            'anonymity': cols[4].text.strip(),
                            'https': cols[6].text.strip() == 'yes',
                            'source': 'free-proxy-list'
                        }
                        proxies.append(proxy)
        except Exception as e:
            print(f"Error parsing free-proxy-list: {e}")
        
        return proxies
    
    def _fetch_from_proxyscrape(self) -> List[Dict]:
        """Fetch proxies from ProxyScrape API"""
        proxies = []
        url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&format=json"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'proxies' in data:
                for proxy_data in data['proxies'][:50]:  # Limit to 50
                    proxy = {
                        'ip': proxy_data.get('ip', ''),
                        'port': str(proxy_data.get('port', '')),
                        'country': proxy_data.get('country', 'Unknown'),
                        'anonymity': proxy_data.get('anonymity', 'Unknown'),
                        'https': proxy_data.get('ssl', False),
                        'source': 'proxyscrape'
                    }
                    if proxy['ip'] and proxy['port']:
                        proxies.append(proxy)
        except Exception as e:
            print(f"Error fetching from ProxyScrape: {e}")
        
        return proxies
    
    def _fetch_from_sslproxies(self) -> List[Dict]:
        """Fetch proxies from sslproxies.org"""
        proxies = []
        url = "https://www.sslproxies.org/"
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the proxy table
            table = soup.find('table', {'class': 'table'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows[:30]:  # Limit to 30 proxies
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        proxy = {
                            'ip': cols[0].text.strip(),
                            'port': cols[1].text.strip(),
                            'country': cols[3].text.strip(),
                            'anonymity': cols[4].text.strip(),
                            'https': True,  # SSL proxies
                            'source': 'sslproxies'
                        }
                        proxies.append(proxy)
        except Exception as e:
            print(f"Error parsing sslproxies: {e}")
        
        return proxies
    
    def test_proxy(self, proxy: Dict) -> bool:
        """Test if a proxy is working"""
        proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        test_urls = [
            'http://httpbin.org/ip',
            'https://api.ipify.org?format=json'
        ]
        
        for test_url in test_urls:
            try:
                response = requests.get(
                    test_url,
                    proxies=proxies,
                    timeout=5,
                    verify=False
                )
                if response.status_code == 200:
                    return True
            except:
                continue
        
        return False
    
    def test_proxies_parallel(self, proxies: List[Dict], max_workers: int = 20) -> List[Dict]:
        """Test multiple proxies in parallel"""
        working_proxies = []
        
        print(f"Testing {len(proxies)} proxies...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all proxy tests
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy): proxy 
                for proxy in proxies
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        working_proxies.append(proxy)
                        print(f"✓ Working proxy found: {proxy['ip']}:{proxy['port']}")
                except Exception as e:
                    pass
        
        print(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    def refresh_proxies(self):
        """Refresh the proxy list"""
        print("Refreshing proxy list...")
        
        # Fetch new proxies
        all_proxies = self.fetch_proxies()
        
        # Test proxies in parallel
        self.working_proxies = self.test_proxies_parallel(all_proxies)
        
        # Update last fetch time
        self.last_fetch = datetime.now()
        
        # Save working proxies to file
        self.save_proxies()
    
    def get_proxy(self) -> Optional[Dict]:
        """Get a random working proxy"""
        # Refresh if needed
        if not self.working_proxies or (
            self.last_fetch and 
            datetime.now() - self.last_fetch > self.fetch_interval
        ):
            self.refresh_proxies()
        
        if self.working_proxies:
            return random.choice(self.working_proxies)
        
        return None
    
    def get_proxy_dict(self, proxy: Dict) -> Dict:
        """Convert proxy to requests format"""
        if not proxy:
            return {}
        
        proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def remove_proxy(self, proxy: Dict):
        """Remove a non-working proxy from the list"""
        self.working_proxies = [
            p for p in self.working_proxies 
            if p['ip'] != proxy['ip'] or p['port'] != proxy['port']
        ]
    
    def save_proxies(self):
        """Save working proxies to file"""
        try:
            with open('working_proxies.json', 'w') as f:
                json.dump(self.working_proxies, f, indent=2)
        except Exception as e:
            print(f"Error saving proxies: {e}")
    
    def load_proxies(self):
        """Load working proxies from file"""
        try:
            with open('working_proxies.json', 'r') as f:
                self.working_proxies = json.load(f)
                print(f"Loaded {len(self.working_proxies)} proxies from file")
        except:
            self.working_proxies = []

# Singleton instance
proxy_manager = ProxyManager()