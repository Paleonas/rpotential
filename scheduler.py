#!/usr/bin/env python3
"""
Scheduler for automated scraping
Run this to start the scheduled scraping service
"""

import os
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import scraper runner
from scraper.run_scraper import run_scraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BlockingScheduler()

def scheduled_scrape():
    """Run scheduled scraping job"""
    logger.info("Starting scheduled scrape...")
    
    try:
        # Run scraper for all platforms
        results = run_scraper()
        
        logger.info(f"Scheduled scrape completed. Total posts: {results['total_posts']}")
        
        for platform, data in results['platforms'].items():
            if data['status'] == 'success':
                logger.info(f"{platform}: {data['posts_found']} posts found")
            else:
                logger.error(f"{platform}: Failed - {data.get('error', 'Unknown error')}")
                
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}", exc_info=True)

def main():
    """Main scheduler entry point"""
    # Get scraping interval from environment
    interval_minutes = int(os.getenv('SCRAPE_INTERVAL_MINUTES', 60))
    
    logger.info(f"Starting scheduler with {interval_minutes} minute interval")
    
    # Schedule the scraping job
    scheduler.add_job(
        scheduled_scrape,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='scrape_job',
        name='Social Media Scraping',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )
    
    # Run immediately on startup
    logger.info("Running initial scrape...")
    scheduled_scrape()
    
    # Start the scheduler
    try:
        logger.info("Scheduler started. Press Ctrl+C to exit.")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        scheduler.shutdown()

if __name__ == '__main__':
    main()