#!/usr/bin/env python3
"""
Generate mock data for demonstration of the analysis capabilities
"""

import json
import random
from datetime import datetime, timedelta
import pandas as pd

def generate_mock_data(count=1000):
    """Generate realistic mock data for LinkedIn and Glassdoor"""
    
    posts = []
    
    # LinkedIn post templates
    linkedin_templates = [
        {
            'title': '{author} on LinkedIn: Excited about Agentforce',
            'content': 'Just witnessed an incredible demo of Salesforce Agentforce. The AI capabilities are truly revolutionary. This will transform how businesses operate. {extra}',
            'keywords': ['Agentforce', 'AI', 'Salesforce'],
            'sentiment': 'positive'
        },
        {
            'title': '{author} shares thoughts on AI transformation',
            'content': 'Marc Benioff\'s vision for Agentforce is compelling. As someone working in CRM, I see the potential for AI agents to revolutionize customer service. {extra}',
            'keywords': ['Marc Benioff', 'Agentforce', 'AI', 'CRM agents'],
            'sentiment': 'positive'
        },
        {
            'title': 'Sierra.AI and the future of enterprise AI | {author}',
            'content': 'Bret Taylor\'s new venture Sierra.AI is pushing boundaries. Having worked with him at Salesforce, I\'m excited to see what comes next. {extra}',
            'keywords': ['Bret Taylor', 'Sierra.AI', 'Salesforce', 'AI'],
            'sentiment': 'positive'
        },
        {
            'title': '{author} discusses AI implementation challenges',
            'content': 'While Agentforce shows promise, implementation challenges remain. Integration with existing systems and data privacy concerns need addressing. {extra}',
            'keywords': ['Agentforce', 'AI'],
            'sentiment': 'neutral'
        },
        {
            'title': 'CRM agents: hype or reality? | {author}',
            'content': 'Everyone\'s talking about CRM agents and AI, but are we overpromising? Need to see more real-world results before jumping on the bandwagon. {extra}',
            'keywords': ['CRM agents', 'AI'],
            'sentiment': 'skeptical'
        }
    ]
    
    # Glassdoor review templates
    glassdoor_templates = [
        {
            'title': 'Great place to work on cutting-edge AI - Salesforce',
            'content': 'Working on the Agentforce team has been incredible. Marc Benioff is very involved and the technology is groundbreaking. Great benefits and culture.',
            'keywords': ['Agentforce', 'Marc Benioff', 'AI', 'Salesforce'],
            'rating': 4.5,
            'sentiment': 'positive'
        },
        {
            'title': 'Exciting but demanding - Salesforce Review',
            'content': 'The Agentforce project is revolutionary but the pace is intense. Long hours but you\'re building the future of AI. Leadership is visionary.',
            'keywords': ['Agentforce', 'AI', 'Salesforce'],
            'rating': 4.0,
            'sentiment': 'positive'
        },
        {
            'title': 'Mixed feelings about direction - Salesforce',
            'content': 'While the AI push with Agentforce is exciting, some concerns about work-life balance and unrealistic deadlines. Technology is impressive though.',
            'keywords': ['Agentforce', 'AI', 'Salesforce'],
            'rating': 3.5,
            'sentiment': 'neutral'
        },
        {
            'title': 'Amazing AI startup culture - Sierra AI',
            'content': 'Bret Taylor has created something special at Sierra.AI. Small team doing big things in AI agents. Great opportunity to shape the future.',
            'keywords': ['Bret Taylor', 'Sierra.AI', 'AI'],
            'rating': 5.0,
            'sentiment': 'positive'
        },
        {
            'title': 'Challenging but rewarding - Salesforce AI division',
            'content': 'Working on CRM agents and AI integration. Complex technical challenges but supportive team. Marc Benioff\'s vision keeps us motivated.',
            'keywords': ['CRM agents', 'AI', 'Marc Benioff', 'Salesforce'],
            'rating': 4.2,
            'sentiment': 'positive'
        }
    ]
    
    # Author names and titles
    linkedin_authors = [
        ('Sarah Chen', 'VP of Product at TechCorp'),
        ('Michael Rodriguez', 'CTO at StartupXYZ'),
        ('Emily Johnson', 'AI Researcher at University'),
        ('David Kim', 'Senior Engineer at BigTech'),
        ('Lisa Anderson', 'Product Manager at Enterprise Inc'),
        ('James Wilson', 'Data Scientist at AI Labs'),
        ('Maria Garcia', 'Director of Innovation'),
        ('Robert Taylor', 'Cloud Architect'),
        ('Jennifer Lee', 'Business Analyst'),
        ('Chris Martin', 'Sales Director')
    ]
    
    glassdoor_titles = [
        'Senior Software Engineer',
        'Product Manager',
        'Data Scientist',
        'ML Engineer',
        'Solutions Architect',
        'Engineering Manager',
        'Technical Lead',
        'AI Researcher',
        'DevOps Engineer',
        'Business Analyst'
    ]
    
    # Extra content snippets
    extra_snippets = [
        'The potential for enterprise transformation is huge.',
        'Looking forward to seeing how this evolves.',
        'Game-changing technology for sure.',
        'Still early days but very promising.',
        'The competition is heating up in this space.',
        'Customers are already seeing value.',
        'Integration capabilities are impressive.',
        'The AI revolution is here.',
        'Exciting times in the CRM industry.',
        'This could redefine how we work.'
    ]
    
    # Generate LinkedIn posts (60% of data)
    linkedin_count = int(count * 0.6)
    for i in range(linkedin_count):
        template = random.choice(linkedin_templates)
        author, title = random.choice(linkedin_authors)
        
        post = {
            'platform': 'linkedin',
            'post_type': random.choice(['post', 'article', 'post']),  # More posts than articles
            'url': f'https://www.linkedin.com/posts/mock-post-{i}',
            'title': template['title'].format(author=author),
            'author': author,
            'author_title': title,
            'content': template['content'].format(extra=random.choice(extra_snippets)),
            'keywords_found': template['keywords'],
            'timestamp': datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            'scraped_at': datetime.utcnow(),
            'likes': random.randint(10, 5000) if template['sentiment'] == 'positive' else random.randint(5, 500),
            'comments': random.randint(0, 200),
            'shares': random.randint(0, 100)
        }
        
        posts.append(post)
    
    # Generate Glassdoor reviews (40% of data)
    glassdoor_count = count - linkedin_count
    companies = ['Salesforce'] * int(glassdoor_count * 0.7) + ['Sierra AI', 'Sierra.AI'] * int(glassdoor_count * 0.15)
    
    for i in range(glassdoor_count):
        template = random.choice(glassdoor_templates)
        job_title = random.choice(glassdoor_titles)
        company = random.choice(companies)
        
        post = {
            'platform': 'glassdoor',
            'post_type': 'review',
            'url': f'https://www.glassdoor.com/Reviews/mock-review-{i}',
            'title': template['title'],
            'author': 'Anonymous Employee',
            'author_title': job_title,
            'content': template['content'],
            'keywords_found': template['keywords'],
            'company': company,
            'rating': template.get('rating', random.uniform(3.0, 5.0)),
            'timestamp': datetime.utcnow() - timedelta(days=random.randint(1, 180)),
            'scraped_at': datetime.utcnow(),
            'location': random.choice(['San Francisco, CA', 'Seattle, WA', 'New York, NY', 'Austin, TX']),
            'is_verified': True
        }
        
        posts.append(post)
    
    # Add some specific patterns for analysis
    
    # Add some posts with multiple personality types
    for i in range(20):
        post = {
            'platform': 'linkedin',
            'post_type': 'post',
            'url': f'https://www.linkedin.com/posts/visionary-{i}',
            'title': 'The future of AI is here with Agentforce',
            'author': 'Tech Visionary',
            'content': 'Revolutionary breakthrough! Agentforce will transform the enterprise. The future is now. Innovation at its finest.',
            'keywords_found': ['Agentforce', 'AI'],
            'timestamp': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            'scraped_at': datetime.utcnow()
        }
        posts.append(post)
    
    # Add some skeptical posts
    for i in range(15):
        post = {
            'platform': 'glassdoor',
            'post_type': 'review',
            'url': f'https://www.glassdoor.com/Reviews/skeptical-{i}',
            'title': 'Concerns about AI hype',
            'author': 'Anonymous Employee',
            'content': 'However, there are concerns about overpromising. Challenging implementation. Difficult integration issues.',
            'keywords_found': ['AI', 'Salesforce'],
            'company': 'Salesforce',
            'rating': 3.0,
            'timestamp': datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            'scraped_at': datetime.utcnow()
        }
        posts.append(post)
    
    # Shuffle to mix platforms and types
    random.shuffle(posts)
    
    return posts[:count]

