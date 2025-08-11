#!/usr/bin/env python3
"""
Create a formatted summary of the analysis results
"""

import json
import pandas as pd

def create_summary():
    """Create a formatted summary of the analysis"""
    
    # Load the analysis report
    with open('analysis_report.json', 'r') as f:
        report = json.load(f)
    
    print("=" * 80)
    print("LINKEDIN & GLASSDOOR ANALYSIS SUMMARY")
    print("=" * 80)
    
    # Overall statistics
    print("\n📊 OVERALL STATISTICS")
    print("-" * 40)
    print(f"Total posts analyzed: {report['summary']['total_posts']:,}")
    print(f"Date range: {report['summary']['date_range']['earliest']} to {report['summary']['date_range']['latest']}")
    print(f"\nPlatform breakdown:")
    for platform, count in report['summary']['platforms'].items():
        percentage = (count / report['summary']['total_posts']) * 100
        print(f"  • {platform.capitalize()}: {count:,} ({percentage:.1f}%)")
    
    print(f"\nPost types:")
    for post_type, count in report['summary']['post_types'].items():
        print(f"  • {post_type.capitalize()}: {count:,}")
    
    # Key insights
    print("\n💡 KEY INSIGHTS")
    print("-" * 40)
    for i, insight in enumerate(report['key_insights'], 1):
        print(f"{i}. {insight}")
    
    # Personality analysis
    print("\n👥 PERSONALITY TYPES IDENTIFIED")
    print("-" * 40)
    personalities = report['personality_analysis']
    sorted_personalities = sorted(personalities.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for personality, data in sorted_personalities:
        print(f"\n{personality.replace('_', ' ').title()}:")
        print(f"  • Count: {data['count']} posts")
        print(f"  • Average sentiment: {data['average_sentiment']}")
        print(f"  • Platform distribution: LinkedIn ({data['platforms'].get('linkedin', 0)}), Glassdoor ({data['platforms'].get('glassdoor', 0)})")
    
    # Sentiment analysis
    print("\n😊 SENTIMENT ANALYSIS")
    print("-" * 40)
    
    # By platform
    platform_sentiments = report['sentiment_trends']['by_platform']
    print("\nSentiment by Platform:")
    for platform, data in platform_sentiments.items():
        sentiment_label = "Positive" if data['average'] > 0 else "Negative" if data['average'] < 0 else "Neutral"
        print(f"  • {platform.capitalize()}: {data['average']} ({sentiment_label})")
        print(f"    - {data['positive_ratio']*100:.1f}% positive posts")
        print(f"    - {data['count']} total posts")
    
    # Top keywords by sentiment
    print("\nTop Keywords by Sentiment:")
    keyword_sentiments = report['sentiment_trends']['by_keyword']
    sorted_keywords = sorted(keyword_sentiments.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    
    for keyword, data in sorted_keywords:
        sentiment_label = "Positive" if data['average'] > 0 else "Negative" if data['average'] < 0 else "Neutral"
        print(f"  • {keyword}: {data['average']} ({sentiment_label}) - {data['count']} mentions")
    
    # Agentforce perception
    print("\n🤖 AGENTFORCE PERCEPTION")
    print("-" * 40)
    agentforce_data = report['agentforce_perception']
    
    for perception, data in sorted(agentforce_data.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"\n{perception.capitalize()}:")
        print(f"  • {data['count']} mentions")
        print(f"  • Average sentiment: {data['average_sentiment']}")
        if data.get('examples'):
            print(f"  • Example: \"{data['examples'][0]['snippet'][:100]}...\"")
    
    # Competitive landscape
    print("\n🏢 COMPETITIVE LANDSCAPE")
    print("-" * 40)
    competitors = report['competitive_landscape']
    
    for competitor, data in competitors.items():
        print(f"\n{competitor}:")
        print(f"  • Total mentions: {data['total_mentions']}")
        print(f"  • Average sentiment: {data['average_sentiment']}")
        print(f"  • Platform breakdown: {dict(data['platforms'])}")
        if data.get('associations'):
            print(f"  • Key associations: {data['associations']}")
    
    # Top keywords
    print("\n🔤 TOP KEYWORDS")
    print("-" * 40)
    for i, kw in enumerate(report['top_keywords'][:10], 1):
        print(f"{i:2d}. {kw['keyword']}: {kw['count']} mentions")
    
    # Save a simplified Excel report
    print("\n📄 CREATING EXCEL REPORT...")
    create_excel_report(report)
    print("Excel report saved as 'analysis_summary.xlsx'")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)

def create_excel_report(report):
    """Create an Excel report with multiple sheets"""
    with pd.ExcelWriter('analysis_summary.xlsx', engine='openpyxl') as writer:
        
        # Summary sheet
        summary_data = {
            'Metric': ['Total Posts', 'LinkedIn Posts', 'Glassdoor Posts', 'Date Range'],
            'Value': [
                report['summary']['total_posts'],
                report['summary']['platforms'].get('linkedin', 0),
                report['summary']['platforms'].get('glassdoor', 0),
                f"{report['summary']['date_range']['earliest']} to {report['summary']['date_range']['latest']}"
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Personality analysis sheet
        personality_data = []
        for personality, data in report['personality_analysis'].items():
            personality_data.append({
                'Personality Type': personality.replace('_', ' ').title(),
                'Count': data['count'],
                'Average Sentiment': data['average_sentiment'],
                'LinkedIn Posts': data['platforms'].get('linkedin', 0),
                'Glassdoor Posts': data['platforms'].get('glassdoor', 0)
            })
        pd.DataFrame(personality_data).to_excel(writer, sheet_name='Personalities', index=False)
        
        # Sentiment by keyword sheet
        keyword_data = []
        for keyword, data in report['sentiment_trends']['by_keyword'].items():
            keyword_data.append({
                'Keyword': keyword,
                'Average Sentiment': data['average'],
                'Total Mentions': data['count'],
                'Positive Ratio': data['positive_ratio']
            })
        pd.DataFrame(keyword_data).to_excel(writer, sheet_name='Keyword Sentiment', index=False)
        
        # Agentforce perception sheet
        agentforce_data = []
        for perception, data in report['agentforce_perception'].items():
            agentforce_data.append({
                'Perception': perception.capitalize(),
                'Count': data['count'],
                'Average Sentiment': data['average_sentiment']
            })
        pd.DataFrame(agentforce_data).to_excel(writer, sheet_name='Agentforce', index=False)
        
        # Competitive landscape sheet
        competitive_data = []
        for competitor, data in report['competitive_landscape'].items():
            competitive_data.append({
                'Competitor': competitor,
                'Total Mentions': data['total_mentions'],
                'Average Sentiment': data['average_sentiment'],
                'LinkedIn Mentions': data['platforms'].get('linkedin', 0),
                'Glassdoor Mentions': data['platforms'].get('glassdoor', 0)
            })
        pd.DataFrame(competitive_data).to_excel(writer, sheet_name='Competitors', index=False)

if __name__ == "__main__":
    create_summary()