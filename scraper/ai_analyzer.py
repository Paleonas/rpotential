"""
AI Analyzer for LinkedIn and Glassdoor data
Analyzes posts to extract insights about personalities, sentiments, and trends
"""

import json
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import re
from collections import Counter, defaultdict

class AIAnalyzer:
    """Analyze scraped data for insights"""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.posts = []
        self.load_data()
        
    def load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                self.posts = json.load(f)
            print(f"Loaded {len(self.posts)} posts for analysis")
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def analyze_personality_types(self) -> Dict:
        """Analyze personality types based on content and platform behavior"""
        personality_profiles = {
            'executive_visionary': {
                'keywords': ['vision', 'transform', 'future', 'revolutionize', 'breakthrough', 'innovation'],
                'platforms': ['linkedin'],
                'post_types': ['article', 'post'],
                'sentiment': [],
                'examples': []
            },
            'tech_enthusiast': {
                'keywords': ['AI', 'technology', 'cutting-edge', 'implementation', 'technical', 'engineering'],
                'platforms': ['linkedin', 'glassdoor'],
                'post_types': ['post', 'review'],
                'sentiment': [],
                'examples': []
            },
            'skeptical_employee': {
                'keywords': ['concerns', 'however', 'but', 'challenging', 'difficult', 'issues'],
                'platforms': ['glassdoor'],
                'post_types': ['review'],
                'sentiment': [],
                'examples': []
            },
            'sales_advocate': {
                'keywords': ['customer', 'revenue', 'growth', 'opportunity', 'market', 'competitive'],
                'platforms': ['linkedin'],
                'post_types': ['post'],
                'sentiment': [],
                'examples': []
            },
            'culture_focused': {
                'keywords': ['culture', 'team', 'work-life', 'environment', 'people', 'values'],
                'platforms': ['glassdoor', 'linkedin'],
                'post_types': ['review', 'post'],
                'sentiment': [],
                'examples': []
            }
        }
        
        # Analyze each post
        for post in self.posts:
            content = post.get('content', '').lower()
            title = post.get('title', '').lower()
            full_text = f"{title} {content}"
            
            # Score each personality type
            for personality, profile in personality_profiles.items():
                score = 0
                
                # Check keywords
                keyword_matches = sum(1 for kw in profile['keywords'] if kw in full_text)
                score += keyword_matches * 2
                
                # Platform match
                if post.get('platform') in profile['platforms']:
                    score += 1
                    
                # Post type match
                if post.get('post_type') in profile['post_types']:
                    score += 1
                
                # If score is high enough, classify
                if score >= 3:
                    sentiment_score = self._calculate_sentiment(full_text)
                    profile['sentiment'].append(sentiment_score)
                    profile['examples'].append({
                        'content': post.get('content', '')[:200] + '...',
                        'author': post.get('author', 'Unknown'),
                        'platform': post.get('platform'),
                        'keywords_found': post.get('keywords_found', []),
                        'sentiment': sentiment_score
                    })
        
        # Calculate statistics
        results = {}
        for personality, profile in personality_profiles.items():
            if profile['examples']:
                avg_sentiment = sum(profile['sentiment']) / len(profile['sentiment'])
                results[personality] = {
                    'count': len(profile['examples']),
                    'average_sentiment': round(avg_sentiment, 2),
                    'top_examples': profile['examples'][:3],
                    'platforms': Counter([ex['platform'] for ex in profile['examples']])
                }
        
        return results
    
    def analyze_sentiment_trends(self) -> Dict:
        """Analyze sentiment trends over time and by topic"""
        sentiment_by_keyword = defaultdict(list)
        sentiment_by_platform = defaultdict(list)
        sentiment_timeline = defaultdict(list)
        
        for post in self.posts:
            content = post.get('content', '').lower()
            sentiment = self._calculate_sentiment(content)
            
            # By keyword
            for keyword in post.get('keywords_found', []):
                sentiment_by_keyword[keyword].append(sentiment)
            
            # By platform
            platform = post.get('platform', 'unknown')
            sentiment_by_platform[platform].append(sentiment)
            
            # By time (if timestamp available)
            if post.get('timestamp'):
                try:
                    date = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    month_key = date.strftime('%Y-%m')
                    sentiment_timeline[month_key].append(sentiment)
                except:
                    pass
        
        # Calculate averages
        results = {
            'by_keyword': {},
            'by_platform': {},
            'timeline': {}
        }
        
        for keyword, sentiments in sentiment_by_keyword.items():
            if sentiments:
                results['by_keyword'][keyword] = {
                    'average': round(sum(sentiments) / len(sentiments), 2),
                    'count': len(sentiments),
                    'positive_ratio': round(len([s for s in sentiments if s > 0]) / len(sentiments), 2)
                }
        
        for platform, sentiments in sentiment_by_platform.items():
            if sentiments:
                results['by_platform'][platform] = {
                    'average': round(sum(sentiments) / len(sentiments), 2),
                    'count': len(sentiments),
                    'positive_ratio': round(len([s for s in sentiments if s > 0]) / len(sentiments), 2)
                }
        
        for month, sentiments in sentiment_timeline.items():
            if sentiments:
                results['timeline'][month] = {
                    'average': round(sum(sentiments) / len(sentiments), 2),
                    'count': len(sentiments)
                }
        
        return results
    
    def analyze_agentforce_perception(self) -> Dict:
        """Specific analysis of Agentforce perception"""
        agentforce_posts = [p for p in self.posts if 'agentforce' in str(p).lower()]
        
        perceptions = {
            'revolutionary': {
                'keywords': ['revolutionary', 'game-changer', 'transform', 'future', 'breakthrough'],
                'posts': []
            },
            'practical': {
                'keywords': ['useful', 'helpful', 'efficient', 'productivity', 'saves time'],
                'posts': []
            },
            'skeptical': {
                'keywords': ['hype', 'concerns', 'not sure', 'overpromise', 'wait and see'],
                'posts': []
            },
            'technical': {
                'keywords': ['API', 'integration', 'implementation', 'architecture', 'scalability'],
                'posts': []
            }
        }
        
        for post in agentforce_posts:
            content = post.get('content', '').lower()
            
            for perception, data in perceptions.items():
                if any(kw in content for kw in data['keywords']):
                    data['posts'].append({
                        'author': post.get('author', 'Unknown'),
                        'platform': post.get('platform'),
                        'snippet': post.get('content', '')[:150] + '...',
                        'sentiment': self._calculate_sentiment(content)
                    })
        
        # Calculate statistics
        results = {}
        for perception, data in perceptions.items():
            if data['posts']:
                sentiments = [p['sentiment'] for p in data['posts']]
                results[perception] = {
                    'count': len(data['posts']),
                    'average_sentiment': round(sum(sentiments) / len(sentiments), 2),
                    'examples': data['posts'][:2]
                }
        
        return results
    
    def analyze_competitive_landscape(self) -> Dict:
        """Analyze mentions of competitors and comparisons"""
        competitors = {
            'Sierra.AI': {'mentions': [], 'with_bret_taylor': 0},
            'Microsoft': {'mentions': [], 'with_copilot': 0},
            'Google': {'mentions': [], 'with_ai': 0},
            'OpenAI': {'mentions': [], 'with_chatgpt': 0}
        }
        
        for post in self.posts:
            content = post.get('content', '').lower()
            
            for competitor, data in competitors.items():
                if competitor.lower() in content:
                    data['mentions'].append({
                        'platform': post.get('platform'),
                        'sentiment': self._calculate_sentiment(content),
                        'context': self._extract_context(content, competitor.lower(), 50)
                    })
                    
                    # Check for specific associations
                    if competitor == 'Sierra.AI' and 'bret taylor' in content:
                        data['with_bret_taylor'] += 1
                    elif competitor == 'Microsoft' and 'copilot' in content:
                        data['with_copilot'] += 1
                    elif competitor == 'Google' and 'ai' in content:
                        data['with_ai'] += 1
                    elif competitor == 'OpenAI' and 'chatgpt' in content:
                        data['with_chatgpt'] += 1
        
        # Calculate results
        results = {}
        for competitor, data in competitors.items():
            if data['mentions']:
                sentiments = [m['sentiment'] for m in data['mentions']]
                results[competitor] = {
                    'total_mentions': len(data['mentions']),
                    'average_sentiment': round(sum(sentiments) / len(sentiments), 2),
                    'platforms': Counter([m['platform'] for m in data['mentions']]),
                    'associations': {k: v for k, v in data.items() if k.startswith('with_') and v > 0}
                }
        
        return results
    
    def _calculate_sentiment(self, text: str) -> float:
        """Simple sentiment calculation (-1 to 1)"""
        positive_words = ['excellent', 'great', 'amazing', 'love', 'innovative', 'revolutionary', 
                         'impressive', 'fantastic', 'wonderful', 'best', 'excited', 'happy']
        negative_words = ['bad', 'poor', 'terrible', 'hate', 'disappointed', 'frustrating',
                         'awful', 'worst', 'difficult', 'problem', 'issue', 'concern']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return round((positive_count - negative_count) / total, 2)
    
    def _extract_context(self, text: str, keyword: str, context_length: int = 50) -> str:
        """Extract context around a keyword"""
        index = text.lower().find(keyword.lower())
        if index == -1:
            return ""
        
        start = max(0, index - context_length)
        end = min(len(text), index + len(keyword) + context_length)
        
        return "..." + text[start:end] + "..."
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        print("\nAnalyzing data...")
        
        report = {
            'summary': {
                'total_posts': len(self.posts),
                'platforms': Counter([p.get('platform') for p in self.posts]),
                'post_types': Counter([p.get('post_type') for p in self.posts]),
                'date_range': self._get_date_range()
            },
            'personality_analysis': self.analyze_personality_types(),
            'sentiment_trends': self.analyze_sentiment_trends(),
            'agentforce_perception': self.analyze_agentforce_perception(),
            'competitive_landscape': self.analyze_competitive_landscape(),
            'top_keywords': self._get_top_keywords(),
            'key_insights': self._generate_insights()
        }
        
        return report
    
    def _get_date_range(self) -> Dict:
        """Get date range of posts"""
        dates = []
        for post in self.posts:
            if post.get('timestamp'):
                try:
                    date = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    dates.append(date)
                except:
                    pass
        
        if dates:
            return {
                'earliest': min(dates).strftime('%Y-%m-%d'),
                'latest': max(dates).strftime('%Y-%m-%d')
            }
        return {'earliest': 'Unknown', 'latest': 'Unknown'}
    
    def _get_top_keywords(self) -> List[Dict]:
        """Get most mentioned keywords"""
        keyword_counts = Counter()
        
        for post in self.posts:
            for keyword in post.get('keywords_found', []):
                keyword_counts[keyword] += 1
        
        return [{'keyword': k, 'count': v} for k, v in keyword_counts.most_common(10)]
    
    def _generate_insights(self) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        # Platform comparison
        platform_sentiments = self.analyze_sentiment_trends()['by_platform']
        if 'linkedin' in platform_sentiments and 'glassdoor' in platform_sentiments:
            linkedin_sent = platform_sentiments['linkedin']['average']
            glassdoor_sent = platform_sentiments['glassdoor']['average']
            
            if linkedin_sent > glassdoor_sent:
                insights.append(f"LinkedIn posts are {abs(linkedin_sent - glassdoor_sent):.1%} more positive than Glassdoor reviews")
            else:
                insights.append(f"Glassdoor reviews are {abs(glassdoor_sent - linkedin_sent):.1%} more critical than LinkedIn posts")
        
        # Agentforce perception
        agentforce_data = self.analyze_agentforce_perception()
        if agentforce_data:
            dominant_perception = max(agentforce_data.items(), key=lambda x: x[1].get('count', 0))
            insights.append(f"Agentforce is predominantly perceived as '{dominant_perception[0]}' with {dominant_perception[1]['count']} mentions")
        
        # Personality types
        personalities = self.analyze_personality_types()
        if personalities:
            top_personality = max(personalities.items(), key=lambda x: x[1]['count'])
            insights.append(f"The most common personality type discussing these topics is '{top_personality[0]}' ({top_personality[1]['count']} posts)")
        
        return insights
    
    def save_report(self, filename: str = 'analysis_report.json'):
        """Save analysis report to file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nAnalysis report saved to {filename}")
        
        # Print summary
        print("\n=== ANALYSIS SUMMARY ===")
        print(f"Total posts analyzed: {report['summary']['total_posts']}")
        print(f"Platforms: {dict(report['summary']['platforms'])}")
        print(f"\nKey Insights:")
        for insight in report['key_insights']:
            print(f"- {insight}")
        
        return report

def analyze_scraped_data(data_file: str = 'linkedin_glassdoor_data.json'):
    """Main function to analyze scraped data"""
    analyzer = AIAnalyzer(data_file)
    report = analyzer.save_report()
    
    # Also save a simplified CSV for spreadsheet viewing
    if analyzer.posts:
        df = pd.DataFrame(analyzer.posts)
        df.to_csv('analysis_summary.csv', index=False)
        print(f"\nSimplified data saved to analysis_summary.csv")
    
    return report

if __name__ == "__main__":
    analyze_scraped_data()