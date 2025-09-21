"""
Scheduler for the MDS Knowledge Capture Agent.
Handles periodic execution based on configuration settings.
"""

import os
import json
import logging
import signal
import sys
from datetime import datetime, time
from typing import Dict, Optional
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from agent import MDSKnowledgeCaptureAgent

logger = logging.getLogger(__name__)


class AgentScheduler:
    """Scheduler for running the MDS Knowledge Capture Agent periodically."""
    
    def __init__(self, config_path: str = "config/agent_config.json"):
        """Initialize scheduler with configuration."""
        self.config = self._load_config(config_path)
        self.scheduler = BlockingScheduler()
        self.agent = None
        self._setup_logging()
        self._setup_signal_handlers()
        
        logger.info("Agent scheduler initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def _setup_logging(self) -> None:
        """Setup logging for scheduler."""
        log_config = self.config.get("logging", {})
        
        # Ensure log directory exists
        log_file = log_config.get("file", "logs/scheduler.log")
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging with scheduler-specific file
        scheduler_log_file = str(Path(log_file).parent / "scheduler.log")
        
        logging.basicConfig(
            level=getattr(logging, log_config.get("level", "INFO")),
            format=log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            handlers=[
                logging.FileHandler(scheduler_log_file),
                logging.StreamHandler()
            ]
        )
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down scheduler gracefully...")
            self.scheduler.shutdown(wait=False)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    def run_agent(self) -> None:
        """Execute the agent and log results."""
        run_timestamp = datetime.now().isoformat()
        logger.info(f"Starting scheduled agent run at {run_timestamp}")
        
        try:
            # Initialize fresh agent instance for this run
            self.agent = MDSKnowledgeCaptureAgent()
            
            # Execute agent
            result = self.agent.run()
            
            # Log summary
            logger.info(f"Agent run completed successfully")
            logger.info(f"Status: {result['status']}")
            logger.info(f"URLs processed: {len(result.get('urls', []))}")
            logger.info(f"PDFs discovered: {len(result.get('discovered_pdfs', []))}")
            logger.info(f"Documents downloaded: {len(result.get('downloaded_docs', []))}")
            logger.info(f"Documents processed: {len(result.get('processed_docs', []))}")
            logger.info(f"Errors: {len(result.get('errors', []))}")
            
            if result.get('errors'):
                logger.warning("Errors encountered during run:")
                for error in result['errors']:
                    logger.warning(f"  - {error}")
            
            # Log detailed results to separate file for analysis
            self._log_detailed_results(result)
            
        except Exception as e:
            logger.error(f"Scheduled agent run failed: {e}")
            raise
    
    def _log_detailed_results(self, result: Dict) -> None:
        """Log detailed results to a separate file for analysis."""
        try:
            results_dir = Path("logs/runs")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"agent_run_{timestamp}.json"
            
            # Prepare results for JSON serialization
            json_result = {
                "run_id": result.get("run_id"),
                "timestamp": timestamp,
                "status": result.get("status"),
                "urls_processed": len(result.get("urls", [])),
                "pdfs_discovered": len(result.get("discovered_pdfs", [])),
                "documents_downloaded": len(result.get("downloaded_docs", [])),
                "documents_processed": len(result.get("processed_docs", [])),
                "errors": result.get("errors", []),
                "analysis": result.get("analysis", ""),
                "downloaded_files": [
                    {
                        "filename": doc.get("filename"),
                        "url": doc.get("url"),
                        "size": doc.get("file_size"),
                        "version": doc.get("version")
                    }
                    for doc in result.get("downloaded_docs", [])
                ],
                "processed_files": [
                    {
                        "filename": Path(doc.get("current_file_path", "")).name,
                        "is_update": doc.get("is_update", False),
                        "version": doc.get("version")
                    }
                    for doc in result.get("processed_docs", [])
                ]
            }
            
            with open(results_file, 'w') as f:
                json.dump(json_result, f, indent=2)
            
            logger.info(f"Detailed results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save detailed results: {e}")
    
    def job_listener(self, event) -> None:
        """Listen for job execution events."""
        if event.exception:
            logger.error(f"Scheduled job failed: {event.exception}")
        else:
            logger.info(f"Scheduled job completed successfully: {event.job_id}")
    
    def start(self) -> None:
        """Start the scheduler based on configuration."""
        schedule_config = self.config.get("agent", {}).get("schedule", {})
        
        if not schedule_config.get("enabled", False):
            logger.info("Scheduling is disabled in configuration")
            return
        
        # Parse schedule configuration
        interval = schedule_config.get("interval", "weekly")
        day_of_week = schedule_config.get("day_of_week", "sunday")
        run_time = schedule_config.get("time", "02:00")
        
        # Parse time
        try:
            hour, minute = map(int, run_time.split(':'))
            run_time_obj = time(hour=hour, minute=minute)
        except ValueError:
            logger.error(f"Invalid time format: {run_time}. Using default 02:00")
            run_time_obj = time(hour=2, minute=0)
        
        # Configure schedule
        if interval == "weekly":
            # Map day names to numbers (Monday = 0)
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day_num = day_map.get(day_of_week.lower(), 6)  # Default to Sunday
            
            trigger = CronTrigger(
                day_of_week=day_num,
                hour=run_time_obj.hour,
                minute=run_time_obj.minute
            )
            
            logger.info(f"Scheduling weekly runs on {day_of_week} at {run_time}")
            
        elif interval == "daily":
            trigger = CronTrigger(
                hour=run_time_obj.hour,
                minute=run_time_obj.minute
            )
            
            logger.info(f"Scheduling daily runs at {run_time}")
            
        else:
            logger.error(f"Unsupported interval: {interval}")
            return
        
        # Add job to scheduler
        self.scheduler.add_job(
            func=self.run_agent,
            trigger=trigger,
            id='mds_knowledge_capture',
            name='MDS Knowledge Capture Agent',
            misfire_grace_time=3600,  # 1 hour grace time
            coalesce=True,  # Combine multiple missed runs into one
            max_instances=1  # Only allow one instance at a time
        )
        
        # Add event listener
        self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        logger.info("Starting scheduler...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise
    
    def run_once(self) -> None:
        """Run the agent once immediately (for testing)."""
        logger.info("Running agent once (immediate execution)")
        self.run_agent()


def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MDS Knowledge Capture Agent Scheduler')
    parser.add_argument('--once', action='store_true', 
                       help='Run the agent once immediately instead of scheduling')
    parser.add_argument('--config', default='config/agent_config.json',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    try:
        scheduler = AgentScheduler(args.config)
        
        if args.once:
            scheduler.run_once()
        else:
            scheduler.start()
            
    except KeyboardInterrupt:
        print("\nScheduler interrupted by user")
    except Exception as e:
        print(f"Scheduler failed: {e}")
        logger.error(f"Scheduler main execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()