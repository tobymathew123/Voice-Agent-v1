"""Test script for data capture functionality."""

import asyncio
import logging
from datetime import datetime
from app.storage.data_capture import MarketingCallData, extract_user_interest, UserInterest
from app.storage.csv_storage import csv_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_interest_extraction():
    """Test user interest extraction."""
    print("\n" + "="*60)
    print("Testing Interest Extraction")
    print("="*60)
    
    test_cases = [
        ("Yes, I'm interested", UserInterest.YES),
        ("No, not interested", UserInterest.NO),
        ("Maybe later", UserInterest.MAYBE),
        ("I'm not sure", UserInterest.UNSURE),
        ("", UserInterest.NO_RESPONSE),
        ("Definitely yes!", UserInterest.YES),
        ("Absolutely not", UserInterest.NO),
        ("I'll think about it", UserInterest.MAYBE),
    ]
    
    for response, expected in test_cases:
        result = extract_user_interest(response)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{response}' → {result} (expected: {expected})")
    
    print("\n" + "="*60)


def test_csv_storage():
    """Test CSV storage."""
    print("\n" + "="*60)
    print("Testing CSV Storage")
    print("="*60)
    
    # Create test marketing call data
    test_data = MarketingCallData(
        call_id="TEST123",
        campaign_id="CAMP-TEST-001",
        campaign_name="Test Campaign",
        user_interest=UserInterest.YES,
        language="en-IN",
        call_started_at=datetime.utcnow(),
        call_ended_at=datetime.utcnow(),
        call_duration_seconds=45,
        response_time_seconds=5,
        segment="test_segment",
        objective="testing",
        call_status="completed",
        notes="Test call for data capture"
    )
    
    print(f"\nSaving test marketing call: {test_data.call_id}")
    success = csv_storage.save_marketing_call(test_data)
    
    if success:
        print(f"✓ Data saved successfully to: {csv_storage.marketing_file}")
    else:
        print("✗ Failed to save data")
    
    # Get statistics
    print("\nRetrieving statistics...")
    stats = csv_storage.get_marketing_stats()
    print(f"Total calls: {stats.get('total_calls', 0)}")
    print(f"Interest breakdown: {stats.get('interest_breakdown', {})}")
    
    print("\n" + "="*60)


def test_multiple_campaigns():
    """Test data capture for multiple campaigns."""
    print("\n" + "="*60)
    print("Testing Multiple Campaigns")
    print("="*60)
    
    campaigns = [
        {
            "campaign_id": "CAMP-2025-Q1-001",
            "campaign_name": "Premium Credit Card",
            "responses": ["Yes, interested", "No thanks", "Maybe later", "Yes definitely"]
        },
        {
            "campaign_id": "CAMP-2025-Q1-002",
            "campaign_name": "Home Loan Offer",
            "responses": ["Not interested", "I'll think about it", "Yes please"]
        }
    ]
    
    for campaign in campaigns:
        print(f"\nCampaign: {campaign['campaign_name']}")
        
        for i, response in enumerate(campaign['responses'], 1):
            interest = extract_user_interest(response)
            
            data = MarketingCallData(
                call_id=f"{campaign['campaign_id']}-CALL-{i}",
                campaign_id=campaign['campaign_id'],
                campaign_name=campaign['campaign_name'],
                user_interest=interest,
                language="en-IN",
                call_started_at=datetime.utcnow(),
                call_ended_at=datetime.utcnow(),
                call_duration_seconds=30 + i*10,
                segment="test",
                objective="product_promotion",
                call_status="completed"
            )
            
            csv_storage.save_marketing_call(data)
            print(f"  Call {i}: '{response}' → {interest}")
    
    # Get campaign-specific stats
    for campaign in campaigns:
        print(f"\nStats for {campaign['campaign_name']}:")
        stats = csv_storage.get_marketing_stats(campaign['campaign_id'])
        print(f"  Total calls: {stats.get('total_calls', 0)}")
        print(f"  Yes rate: {stats.get('yes_rate', 0):.1f}%")
        print(f"  No rate: {stats.get('no_rate', 0):.1f}%")
    
    print("\n" + "="*60)


def main():
    """Run all data capture tests."""
    print("\n" + "="*60)
    print("DATA CAPTURE TESTS")
    print("="*60)
    
    try:
        test_interest_extraction()
        test_csv_storage()
        test_multiple_campaigns()
        
        print("\n" + "="*60)
        print("All data capture tests completed!")
        print(f"Data files location: {csv_storage.data_dir}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
