"""API endpoints for data analytics and reporting."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date
import logging

from app.storage.csv_storage import csv_storage
from app.storage.metrics_storage import metrics_storage

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/marketing/stats")
async def get_marketing_stats(campaign_id: Optional[str] = Query(None)):
    """Get marketing call statistics.
    
    Args:
        campaign_id: Optional campaign ID filter
        
    Returns:
        Statistics dictionary
    """
    try:
        stats = csv_storage.get_marketing_stats(campaign_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting marketing stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")


@router.get("/marketing/export")
async def export_marketing_data(campaign_id: Optional[str] = Query(None)):
    """Export marketing call data.
    
    Args:
        campaign_id: Optional campaign ID filter
        
    Returns:
        File path information
    """
    try:
        return {
            "file_path": str(csv_storage.marketing_file),
            "message": "Marketing data is stored in CSV format",
            "note": "Download the file directly from the server"
        }
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error exporting data")


@router.get("/metrics/overview")
async def get_metrics_overview():
    """Get overall call metrics overview.
    
    Returns:
        Metrics overview dictionary
    """
    try:
        overview = metrics_storage.get_metrics_overview()
        return overview
    except Exception as e:
        logger.error(f"Error getting metrics overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")


@router.get("/metrics/daily")
async def get_daily_metrics(target_date: Optional[str] = Query(None)):
    """Get daily metrics summary.
    
    Args:
        target_date: Date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Daily metrics summary
    """
    try:
        if target_date:
            target = date.fromisoformat(target_date)
        else:
            target = None
        
        summary = metrics_storage.get_daily_summary(target)
        return summary.dict()
    except Exception as e:
        logger.error(f"Error getting daily metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving daily metrics")
