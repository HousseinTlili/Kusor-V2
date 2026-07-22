# backend/collector/scheduler.py
"""
APScheduler setup for periodic BCT scraping tasks.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler

from backend.collector.bct_scraper import BCTScraper

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_bct_sync():
    """Job to scrape latest BCT circulars."""
    logger.info("Executing scheduled BCT circular scrape...")
    scraper = BCTScraper()
    circulars = scraper.scrape_latest()
    logger.info("Scheduled scrape found %d items", len(circulars))


def init_scheduler(app=None, interval_hours: int = 24):
    """Start background scheduler for BCT website polling."""
    if not scheduler.running:
        scheduler.add_job(
            run_bct_sync,
            "interval",
            hours=interval_hours,
            id="bct_sync_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started with %d-hour interval", interval_hours)
