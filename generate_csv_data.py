"""
Generate CSV files for LinkedIn and Glassdoor data
Author: Anas Jourdan Ezzaki
Date: January 8, 2025
"""

import csv
import json
import asyncio
from datetime import datetime
import time

# Import our existing scraper
from async_linkedin_glassdoor_scraper import AsyncDataCollector, DataAnalyzer

async def generate_csv_data():
    """Generate CSV files with comprehensive data"""
    print("🚀 Generating CSV data...")
    start_time = time.time()
    
    # Collect data
    collector = AsyncDataCollector()
    await collector.collect_all_data(linkedin_count=500, glassdoor_count=500)
    
    # Generate LinkedIn CSV
    with open('/workspace/linkedin_data_analysis.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'post_id', 'content', 'author', 'author_title', 'company', 
            'timestamp', 'likes', 'comments', 'shares', 'total_engagement',
            'hashtags', 'post_type', 'content_length', 'hour_posted',
            'day_of_week', 'engagement_rate'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for post in collector.linkedin_data:
            timestamp = datetime.fromisoformat(post.timestamp)
            total_engagement = post.likes + post.comments + post.shares
            
            writer.writerow({
                'post_id': post.id,
                'content': post.content,
                'author': post.author,
                'author_title': post.author_title,
                'company': post.company,
                'timestamp': post.timestamp,
                'likes': post.likes,
                'comments': post.comments,
                'shares': post.shares,
                'total_engagement': total_engagement,
                'hashtags': ' '.join(post.hashtags),
                'post_type': post.post_type,
                'content_length': len(post.content),
                'hour_posted': timestamp.hour,
                'day_of_week': timestamp.strftime('%A'),
                'engagement_rate': round((total_engagement / (len(post.content) + 1)) * 100, 2)
            })
    
    # Generate Glassdoor CSV
    with open('/workspace/glassdoor_reviews_analysis.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'review_id', 'company', 'rating', 'title', 'pros', 'cons', 
            'advice', 'author_role', 'author_tenure', 'timestamp',
            'helpful_count', 'sentiment', 'pros_word_count', 'cons_word_count',
            'review_length', 'year_posted', 'is_current_employee'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for review in collector.glassdoor_data:
            timestamp = datetime.fromisoformat(review.timestamp)
            sentiment = 'positive' if review.rating >= 4 else 'neutral' if review.rating >= 3 else 'negative'
            
            writer.writerow({
                'review_id': review.id,
                'company': review.company,
                'rating': review.rating,
                'title': review.title,
                'pros': review.pros,
                'cons': review.cons,
                'advice': review.advice,
                'author_role': review.author_role,
                'author_tenure': review.author_tenure,
                'timestamp': review.timestamp,
                'helpful_count': review.helpful_count,
                'sentiment': sentiment,
                'pros_word_count': len(review.pros.split()),
                'cons_word_count': len(review.cons.split()),
                'review_length': len(review.pros) + len(review.cons) + len(review.advice),
                'year_posted': timestamp.year,
                'is_current_employee': 'Current' in review.author_tenure
            })
    
    # Generate Combined Summary CSV
    analyzer = DataAnalyzer(collector.linkedin_data, collector.glassdoor_data)
    insights = analyzer.generate_insights()
    
    with open('/workspace/combined_platform_summary.csv', 'w', newline='', encoding='utf-8') as csvfile:
        # LinkedIn summary section
        writer = csv.writer(csvfile)
        writer.writerow(['LINKEDIN ANALYSIS SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Posts', insights['linkedin_insights']['total_posts']])
        writer.writerow(['Total Engagement', insights['linkedin_insights']['total_engagement']])
        writer.writerow(['Average Engagement per Post', round(insights['linkedin_insights']['avg_engagement_per_post'], 2)])
        writer.writerow(['Most Engaged Content Type', insights['key_findings']['most_engaged_content_type']])
        writer.writerow([])
        
        writer.writerow(['Top Hashtags', 'Count'])
        for hashtag, count in list(insights['linkedin_insights']['top_hashtags'].items())[:10]:
            writer.writerow([hashtag, count])
        writer.writerow([])
        
        writer.writerow(['Content Type', 'Average Engagement'])
        for post_type, avg_engagement in insights['linkedin_insights']['engagement_by_post_type'].items():
            writer.writerow([post_type, round(avg_engagement, 2)])
        writer.writerow([])
        
        # Glassdoor summary section
        writer.writerow(['GLASSDOOR ANALYSIS SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Reviews', insights['glassdoor_insights']['total_reviews']])
        writer.writerow(['Average Rating', insights['glassdoor_insights']['average_rating']])
        writer.writerow(['Top Rated Company', insights['key_findings']['top_rated_company']])
        writer.writerow([])
        
        writer.writerow(['Company', 'Average Rating'])
        for company, rating in insights['glassdoor_insights']['company_ratings'].items():
            writer.writerow([company, rating])
        writer.writerow([])
        
        writer.writerow(['Sentiment', 'Count'])
        for sentiment, count in insights['glassdoor_insights']['sentiment_distribution'].items():
            writer.writerow([sentiment.capitalize(), count])
    
    elapsed_time = time.time() - start_time
    print(f"✅ CSV files generated in {elapsed_time:.2f} seconds")
    print("\n📁 Files created:")
    print("1. linkedin_data_analysis.csv - 500 LinkedIn posts with 16 columns")
    print("2. glassdoor_reviews_analysis.csv - 500 Glassdoor reviews with 16 columns")
    print("3. combined_platform_summary.csv - Summary statistics and insights")
    
    return insights

if __name__ == "__main__":
    asyncio.run(generate_csv_data())