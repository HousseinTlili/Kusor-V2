from apscheduler.schedulers.background import BackgroundScheduler
from typing import Dict, Any

class CollectorScheduler:
    """
    Runs BCTScraper on a configurable schedule.
    Default: daily at 06:00 Tunis time (UTC+1).
    """

    def __init__(
        self,
        scraper: Any,  # BCTScraper instance
        hour: int = 6,
        minute: int = 0,
    ) -> None:
        self.scraper = scraper
        self.hour = hour
        self.minute = minute
        self.scheduler = BackgroundScheduler()
        
        # Add cron job for daily run
        self.scheduler.add_job(
            self.scraper.run,
            "cron",
            hour=self.hour,
            minute=self.minute,
            id="bct_scraper_job"
        )

    def start(self) -> None:
        """Start the APScheduler background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def run_now(self) -> Dict[str, Any]:
        """Trigger an immediate scraping run (for manual sync)."""
        return self.scraper.run()
