#!/usr/bin/env python3
"""
Main scraper runner script
Run this to execute all scrapers and collect data
"""

import sys
import os
from datetime import datetime
from typing import List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, SessionLocal, ScrapeSession
from scraper.linkedin_scraper import LinkedInScraper
from scraper.glassdoor_scraper import GlassdoorScraper

def run_scraper(platform: str = None) -> Dict:
    """Run scrapers for specified platform or all platforms"""
    # Initialize database
    init_db()
    
    results = {
        'total_posts': 0,
        'platforms': {}
    }
    
    # Determine which scrapers to run
    scrapers = []
    if platform == 'linkedin' or platform is None:
        scrapers.append(LinkedInScraper())
    if platform == 'glassdoor' or platform is None:
        scrapers.append(GlassdoorScraper())
    
    # Run each scraper
    for scraper in scrapers:
        print(f"\n{'='*50}")
        print(f"Running {scraper.platform} scraper...")
        print(f"{'='*50}")
        
        # Create scrape session
        db = SessionLocal()
        session = ScrapeSession(
            platform=scraper.platform,
            status='running'
        )
        db.add(session)
        db.commit()
        
        try:
            # Run the scraper
            posts = scraper.scrape()
            
            # Update session
            session.status = 'completed'
            session.posts_scraped = len(posts)
            session.ended_at = datetime.utcnow()
            
            # Store results
            results['platforms'][scraper.platform] = {
                'posts_found': len(posts),
                'status': 'success'
            }
            results['total_posts'] += len(posts)
            
            print(f"\n✓ {scraper.platform} scraping completed: {len(posts)} posts found")
            
        except Exception as e:
            # Update session with error
            session.status = 'failed'
            session.error_message = str(e)
            session.ended_at = datetime.utcnow()
            
            results['platforms'][scraper.platform] = {
                'posts_found': 0,
                'status': 'failed',
                'error': str(e)
            }
            
            print(f"\n✗ {scraper.platform} scraping failed: {e}")
        
        finally:
            db.commit()
            db.close()
    
    return results

def print_summary(results: Dict):
    """Print summary of scraping results"""
    print(f"\n{'='*50}")
    print("SCRAPING SUMMARY")
    print(f"{'='*50}")
    print(f"Total posts collected: {results['total_posts']}")
    
    for platform, data in results['platforms'].items():
        status_icon = "✓" if data['status'] == 'success' else "✗"
        print(f"{status_icon} {platform}: {data['posts_found']} posts")
        if 'error' in data:
            print(f"  Error: {data['error']}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run social media scrapers')
    parser.add_argument(
        '--platform',
        choices=['linkedin', 'glassdoor'],
        help='Specific platform to scrape (default: all)'
    )
    parser.add_argument(
        '--query',
        help='Specific search query (default: use all keywords)'
    )
    
    args = parser.parse_args()
    
    print("Starting social media monitoring scraper...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run scrapers
    results = run_scraper(args.platform)
    
    # Print summary
    print_summary(results)
    
    print("\nScraping completed!")

if __name__ == '__main__':
    main()