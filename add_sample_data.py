#!/usr/bin/env python3
"""
Add sample data to the database for demonstration
"""

from datetime import datetime, timedelta
import random
import json
from models.database import init_db, SessionLocal, ScrapedPost, Keyword, ScrapeSession

def add_sample_data():
    """Add sample data to the database"""
    # Initialize database
    init_db()
    db = SessionLocal()
    
    # Sample keywords
    keywords_data = [
        ('Marc Benioff', 'people', 45),
        ('Bret Taylor', 'people', 23),
        ('Agentforce', 'products', 67),
        ('Sierra.AI', 'products', 34),
        ('Salesforce', 'companies', 89),
        ('AI', 'general', 112),
        ('CRM agents', 'general', 28)
    ]
    
    # Add keywords
    for keyword, category, mentions in keywords_data:
        kw = db.query(Keyword).filter_by(keyword=keyword).first()
        if not kw:
            kw = Keyword(
                keyword=keyword,
                category=category,
                total_mentions=mentions,
                last_seen=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            )
            db.add(kw)
    
    # Sample posts
    sample_posts = [
        {
            'platform': 'linkedin',
            'post_type': 'post',
            'url': 'https://www.linkedin.com/posts/marc-benioff_agentforce-launch',
            'author': 'Marc Benioff',
            'author_title': 'Chair & CEO at Salesforce',
            'content': 'Excited to announce Agentforce - our revolutionary AI agent platform that will transform how businesses operate. This is the future of CRM and enterprise AI.',
            'keywords_found': ['Marc Benioff', 'Agentforce', 'AI', 'CRM agents'],
            'likes': 2453,
            'comments': 187,
            'shares': 342,
            'company': 'Salesforce',
            'is_verified': True
        },
        {
            'platform': 'linkedin',
            'post_type': 'article',
            'url': 'https://www.linkedin.com/pulse/ai-revolution-bret-taylor',
            'author': 'Bret Taylor',
            'author_title': 'Co-founder & CEO at Sierra',
            'content': 'After my time at Salesforce, I\'m now focused on Sierra.AI - building the next generation of AI agents. The potential for AI to augment human capabilities is immense.',
            'keywords_found': ['Bret Taylor', 'Salesforce', 'Sierra.AI', 'AI'],
            'likes': 1876,
            'comments': 92,
            'shares': 234,
            'company': 'Sierra',
            'is_verified': True
        },
        {
            'platform': 'glassdoor',
            'post_type': 'review',
            'url': 'https://www.glassdoor.com/Reviews/Salesforce-Reviews-E11159.htm',
            'author': 'Anonymous Employee',
            'author_title': 'Senior Software Engineer',
            'content': 'Working on Agentforce has been incredible. Marc Benioff\'s vision for AI agents is revolutionary. The team is top-notch and the technology is cutting-edge.',
            'keywords_found': ['Agentforce', 'Marc Benioff', 'AI'],
            'company': 'Salesforce',
            'location': 'San Francisco, CA',
            'is_verified': True,
            'rating': 4.5
        },
        {
            'platform': 'linkedin',
            'post_type': 'post',
            'url': 'https://www.linkedin.com/posts/salesforce-agentforce-demo',
            'author': 'Sarah Chen',
            'author_title': 'VP of Product at Salesforce',
            'content': 'Just finished demo of Agentforce to Fortune 500 CEO. The response was incredible! AI agents are the future of enterprise software.',
            'keywords_found': ['Agentforce', 'AI', 'Salesforce'],
            'likes': 892,
            'comments': 43,
            'shares': 67,
            'company': 'Salesforce',
            'is_verified': True
        },
        {
            'platform': 'glassdoor',
            'post_type': 'review',
            'url': 'https://www.glassdoor.com/Reviews/Sierra-AI-Reviews.htm',
            'author': 'Anonymous Employee',
            'author_title': 'Machine Learning Engineer',
            'content': 'Bret Taylor is an amazing leader. Sierra.AI is pushing the boundaries of what\'s possible with AI agents. Great culture and cutting-edge work.',
            'keywords_found': ['Bret Taylor', 'Sierra.AI', 'AI'],
            'company': 'Sierra AI',
            'location': 'Palo Alto, CA',
            'is_verified': True,
            'rating': 5.0
        },
        {
            'platform': 'linkedin',
            'post_type': 'post',
            'url': 'https://www.linkedin.com/posts/ai-crm-discussion',
            'author': 'Michael Rodriguez',
            'author_title': 'CTO at TechCorp',
            'content': 'Just evaluated Salesforce Agentforce vs competitors. The AI capabilities are impressive. CRM agents will revolutionize customer service.',
            'keywords_found': ['Salesforce', 'Agentforce', 'AI', 'CRM agents'],
            'likes': 567,
            'comments': 28,
            'shares': 45,
            'is_verified': False
        },
        {
            'platform': 'linkedin',
            'post_type': 'post',
            'url': 'https://www.linkedin.com/posts/sierra-ai-funding',
            'author': 'TechCrunch',
            'author_title': 'Technology News',
            'content': 'BREAKING: Sierra.AI raises $100M Series B led by Sequoia. Bret Taylor\'s AI agent startup is valued at $1B. The future of enterprise AI is here.',
            'keywords_found': ['Sierra.AI', 'Bret Taylor', 'AI'],
            'likes': 3421,
            'comments': 234,
            'shares': 567,
            'is_verified': True
        },
        {
            'platform': 'glassdoor',
            'post_type': 'review',
            'url': 'https://www.glassdoor.com/Reviews/Salesforce-Agentforce-Team.htm',
            'author': 'Anonymous Employee',
            'author_title': 'Product Manager',
            'content': 'The Agentforce team is doing groundbreaking work. Marc Benioff visits our team weekly. The AI technology we\'re building will change everything.',
            'keywords_found': ['Agentforce', 'Marc Benioff', 'AI'],
            'company': 'Salesforce',
            'location': 'Seattle, WA',
            'is_verified': True,
            'rating': 4.8
        }
    ]
    
    # Add posts with random timestamps
    for i, post_data in enumerate(sample_posts):
        # Check if post already exists
        existing = db.query(ScrapedPost).filter_by(url=post_data['url']).first()
        if existing:
            continue
        
        # Random timestamp in the last 7 days
        hours_ago = random.randint(1, 168)
        
        post = ScrapedPost(
            platform=post_data['platform'],
            post_type=post_data['post_type'],
            url=post_data['url'],
            author=post_data['author'],
            author_title=post_data.get('author_title'),
            content=post_data['content'],
            timestamp=datetime.utcnow() - timedelta(hours=hours_ago + 24),
            scraped_at=datetime.utcnow() - timedelta(hours=hours_ago),
            keywords_found=json.dumps(post_data['keywords_found']),
            likes=post_data.get('likes'),
            comments=post_data.get('comments'),
            shares=post_data.get('shares'),
            company=post_data.get('company'),
            location=post_data.get('location'),
            is_verified=post_data.get('is_verified', False)
        )
        
        # Add rating if it's a Glassdoor review
        if 'rating' in post_data:
            post.sentiment_score = post_data['rating']
        
        db.add(post)
    
    # Add scrape sessions
    sessions = [
        {
            'platform': 'linkedin',
            'status': 'completed',
            'posts_scraped': 5,
            'hours_ago': 2
        },
        {
            'platform': 'glassdoor',
            'status': 'completed',
            'posts_scraped': 3,
            'hours_ago': 4
        },
        {
            'platform': 'linkedin',
            'status': 'completed',
            'posts_scraped': 4,
            'hours_ago': 24
        },
        {
            'platform': 'glassdoor',
            'status': 'completed',
            'posts_scraped': 2,
            'hours_ago': 48
        }
    ]
    
    for session_data in sessions:
        session = ScrapeSession(
            platform=session_data['platform'],
            started_at=datetime.utcnow() - timedelta(hours=session_data['hours_ago']),
            ended_at=datetime.utcnow() - timedelta(hours=session_data['hours_ago'] - 0.5),
            status=session_data['status'],
            posts_scraped=session_data['posts_scraped']
        )
        db.add(session)
    
    # Commit all changes
    db.commit()
    db.close()
    
    print("Sample data added successfully!")
    print("- Added/updated 7 keywords")
    print("- Added sample posts from LinkedIn and Glassdoor")
    print("- Added scrape session history")
    print("\nYou can now view the dashboard at http://localhost:5000")

if __name__ == "__main__":
    add_sample_data()