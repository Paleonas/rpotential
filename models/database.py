from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class ScrapedPost(Base):
    """Model for storing scraped posts from LinkedIn and Glassdoor"""
    __tablename__ = 'scraped_posts'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # 'linkedin' or 'glassdoor'
    post_type = Column(String(50))  # 'post', 'ad', 'review', etc.
    url = Column(String(500), unique=True)
    author = Column(String(200))
    author_title = Column(String(200))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # Sentiment and relevance scores (can be added later)
    sentiment_score = Column(Float)
    relevance_score = Column(Float)
    
    # Keywords found
    keywords_found = Column(Text)  # JSON string of keywords
    
    # Engagement metrics (if available)
    likes = Column(Integer)
    comments = Column(Integer)
    shares = Column(Integer)
    
    # Additional metadata
    company = Column(String(200))
    location = Column(String(200))
    is_verified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<ScrapedPost(platform='{self.platform}', author='{self.author}', timestamp='{self.timestamp}')>"

class Keyword(Base):
    """Model for tracking keywords and their mentions"""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # 'person', 'product', 'company'
    total_mentions = Column(Integer, default=0)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Keyword(keyword='{self.keyword}', mentions={self.total_mentions})>"

class ScrapeSession(Base):
    """Model for tracking scraping sessions"""
    __tablename__ = 'scrape_sessions'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    status = Column(String(50))  # 'running', 'completed', 'failed'
    posts_scraped = Column(Integer, default=0)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<ScrapeSession(platform='{self.platform}', status='{self.status}', posts={self.posts_scraped})>"

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/monitoring.db')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()