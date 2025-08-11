#!/usr/bin/env python3
"""
Main script to run async data collection and analysis
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.async_scraper import AsyncScraper
from scraper.ai_analyzer import analyze_scraped_data
import time

async def main():
    """Main function to run collection and analysis"""
    print("=" * 60)
    print("ASYNC DATA COLLECTION AND ANALYSIS")
    print("=" * 60)
    
    # Step 1: Collect data
    print("\n[1/2] Starting async data collection...")
    print("Target: 1000+ posts from LinkedIn and Glassdoor")
    print("Keywords: Marc Benioff, Agentforce, Sierra.AI, Bret Taylor, Salesforce\n")
    
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
        print("\nSample posts collected:")
        for i, post in enumerate(posts[:5]):
            print(f"\n{i+1}. {post['platform'].upper()} - {post.get('post_type', 'unknown')}")
            print(f"   Title: {post.get('title', 'N/A')[:80]}...")
            print(f"   Keywords: {', '.join(post.get('keywords_found', []))}")
            print(f"   URL: {post.get('url', 'N/A')}")
    
    # Step 2: Analyze data
    print("\n" + "=" * 60)
    print("[2/2] Starting AI analysis...")
    print("=" * 60)
    
    if len(posts) > 0:
        report = analyze_scraped_data('linkedin_glassdoor_data.json')
        
        # Show detailed insights
        print("\n" + "=" * 60)
        print("DETAILED ANALYSIS RESULTS")
        print("=" * 60)
        
        # Personality analysis
        if 'personality_analysis' in report:
            print("\n### PERSONALITY TYPES IDENTIFIED ###")
            for personality, data in report['personality_analysis'].items():
                print(f"\n{personality.upper()}:")
                print(f"  - Count: {data['count']} posts")
                print(f"  - Average sentiment: {data['average_sentiment']}")
                print(f"  - Platforms: {dict(data['platforms'])}")
        
        # Sentiment trends
        if 'sentiment_trends' in report:
            print("\n### SENTIMENT ANALYSIS ###")
            
            # By platform
            platform_sentiments = report['sentiment_trends'].get('by_platform', {})
            if platform_sentiments:
                print("\nSentiment by Platform:")
                for platform, data in platform_sentiments.items():
                    print(f"  {platform}: {data['average']} (positive ratio: {data['positive_ratio']})")
            
            # By keyword
            keyword_sentiments = report['sentiment_trends'].get('by_keyword', {})
            if keyword_sentiments:
                print("\nSentiment by Keyword (top 5):")
                sorted_keywords = sorted(keyword_sentiments.items(), 
                                       key=lambda x: x[1]['count'], 
                                       reverse=True)[:5]
                for keyword, data in sorted_keywords:
                    print(f"  {keyword}: {data['average']} ({data['count']} mentions)")
        
        # Agentforce perception
        if 'agentforce_perception' in report:
            print("\n### AGENTFORCE PERCEPTION ###")
            for perception, data in report['agentforce_perception'].items():
                print(f"\n{perception.upper()}:")
                print(f"  - Count: {data['count']} mentions")
                print(f"  - Sentiment: {data['average_sentiment']}")
        
        # Competitive landscape
        if 'competitive_landscape' in report:
            print("\n### COMPETITIVE MENTIONS ###")
            for competitor, data in report['competitive_landscape'].items():
                print(f"\n{competitor}:")
                print(f"  - Total mentions: {data['total_mentions']}")
                print(f"  - Sentiment: {data['average_sentiment']}")
                if data.get('associations'):
                    print(f"  - Associations: {data['associations']}")
        
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE!")
        print("=" * 60)
        print("\nFiles created:")
        print("  - linkedin_glassdoor_data.json (raw data)")
        print("  - linkedin_glassdoor_data.csv (spreadsheet format)")
        print("  - analysis_report.json (detailed analysis)")
        print("  - analysis_summary.csv (summary for spreadsheet)")
        
    else:
        print("\nNo data collected. Please check your internet connection and try again.")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())