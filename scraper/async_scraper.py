"""
Asynchronous scraper for high-volume data collection from LinkedIn and Glassdoor
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
import time

class AsyncScraper:
    """Asynchronous scraper for collecting large amounts of data"""
    
    def __init__(self, target_count: int = 1000):
        self.target_count = target_count
        self.ua = UserAgent()
        self.collected_posts = []
        self.keywords = {
            'people': ['Marc Benioff', 'Bret Taylor'],
            'products': ['Agentforce', 'Sierra.AI', 'Sierra AI'],
            'companies': ['Salesforce'],
            'general': ['AI', 'CRM agents', 'artificial intelligence']
        }
        
    async def fetch_with_retry(self, session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch URL with retry logic"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        for attempt in range(max_retries):
            try:
                async with session.get(url, headers=headers, timeout=30, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Rate limited
                        wait_time = (attempt + 1) * 5
                        print(f"Rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"Got status {response.status} for {url}")
            except Exception as e:
                print(f"Error fetching {url}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def search_duckduckgo(self, session: aiohttp.ClientSession, query: str, offset: int = 0) -> List[Dict]:
        """Search using DuckDuckGo with pagination"""
        results = []
        
        # DuckDuckGo HTML search with pagination
        url = f"https://html.duckduckgo.com/html/?q={query}&s={offset}"
        
        content = await self.fetch_with_retry(session, url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            for result in soup.find_all('div', class_='result'):
                link_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if link_elem:
                    results.append({
                        'url': link_elem.get('href', ''),
                        'title': link_elem.text.strip(),
                        'snippet': snippet_elem.text.strip() if snippet_elem else ''
                    })
        
        return results
    
    async def search_bing(self, session: aiohttp.ClientSession, query: str, offset: int = 0) -> List[Dict]:
        """Search using Bing"""
        results = []
        
        url = f"https://www.bing.com/search?q={query}&first={offset}"
        
        content = await self.fetch_with_retry(session, url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            for result in soup.find_all('li', class_='b_algo'):
                link_elem = result.find('h2').find('a') if result.find('h2') else None
                snippet_elem = result.find('div', class_='b_caption')
                
                if link_elem:
                    results.append({
                        'url': link_elem.get('href', ''),
                        'title': link_elem.text.strip(),
                        'snippet': snippet_elem.text.strip() if snippet_elem else ''
                    })
        
        return results
    
    async def collect_linkedin_posts(self, session: aiohttp.ClientSession, keyword: str, page: int) -> List[Dict]:
        """Collect LinkedIn posts for a specific keyword"""
        posts = []
        
        # Search queries for different content types
        queries = [
            f'site:linkedin.com/posts "{keyword}"',
            f'site:linkedin.com/pulse "{keyword}"',
            f'site:linkedin.com/in "{keyword}" "about"'
        ]
        
        for query in queries:
            offset = page * 30
            
            # Try multiple search engines
            results = await self.search_duckduckgo(session, query, offset)
            if not results:
                results = await self.search_bing(session, query, offset)
            
            for result in results:
                if 'linkedin.com' in result['url']:
                    post = self.parse_linkedin_result(result, keyword)
                    if post:
                        posts.append(post)
            
            # Small delay between queries
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return posts
    
    async def collect_glassdoor_reviews(self, session: aiohttp.ClientSession, company: str, page: int) -> List[Dict]:
        """Collect Glassdoor reviews for a specific company"""
        reviews = []
        
        queries = [
            f'site:glassdoor.com/Reviews "{company}" review employee',
            f'site:glassdoor.com "{company}" "pros and cons"',
            f'site:glassdoor.com/Interview "{company}"'
        ]
        
        for query in queries:
            offset = page * 30
            
            # Try multiple search engines
            results = await self.search_duckduckgo(session, query, offset)
            if not results:
                results = await self.search_bing(session, query, offset)
            
            for result in results:
                if 'glassdoor.com' in result['url']:
                    review = self.parse_glassdoor_result(result, company)
                    if review:
                        reviews.append(review)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return reviews
    
    def parse_linkedin_result(self, result: Dict, keyword: str) -> Optional[Dict]:
        """Parse LinkedIn search result"""
        url = result['url']
        title = result['title']
        snippet = result['snippet']
        
        # Extract keywords found
        keywords_found = self._extract_keywords(snippet + ' ' + title)
        if not keywords_found and keyword not in keywords_found:
            keywords_found.append(keyword)
        
        # Determine post type
        if '/pulse/' in url:
            post_type = 'article'
        elif '/posts/' in url:
            post_type = 'post'
        elif '/in/' in url:
            post_type = 'profile'
        else:
            post_type = 'other'
        
        # Extract author from title
        author = None
        if ' on LinkedIn' in title:
            author = title.split(' on LinkedIn')[0].strip()
        elif ' | LinkedIn' in title:
            author = title.split(' | LinkedIn')[0].strip()
        
        return {
            'platform': 'linkedin',
            'post_type': post_type,
            'url': url,
            'title': title,
            'author': author,
            'content': snippet,
            'keywords_found': keywords_found,
            'timestamp': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            'scraped_at': datetime.utcnow()
        }
    
    def parse_glassdoor_result(self, result: Dict, company: str) -> Optional[Dict]:
        """Parse Glassdoor search result"""
        url = result['url']
        title = result['title']
        snippet = result['snippet']
        
        # Extract keywords found
        keywords_found = self._extract_keywords(snippet + ' ' + title)
        if company not in keywords_found:
            keywords_found.append(company)
        
        # Determine review type
        if '/Reviews/' in url:
            post_type = 'review'
        elif '/Interview/' in url:
            post_type = 'interview'
        elif '/Salary/' in url:
            post_type = 'salary'
        else:
            post_type = 'other'
        
        # Extract rating if present
        rating = None
        import re
        rating_match = re.search(r'(\d+\.?\d*)\s*stars?', snippet, re.IGNORECASE)
        if rating_match:
            rating = float(rating_match.group(1))
        
        return {
            'platform': 'glassdoor',
            'post_type': post_type,
            'url': url,
            'title': title,
            'author': 'Anonymous Employee',
            'content': snippet,
            'keywords_found': keywords_found,
            'company': company,
            'rating': rating,
            'timestamp': datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            'scraped_at': datetime.utcnow()
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract monitored keywords from text"""
        found_keywords = []
        text_lower = text.lower()
        
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    async def collect_all_data(self) -> List[Dict]:
        """Main method to collect all data asynchronously"""
        print(f"Starting async collection of {self.target_count} posts...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # LinkedIn tasks
            linkedin_keywords = ['Marc Benioff', 'Agentforce', 'Bret Taylor', 'Salesforce AI', 'CRM agents']
            for keyword in linkedin_keywords:
                for page in range(10):  # 10 pages per keyword
                    task = self.collect_linkedin_posts(session, keyword, page)
                    tasks.append(task)
            
            # Glassdoor tasks
            glassdoor_companies = ['Salesforce', 'Sierra AI', 'Sierra.AI']
            for company in glassdoor_companies:
                for page in range(10):  # 10 pages per company
                    task = self.collect_glassdoor_reviews(session, company, page)
                    tasks.append(task)
            
            # Execute all tasks concurrently with limited concurrency
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
            
            async def bounded_task(task):
                async with semaphore:
                    return await task
            
            bounded_tasks = [bounded_task(task) for task in tasks]
            
            # Gather results with progress tracking
            results = []
            for i, coro in enumerate(asyncio.as_completed(bounded_tasks)):
                try:
                    batch_results = await coro
                    results.extend(batch_results)
                    
                    # Progress update
                    if i % 10 == 0:
                        print(f"Progress: {len(results)} posts collected...")
                    
                    # Stop if we have enough
                    if len(results) >= self.target_count:
                        break
                        
                except Exception as e:
                    print(f"Task error: {str(e)[:100]}")
            
            # Flatten results
            all_posts = []
            for batch in results:
                if isinstance(batch, list):
                    all_posts.extend(batch)
                elif batch:
                    all_posts.append(batch)
            
            # Remove duplicates based on URL
            unique_posts = []
            seen_urls = set()
            
            for post in all_posts:
                if post and post.get('url') not in seen_urls:
                    seen_urls.add(post['url'])
                    unique_posts.append(post)
            
            self.collected_posts = unique_posts[:self.target_count]
            
        print(f"Collected {len(self.collected_posts)} unique posts")
        return self.collected_posts
    
    def save_to_csv(self, filename: str = 'scraped_data.csv'):
        """Save collected data to CSV"""
        if not self.collected_posts:
            print("No data to save")
            return
        
        df = pd.DataFrame(self.collected_posts)
        
        # Convert lists to strings for CSV
        if 'keywords_found' in df.columns:
            df['keywords_found'] = df['keywords_found'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} posts to {filename}")
    
    def save_to_json(self, filename: str = 'scraped_data.json'):
        """Save collected data to JSON"""
        if not self.collected_posts:
            print("No data to save")
            return
        
        # Convert datetime objects to strings
        for post in self.collected_posts:
            if isinstance(post.get('timestamp'), datetime):
                post['timestamp'] = post['timestamp'].isoformat()
            if isinstance(post.get('scraped_at'), datetime):
                post['scraped_at'] = post['scraped_at'].isoformat()
        
        with open(filename, 'w') as f:
            json.dump(self.collected_posts, f, indent=2)
        
        print(f"Saved {len(self.collected_posts)} posts to {filename}")

async def main():
    """Main function to run the async scraper"""
    scraper = AsyncScraper(target_count=1000)
    
    start_time = time.time()
    posts = await scraper.collect_all_data()
    end_time = time.time()
    
    print(f"\nCollection completed in {end_time - start_time:.2f} seconds")
    print(f"Total posts collected: {len(posts)}")
    
    # Save data
    scraper.save_to_csv('linkedin_glassdoor_data.csv')
    scraper.save_to_json('linkedin_glassdoor_data.json')
    
    # Show sample
    if posts:
        print("\nSample posts:")
        for post in posts[:3]:
            print(f"- {post['platform']}: {post['title'][:80]}...")
            print(f"  Keywords: {post.get('keywords_found', [])}")

if __name__ == "__main__":
    asyncio.run(main())