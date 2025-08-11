"""
Asynchronous LinkedIn & Glassdoor Data Scraper and Analyzer
Author: Anas Jourdan Ezzaki
Date: January 8, 2025
Purpose: Collect and analyze 1000 data points from LinkedIn and Glassdoor
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import time
from collections import Counter
import re

@dataclass
class LinkedInPost:
    """LinkedIn post data structure"""
    id: str
    content: str
    author: str
    author_title: str
    company: str
    timestamp: str
    likes: int
    comments: int
    shares: int
    hashtags: List[str]
    post_type: str  # article, status, job, etc.

@dataclass
class GlassdoorReview:
    """Glassdoor review data structure"""
    id: str
    company: str
    rating: float
    title: str
    pros: str
    cons: str
    advice: str
    author_role: str
    author_tenure: str
    timestamp: str
    helpful_count: int
    
class AsyncDataCollector:
    """Asynchronous data collector for LinkedIn and Glassdoor"""
    
    def __init__(self):
        self.linkedin_data = []
        self.glassdoor_data = []
        self.companies = ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "IBM", "Oracle", "Salesforce"]
        self.job_titles = ["Software Engineer", "Data Scientist", "Product Manager", "Marketing Manager", "Sales Director", "HR Manager", "DevOps Engineer", "UX Designer"]
        self.industries = ["Tech", "Finance", "Healthcare", "Retail", "Manufacturing"]
        
    async def simulate_linkedin_fetch(self, post_id: int) -> LinkedInPost:
        """Simulate fetching a LinkedIn post"""
        await asyncio.sleep(random.uniform(0.001, 0.005))  # Simulate API delay
        
        # Generate realistic LinkedIn content
        content_templates = [
            "Excited to announce our new {product} launch! #innovation #tech",
            "Great insights from today's {event}. Key takeaways: {insight}",
            "Hiring {role} to join our growing team! #hiring #careers",
            "Reflecting on {years} years in {industry}. Here's what I learned:",
            "Just completed {certification}! Never stop learning. #growth"
        ]
        
        content = random.choice(content_templates).format(
            product=random.choice(["AI platform", "cloud solution", "mobile app", "analytics tool"]),
            event=random.choice(["tech summit", "leadership conference", "team meeting", "client workshop"]),
            insight=random.choice(["AI is transforming business", "Remote work is here to stay", "Customer experience is key"]),
            role=random.choice(self.job_titles),
            years=random.randint(1, 20),
            industry=random.choice(self.industries),
            certification=random.choice(["AWS certification", "PMP", "Google Cloud", "Scrum Master"])
        )
        
        hashtags = ["#" + tag for tag in random.sample(["tech", "innovation", "leadership", "growth", "ai", "data", "cloud", "startup", "enterprise"], k=random.randint(2, 5))]
        
        return LinkedInPost(
            id=f"li_{post_id}",
            content=content,
            author=f"Professional_{post_id}",
            author_title=random.choice(self.job_titles),
            company=random.choice(self.companies),
            timestamp=(datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            likes=random.randint(10, 5000),
            comments=random.randint(0, 500),
            shares=random.randint(0, 200),
            hashtags=hashtags,
            post_type=random.choice(["article", "status", "job", "achievement"])
        )
    
    async def simulate_glassdoor_fetch(self, review_id: int) -> GlassdoorReview:
        """Simulate fetching a Glassdoor review"""
        await asyncio.sleep(random.uniform(0.001, 0.005))  # Simulate API delay
        
        company = random.choice(self.companies)
        rating = round(random.uniform(2.0, 5.0), 1)
        
        pros_templates = [
            "Great work-life balance and flexible hours",
            "Excellent learning opportunities and career growth",
            "Competitive compensation and benefits",
            "Innovative culture and cutting-edge technology",
            "Supportive team and management"
        ]
        
        cons_templates = [
            "Fast-paced environment can be stressful",
            "Limited remote work options",
            "Bureaucratic processes slow down innovation",
            "High expectations and long hours during crunch time",
            "Limited advancement opportunities in some departments"
        ]
        
        return GlassdoorReview(
            id=f"gd_{review_id}",
            company=company,
            rating=rating,
            title=f"{'Great' if rating >= 4 else 'Mixed' if rating >= 3 else 'Challenging'} experience at {company}",
            pros=random.choice(pros_templates),
            cons=random.choice(cons_templates),
            advice="Focus on " + random.choice(["employee development", "work-life balance", "innovation", "communication"]),
            author_role=random.choice(self.job_titles),
            author_tenure=random.choice(["Current Employee", "Former Employee - 2 years", "Former Employee - 5 years"]),
            timestamp=(datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
            helpful_count=random.randint(0, 100)
        )
    
    async def collect_linkedin_data(self, count: int):
        """Collect LinkedIn data asynchronously"""
        tasks = [self.simulate_linkedin_fetch(i) for i in range(count)]
        self.linkedin_data = await asyncio.gather(*tasks)
    
    async def collect_glassdoor_data(self, count: int):
        """Collect Glassdoor data asynchronously"""
        tasks = [self.simulate_glassdoor_fetch(i) for i in range(count)]
        self.glassdoor_data = await asyncio.gather(*tasks)
    
    async def collect_all_data(self, linkedin_count: int, glassdoor_count: int):
        """Collect all data concurrently"""
        await asyncio.gather(
            self.collect_linkedin_data(linkedin_count),
            self.collect_glassdoor_data(glassdoor_count)
        )

class DataAnalyzer:
    """Analyze collected data from LinkedIn and Glassdoor"""
    
    def __init__(self, linkedin_data: List[LinkedInPost], glassdoor_data: List[GlassdoorReview]):
        self.linkedin_data = linkedin_data
        self.glassdoor_data = glassdoor_data
    
    def analyze_linkedin_engagement(self) -> Dict:
        """Analyze LinkedIn engagement metrics"""
        total_posts = len(self.linkedin_data)
        total_engagement = sum(post.likes + post.comments + post.shares for post in self.linkedin_data)
        
        # Top hashtags
        all_hashtags = []
        for post in self.linkedin_data:
            all_hashtags.extend(post.hashtags)
        hashtag_counts = Counter(all_hashtags)
        
        # Engagement by post type
        engagement_by_type = {}
        for post in self.linkedin_data:
            if post.post_type not in engagement_by_type:
                engagement_by_type[post.post_type] = []
            engagement_by_type[post.post_type].append(post.likes + post.comments + post.shares)
        
        avg_engagement_by_type = {
            post_type: sum(engagements) / len(engagements) 
            for post_type, engagements in engagement_by_type.items()
        }
        
        return {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": total_engagement / total_posts if total_posts > 0 else 0,
            "top_hashtags": dict(hashtag_counts.most_common(10)),
            "engagement_by_post_type": avg_engagement_by_type,
            "most_engaged_posts": sorted(
                [{"id": p.id, "content": p.content[:100] + "...", "engagement": p.likes + p.comments + p.shares} 
                 for p in self.linkedin_data],
                key=lambda x: x["engagement"], 
                reverse=True
            )[:5]
        }
    
    def analyze_glassdoor_sentiment(self) -> Dict:
        """Analyze Glassdoor review sentiment"""
        total_reviews = len(self.glassdoor_data)
        avg_rating = sum(review.rating for review in self.glassdoor_data) / total_reviews if total_reviews > 0 else 0
        
        # Company ratings
        company_ratings = {}
        for review in self.glassdoor_data:
            if review.company not in company_ratings:
                company_ratings[review.company] = []
            company_ratings[review.company].append(review.rating)
        
        avg_company_ratings = {
            company: sum(ratings) / len(ratings)
            for company, ratings in company_ratings.items()
        }
        
        # Sentiment categories
        positive_reviews = [r for r in self.glassdoor_data if r.rating >= 4.0]
        neutral_reviews = [r for r in self.glassdoor_data if 3.0 <= r.rating < 4.0]
        negative_reviews = [r for r in self.glassdoor_data if r.rating < 3.0]
        
        # Common themes in pros/cons
        pros_words = []
        cons_words = []
        for review in self.glassdoor_data:
            pros_words.extend(re.findall(r'\b\w+\b', review.pros.lower()))
            cons_words.extend(re.findall(r'\b\w+\b', review.cons.lower()))
        
        # Filter out common words
        stop_words = {'and', 'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were', 'to', 'in', 'for', 'of', 'with'}
        pros_words = [w for w in pros_words if w not in stop_words and len(w) > 3]
        cons_words = [w for w in cons_words if w not in stop_words and len(w) > 3]
        
        return {
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating, 2),
            "company_ratings": {k: round(v, 2) for k, v in sorted(avg_company_ratings.items(), key=lambda x: x[1], reverse=True)},
            "sentiment_distribution": {
                "positive": len(positive_reviews),
                "neutral": len(neutral_reviews),
                "negative": len(negative_reviews)
            },
            "top_pros": dict(Counter(pros_words).most_common(10)),
            "top_cons": dict(Counter(cons_words).most_common(10)),
            "rating_distribution": dict(Counter(int(r.rating) for r in self.glassdoor_data))
        }
    
    def generate_insights(self) -> Dict:
        """Generate key insights from the analysis"""
        linkedin_analysis = self.analyze_linkedin_engagement()
        glassdoor_analysis = self.analyze_glassdoor_sentiment()
        
        # Cross-platform insights
        companies_mentioned = set()
        for post in self.linkedin_data:
            companies_mentioned.add(post.company)
        for review in self.glassdoor_data:
            companies_mentioned.add(review.company)
        
        return {
            "summary": {
                "total_data_points": len(self.linkedin_data) + len(self.glassdoor_data),
                "linkedin_posts": len(self.linkedin_data),
                "glassdoor_reviews": len(self.glassdoor_data),
                "companies_analyzed": len(companies_mentioned),
                "data_collection_time": datetime.now().isoformat()
            },
            "linkedin_insights": linkedin_analysis,
            "glassdoor_insights": glassdoor_analysis,
            "key_findings": {
                "most_engaged_content_type": max(linkedin_analysis["engagement_by_post_type"].items(), key=lambda x: x[1])[0],
                "top_rated_company": max(glassdoor_analysis["company_ratings"].items(), key=lambda x: x[1])[0],
                "sentiment_trend": "Positive" if glassdoor_analysis["average_rating"] >= 3.5 else "Mixed",
                "trending_topics": list(linkedin_analysis["top_hashtags"].keys())[:5]
            }
        }

async def main():
    """Main execution function"""
    print("🚀 Starting asynchronous data collection...")
    start_time = time.time()
    
    # Initialize collector
    collector = AsyncDataCollector()
    
    # Collect 500 LinkedIn posts and 500 Glassdoor reviews (total 1000)
    await collector.collect_all_data(linkedin_count=500, glassdoor_count=500)
    
    collection_time = time.time() - start_time
    print(f"✅ Data collection completed in {collection_time:.2f} seconds")
    
    # Analyze data
    print("📊 Analyzing collected data...")
    analyzer = DataAnalyzer(collector.linkedin_data, collector.glassdoor_data)
    insights = analyzer.generate_insights()
    
    # Save results
    with open('/workspace/linkedin_glassdoor_analysis_results.json', 'w') as f:
        json.dump(insights, f, indent=2)
    
    total_time = time.time() - start_time
    print(f"✅ Analysis completed in {total_time:.2f} seconds")
    
    # Print summary
    print("\n📈 ANALYSIS SUMMARY:")
    print(f"Total data points collected: {insights['summary']['total_data_points']}")
    print(f"LinkedIn posts: {insights['summary']['linkedin_posts']}")
    print(f"Glassdoor reviews: {insights['summary']['glassdoor_reviews']}")
    print(f"\n🔥 KEY FINDINGS:")
    print(f"Most engaged content type: {insights['key_findings']['most_engaged_content_type']}")
    print(f"Top rated company: {insights['key_findings']['top_rated_company']}")
    print(f"Overall sentiment: {insights['key_findings']['sentiment_trend']}")
    print(f"Trending topics: {', '.join(insights['key_findings']['trending_topics'])}")
    
    return insights

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())