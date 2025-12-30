"""Metrics storage and aggregation."""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, date
from collections import defaultdict
import threading

from app.storage.metrics import CallMetrics, DailyMetricsSummary

logger = logging.getLogger(__name__)


class MetricsStorage:
    """Storage and aggregation for call metrics.
    
    Stores detailed call metrics in CSV for admin dashboard.
    Provides aggregation functions for daily/monthly summaries.
    """
    
    def __init__(self, data_dir: str = "call_data"):
        """Initialize metrics storage.
        
        Args:
            data_dir: Directory for metrics files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.metrics_file = self.data_dir / "call_metrics.csv"
        self.daily_summary_file = self.data_dir / "daily_summary.csv"
        
        # Thread lock for safe concurrent writes
        self._lock = threading.Lock()
        
        # Initialize CSV files
        self._init_metrics_csv()
        self._init_daily_summary_csv()
        
        logger.info(f"Metrics storage initialized: {self.data_dir}")
    
    def _init_metrics_csv(self):
        """Initialize call metrics CSV with headers."""
        if not self.metrics_file.exists():
            headers = [
                "call_id",
                "vobiz_call_sid",
                "direction",
                "call_type",
                "from_number_hash",
                "to_number_hash",
                "call_started_at",
                "call_answered_at",
                "call_ended_at",
                "ring_duration",
                "talk_duration",
                "total_duration",
                "call_status",
                "disconnect_reason",
                "call_cost",
                "currency",
                "audio_quality",
                "transcript_available",
                "campaign_id",
                "agent_persona",
                "user_turns",
                "agent_turns",
                "language",
                "notes"
            ]
            
            with open(self.metrics_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created metrics CSV: {self.metrics_file}")
    
    def _init_daily_summary_csv(self):
        """Initialize daily summary CSV with headers."""
        if not self.daily_summary_file.exists():
            headers = [
                "date",
                "total_calls",
                "inbound_calls",
                "outbound_calls",
                "marketing_calls",
                "notification_calls",
                "customer_service_calls",
                "completed_calls",
                "failed_calls",
                "no_answer_calls",
                "avg_talk_duration",
                "total_talk_duration",
                "total_cost",
                "avg_cost_per_call",
                "avg_user_turns",
                "transcript_coverage"
            ]
            
            with open(self.daily_summary_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Created daily summary CSV: {self.daily_summary_file}")
    
    def save_call_metrics(self, metrics: CallMetrics) -> bool:
        """Save call metrics to CSV.
        
        Args:
            metrics: CallMetrics instance
            
        Returns:
            True if saved successfully
        """
        try:
            with self._lock:
                with open(self.metrics_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        metrics.call_id,
                        metrics.vobiz_call_sid or "",
                        metrics.direction,
                        metrics.call_type,
                        metrics.from_number_hash or "",
                        metrics.to_number_hash or "",
                        metrics.call_started_at.isoformat(),
                        metrics.call_answered_at.isoformat() if metrics.call_answered_at else "",
                        metrics.call_ended_at.isoformat() if metrics.call_ended_at else "",
                        metrics.ring_duration or "",
                        metrics.talk_duration or "",
                        metrics.total_duration or "",
                        metrics.call_status,
                        metrics.disconnect_reason or "",
                        metrics.call_cost or "",
                        metrics.currency,
                        metrics.audio_quality or "",
                        metrics.transcript_available,
                        metrics.campaign_id or "",
                        metrics.agent_persona or "",
                        metrics.user_turns,
                        metrics.agent_turns,
                        metrics.language,
                        metrics.notes or ""
                    ])
                
                logger.info(f"Saved call metrics: {metrics.call_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving call metrics: {str(e)}", exc_info=True)
            return False
    
    def get_daily_summary(self, target_date: Optional[date] = None) -> DailyMetricsSummary:
        """Get daily metrics summary.
        
        Args:
            target_date: Date to summarize (defaults to today)
            
        Returns:
            DailyMetricsSummary instance
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [r for r in reader if r['call_started_at'].startswith(date_str)]
            
            if not rows:
                return DailyMetricsSummary(date=date_str)
            
            # Aggregate metrics
            summary = DailyMetricsSummary(date=date_str)
            summary.total_calls = len(rows)
            
            total_talk_duration = 0
            total_cost = 0.0
            total_user_turns = 0
            transcripts_count = 0
            
            for row in rows:
                # Direction
                if row['direction'] == 'inbound':
                    summary.inbound_calls += 1
                else:
                    summary.outbound_calls += 1
                
                # Call type
                if row['call_type'] == 'marketing':
                    summary.marketing_calls += 1
                elif row['call_type'] == 'notification':
                    summary.notification_calls += 1
                elif row['call_type'] == 'customer_service':
                    summary.customer_service_calls += 1
                
                # Status
                if row['call_status'] == 'completed':
                    summary.completed_calls += 1
                elif row['call_status'] == 'failed':
                    summary.failed_calls += 1
                elif row['call_status'] == 'no_answer':
                    summary.no_answer_calls += 1
                
                # Duration
                if row['talk_duration']:
                    total_talk_duration += int(row['talk_duration'])
                
                # Cost
                if row['call_cost']:
                    total_cost += float(row['call_cost'])
                
                # User turns
                if row['user_turns']:
                    total_user_turns += int(row['user_turns'])
                
                # Transcripts
                if row['transcript_available'] == 'True':
                    transcripts_count += 1
            
            # Calculate averages
            summary.total_talk_duration = total_talk_duration
            if summary.total_calls > 0:
                summary.avg_talk_duration = total_talk_duration / summary.total_calls
                summary.avg_user_turns = total_user_turns / summary.total_calls
                summary.transcript_coverage = (transcripts_count / summary.total_calls) * 100
            
            summary.total_cost = total_cost
            if summary.total_calls > 0:
                summary.avg_cost_per_call = total_cost / summary.total_calls
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting daily summary: {str(e)}")
            return DailyMetricsSummary(date=date_str)
    
    def save_daily_summary(self, summary: DailyMetricsSummary) -> bool:
        """Save daily summary to CSV.
        
        Args:
            summary: DailyMetricsSummary instance
            
        Returns:
            True if saved successfully
        """
        try:
            with self._lock:
                with open(self.daily_summary_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        summary.date,
                        summary.total_calls,
                        summary.inbound_calls,
                        summary.outbound_calls,
                        summary.marketing_calls,
                        summary.notification_calls,
                        summary.customer_service_calls,
                        summary.completed_calls,
                        summary.failed_calls,
                        summary.no_answer_calls,
                        summary.avg_talk_duration or "",
                        summary.total_talk_duration,
                        summary.total_cost,
                        summary.avg_cost_per_call or "",
                        summary.avg_user_turns or "",
                        summary.transcript_coverage or ""
                    ])
                
                logger.info(f"Saved daily summary: {summary.date}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving daily summary: {str(e)}", exc_info=True)
            return False
    
    def get_metrics_overview(self) -> Dict:
        """Get overall metrics overview.
        
        Returns:
            Dictionary with overview statistics
        """
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                return {"total_calls": 0}
            
            total_calls = len(rows)
            completed = len([r for r in rows if r['call_status'] == 'completed'])
            
            total_duration = sum(int(r['total_duration']) for r in rows if r['total_duration'])
            total_cost = sum(float(r['call_cost']) for r in rows if r['call_cost'])
            
            return {
                "total_calls": total_calls,
                "completed_calls": completed,
                "completion_rate": (completed / total_calls * 100) if total_calls > 0 else 0,
                "total_duration_minutes": total_duration / 60,
                "total_cost": total_cost,
                "avg_cost_per_call": (total_cost / total_calls) if total_calls > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics overview: {str(e)}")
            return {"error": str(e)}


# Global storage instance
metrics_storage = MetricsStorage()