def main():
    """Generate and save mock data"""
    print("Generating 1000+ mock posts for demonstration...")
    
    # Generate data
    posts = generate_mock_data(1200)  # Generate extra to ensure we have 1000+
    
    # Convert datetime objects to strings for JSON
    for post in posts:
        if isinstance(post.get('timestamp'), datetime):
            post['timestamp'] = post['timestamp'].isoformat()
        if isinstance(post.get('scraped_at'), datetime):
            post['scraped_at'] = post['scraped_at'].isoformat()
    
    # Save to JSON
    with open('linkedin_glassdoor_data.json', 'w') as f:
        json.dump(posts, f, indent=2)
    
    # Save to CSV
    df = pd.DataFrame(posts)
    if 'keywords_found' in df.columns:
        df['keywords_found'] = df['keywords_found'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    df.to_csv('linkedin_glassdoor_data.csv', index=False)
    
    print(f"\nGenerated {len(posts)} mock posts")
    print(f"LinkedIn posts: {len([p for p in posts if p['platform'] == 'linkedin'])}")
    print(f"Glassdoor reviews: {len([p for p in posts if p['platform'] == 'glassdoor'])}")
    print("\nFiles created:")
    print("  - linkedin_glassdoor_data.json")
    print("  - linkedin_glassdoor_data.csv")
    
    # Show sample
    print("\nSample posts:")
    for i, post in enumerate(posts[:3]):
        print(f"\n{i+1}. {post['platform'].upper()} - {post['post_type']}")
        print(f"   Title: {post.get('title', 'N/A')[:80]}...")
        print(f"   Keywords: {', '.join(post['keywords_found'])}")
        print(f"   Content: {post['content'][:100]}...")

if __name__ == "__main__":
    main()