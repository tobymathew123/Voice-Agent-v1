"""Test script for call metrics tracking."""

import logging
from datetime import datetime, date
from app.storage.metrics import CallMetrics, calculate_call_metrics, hash_phone_number
from app.storage.metrics_storage import metrics_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_phone_hashing():
    """Test phone number hashing."""
    print("\n" + "="*60)
    print("Testing Phone Number Hashing")
    print("="*60)
    
    test_numbers = [
        "+15551234567",
        "+919876543210",
        "1234"
    ]
    
    for number in test_numbers:
        hashed = hash_phone_number(number)
        print(f"{number} → {hashed}")
    
    print("\n" + "="*60)


def test_metrics_calculation():
    """Test metrics calculation from session data."""
    print("\n" + "="*60)
    print("Testing Metrics Calculation")
    print("="*60)
    
    # Mock session data
    session_data = {
        'call_id': 'TEST-CALL-001',
        'direction': 'inbound',
        'call_type': 'customer_service',
        'created_at': datetime(2025, 12, 30, 10, 0, 0),
        'answered_at': datetime(2025, 12, 30, 10, 0, 5),
        'ended_at': datetime(2025, 12, 30, 10, 2, 30),
        'status': 'completed',
        'conversation_history': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'},
            {'role': 'user', 'content': 'I need help'},
            {'role': 'assistant', 'content': 'Sure, how can I help?'},
        ],
        'metadata': {},
        'language': 'en-IN'
    }
    
    metrics = calculate_call_metrics(session_data)
    
    print(f"Call ID: {metrics.call_id}")
    print(f"Direction: {metrics.direction}")
    print(f"Type: {metrics.call_type}")
    print(f"Ring Duration: {metrics.ring_duration}s")
    print(f"Talk Duration: {metrics.talk_duration}s")
    print(f"Total Duration: {metrics.total_duration}s")
    print(f"User Turns: {metrics.user_turns}")
    print(f"Agent Turns: {metrics.agent_turns}")
    print(f"Transcript Available: {metrics.transcript_available}")
    
    print("\n" + "="*60)


def test_metrics_storage():
    """Test metrics storage."""
    print("\n" + "="*60)
    print("Testing Metrics Storage")
    print("="*60)
    
    # Create test metrics
    test_metrics = [
        CallMetrics(
            call_id=f"TEST-{i}",
            direction="inbound" if i % 2 == 0 else "outbound",
            call_type="customer_service" if i % 3 == 0 else "marketing",
            call_started_at=datetime.utcnow(),
            call_answered_at=datetime.utcnow(),
            call_ended_at=datetime.utcnow(),
            ring_duration=5,
            talk_duration=120 + i*10,
            total_duration=125 + i*10,
            call_status="completed",
            call_cost=2.5 + i*0.5,
            user_turns=3 + i,
            agent_turns=3 + i,
            transcript_available=True
        )
        for i in range(5)
    ]
    
    print(f"\nSaving {len(test_metrics)} test metrics...")
    for metrics in test_metrics:
        success = metrics_storage.save_call_metrics(metrics)
        status = "✓" if success else "✗"
        print(f"{status} Saved: {metrics.call_id}")
    
    print(f"\nMetrics file: {metrics_storage.metrics_file}")
    
    print("\n" + "="*60)


def test_daily_summary():
    """Test daily summary generation."""
    print("\n" + "="*60)
    print("Testing Daily Summary")
    print("="*60)
    
    # Get today's summary
    summary = metrics_storage.get_daily_summary()
    
    print(f"\nDate: {summary.date}")
    print(f"Total Calls: {summary.total_calls}")
    print(f"Inbound: {summary.inbound_calls}")
    print(f"Outbound: {summary.outbound_calls}")
    print(f"Marketing: {summary.marketing_calls}")
    print(f"Completed: {summary.completed_calls}")
    print(f"Avg Talk Duration: {summary.avg_talk_duration:.1f}s" if summary.avg_talk_duration else "N/A")
    print(f"Total Cost: ₹{summary.total_cost:.2f}")
    print(f"Avg Cost/Call: ₹{summary.avg_cost_per_call:.2f}" if summary.avg_cost_per_call else "N/A")
    
    # Save summary
    if summary.total_calls > 0:
        metrics_storage.save_daily_summary(summary)
        print(f"\n✓ Daily summary saved to: {metrics_storage.daily_summary_file}")
    
    print("\n" + "="*60)


def test_metrics_overview():
    """Test overall metrics overview."""
    print("\n" + "="*60)
    print("Testing Metrics Overview")
    print("="*60)
    
    overview = metrics_storage.get_metrics_overview()
    
    print(f"\nTotal Calls: {overview.get('total_calls', 0)}")
    print(f"Completed Calls: {overview.get('completed_calls', 0)}")
    print(f"Completion Rate: {overview.get('completion_rate', 0):.1f}%")
    print(f"Total Duration: {overview.get('total_duration_minutes', 0):.1f} minutes")
    print(f"Total Cost: ₹{overview.get('total_cost', 0):.2f}")
    print(f"Avg Cost/Call: ₹{overview.get('avg_cost_per_call', 0):.2f}")
    
    print("\n" + "="*60)


def main():
    """Run all metrics tests."""
    print("\n" + "="*60)
    print("CALL METRICS TRACKING TESTS")
    print("="*60)
    
    try:
        test_phone_hashing()
        test_metrics_calculation()
        test_metrics_storage()
        test_daily_summary()
        test_metrics_overview()
        
        print("\n" + "="*60)
        print("All metrics tests completed!")
        print(f"Data location: {metrics_storage.data_dir}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
