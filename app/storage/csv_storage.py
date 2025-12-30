"""CSV storage for call data capture."""

import csv
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import threading

from app.storage.data_capture import MarketingCallData, NotificationCallData

logger = logging.getLogger(__name__)


class CSVStorage:
    """Thread-safe CSV storage for call data.
    
    Stores marketing and notification call data in separate CSV files.
    """
    
    def __init__(self, data_dir: str = "call_data"):
        """Initialize CSV storage.
        
        Args:
            data_dir: Directory for CSV files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.marketing_file = self.data_dir / "marketing_calls.csv"
        self.notification_file = self.data_dir / "notification_calls.csv"
        
        # Thread lock for safe concurrent writes
        self._lock = threading.Lock()
        
        # Initialize CSV files with headers
        self._init_marketing_csv()
        self._init_notification_csv()
        
        logger.info(f"CSV storage initialized: {self.data_dir}")
    
    def _init_marketing_csv(self):
        """Initialize marketing calls CSV with headers."""
        if not self.marketing_file.exists():
            headers = [
                "call_id",
                "campaign_id",
                "campaign_name",
                "user_interest",
                "language",
                "call_started_at",
                "call_ended_at",
                "call_duration_seconds",
                "response_time_seconds",
                "segment",
                "objective",
                "call_status",
                "notes"
            ]
            
            with open(self.marketing_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created marketing CSV: {self.marketing_file}")
    
    def _init_notification_csv(self):
        """Initialize notification calls CSV with headers."""
        if not self.notification_file.exists():
            headers = [
                "call_id",
                "notification_type",
                "priority",
                "delivered",
                "acknowledged",
                "call_started_at",
                "call_ended_at",
                "call_duration_seconds",
                "language",
                "call_status"
            ]
            
            with open(self.notification_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created notification CSV: {self.notification_file}")
    
    def save_marketing_call(self, data: MarketingCallData) -> bool:
        """Save marketing call data to CSV.
        
        Args:
            data: MarketingCallData instance
            
        Returns:
            True if saved successfully
        """
        try:
            with self._lock:
                with open(self.marketing_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        data.call_id,
                        data.campaign_id,
                        data.campaign_name,
                        data.user_interest,
                        data.language,
                        data.call_started_at.isoformat(),
                        data.call_ended_at.isoformat() if data.call_ended_at else "",
                        data.call_duration_seconds or "",
                        data.response_time_seconds or "",
                        data.segment or "",
                        data.objective or "",
                        data.call_status,
                        data.notes or ""
                    ])
                
                logger.info(f"Saved marketing call data: {data.call_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving marketing call data: {str(e)}", exc_info=True)
            return False
    
    def save_notification_call(self, data: NotificationCallData) -> bool:
        """Save notification call data to CSV.
        
        Args:
            data: NotificationCallData instance
            
        Returns:
            True if saved successfully
        """
        try:
            with self._lock:
                with open(self.notification_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        data.call_id,
                        data.notification_type,
                        data.priority,
                        data.delivered,
                        data.acknowledged,
                        data.call_started_at.isoformat(),
                        data.call_ended_at.isoformat() if data.call_ended_at else "",
                        data.call_duration_seconds or "",
                        data.language,
                        data.call_status
                    ])
                
                logger.info(f"Saved notification call data: {data.call_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving notification call data: {str(e)}", exc_info=True)
            return False
    
    def get_marketing_stats(self, campaign_id: Optional[str] = None) -> dict:
        """Get marketing call statistics.
        
        Args:
            campaign_id: Optional campaign filter
            
        Returns:
            Dictionary with statistics
        """
        try:
            with open(self.marketing_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if campaign_id:
                rows = [r for r in rows if r['campaign_id'] == campaign_id]
            
            total_calls = len(rows)
            if total_calls == 0:
                return {"total_calls": 0}
            
            interest_counts = {}
            for row in rows:
                interest = row['user_interest']
                interest_counts[interest] = interest_counts.get(interest, 0) + 1
            
            return {
                "total_calls": total_calls,
                "interest_breakdown": interest_counts,
                "yes_rate": interest_counts.get('yes', 0) / total_calls * 100,
                "no_rate": interest_counts.get('no', 0) / total_calls * 100,
            }
            
        except Exception as e:
            logger.error(f"Error getting marketing stats: {str(e)}")
            return {"error": str(e)}


# Global storage instance
csv_storage = CSVStorage()
