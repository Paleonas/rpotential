#!/usr/bin/env python3
"""
Flask web application for social media monitoring dashboard
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database models
from models.database import init_db, SessionLocal, ScrapedPost, Keyword, ScrapeSession
from sqlalchemy import desc, func

# Import scrapers for manual runs
from scraper.run_scraper import run_scraper

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
CORS(app)

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    db = SessionLocal()
    try:
        # Get total posts
        total_posts = db.query(ScrapedPost).count()
        
        # Get posts by platform
        platform_stats = db.query(
            ScrapedPost.platform,
            func.count(ScrapedPost.id).label('count')
        ).group_by(ScrapedPost.platform).all()
        
        # Get top keywords
        top_keywords = db.query(Keyword).order_by(
            desc(Keyword.total_mentions)
        ).limit(10).all()
        
        # Get recent scrape sessions
        recent_sessions = db.query(ScrapeSession).order_by(
            desc(ScrapeSession.started_at)
        ).limit(5).all()
        
        # Posts over time (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        posts_over_time = db.query(
            func.date(ScrapedPost.scraped_at).label('date'),
            func.count(ScrapedPost.id).label('count')
        ).filter(
            ScrapedPost.scraped_at >= seven_days_ago
        ).group_by(
            func.date(ScrapedPost.scraped_at)
        ).all()
        
        return jsonify({
            'total_posts': total_posts,
            'platform_stats': [
                {'platform': p, 'count': c} for p, c in platform_stats
            ],
            'top_keywords': [
                {
                    'keyword': k.keyword,
                    'mentions': k.total_mentions,
                    'category': k.category,
                    'last_seen': k.last_seen.isoformat() if k.last_seen else None
                } for k in top_keywords
            ],
            'recent_sessions': [
                {
                    'platform': s.platform,
                    'started_at': s.started_at.isoformat(),
                    'status': s.status,
                    'posts_scraped': s.posts_scraped
                } for s in recent_sessions
            ],
            'posts_over_time': [
                {
                    'date': str(date),
                    'count': count
                } for date, count in posts_over_time
            ]
        })
    finally:
        db.close()

@app.route('/api/posts')
def get_posts():
    """Get posts with pagination and filtering"""
    db = SessionLocal()
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        platform = request.args.get('platform')
        keyword = request.args.get('keyword')
        post_type = request.args.get('post_type')
        
        # Build query
        query = db.query(ScrapedPost)
        
        # Apply filters
        if platform:
            query = query.filter(ScrapedPost.platform == platform)
        if keyword:
            query = query.filter(
                ScrapedPost.keywords_found.contains(keyword)
            )
        if post_type:
            query = query.filter(ScrapedPost.post_type == post_type)
        
        # Order by most recent
        query = query.order_by(desc(ScrapedPost.scraped_at))
        
        # Paginate
        total = query.count()
        posts = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'posts': [
                {
                    'id': p.id,
                    'platform': p.platform,
                    'post_type': p.post_type,
                    'url': p.url,
                    'author': p.author,
                    'author_title': p.author_title,
                    'content': p.content,
                    'timestamp': p.timestamp.isoformat() if p.timestamp else None,
                    'scraped_at': p.scraped_at.isoformat(),
                    'keywords_found': json.loads(p.keywords_found) if p.keywords_found else [],
                    'likes': p.likes,
                    'comments': p.comments,
                    'shares': p.shares,
                    'company': p.company,
                    'location': p.location,
                    'is_verified': p.is_verified
                } for p in posts
            ],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    finally:
        db.close()

@app.route('/api/keywords')
def get_keywords():
    """Get all keywords with stats"""
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).order_by(
            desc(Keyword.total_mentions)
        ).all()
        
        return jsonify({
            'keywords': [
                {
                    'id': k.id,
                    'keyword': k.keyword,
                    'category': k.category,
                    'total_mentions': k.total_mentions,
                    'last_seen': k.last_seen.isoformat() if k.last_seen else None,
                    'created_at': k.created_at.isoformat()
                } for k in keywords
            ]
        })
    finally:
        db.close()

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scrape"""
    data = request.get_json() or {}
    platform = data.get('platform')
    
    try:
        # Run scraper
        results = run_scraper(platform)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export')
def export_data():
    """Export data as JSON"""
    db = SessionLocal()
    try:
        # Get date range
        days = int(request.args.get('days', 7))
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get posts
        posts = db.query(ScrapedPost).filter(
            ScrapedPost.scraped_at >= since
        ).all()
        
        # Format for export
        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'date_range': {
                'from': since.isoformat(),
                'to': datetime.utcnow().isoformat()
            },
            'total_posts': len(posts),
            'posts': [
                {
                    'platform': p.platform,
                    'post_type': p.post_type,
                    'url': p.url,
                    'author': p.author,
                    'content': p.content,
                    'timestamp': p.timestamp.isoformat() if p.timestamp else None,
                    'keywords_found': json.loads(p.keywords_found) if p.keywords_found else [],
                    'company': p.company
                } for p in posts
            ]
        }
        
        return jsonify(export_data)
    finally:
        db.close()

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the Flask app
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Social Media Monitoring Dashboard...")
    print(f"Access the dashboard at: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)