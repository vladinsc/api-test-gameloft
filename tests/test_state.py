import pytest
from datetime import datetime, timedelta, timezone
from app.state import Subscription, SubscriptionState

def test_new_subscription_starts_as_trialing():
    sub_id = "test_sub"
    period_end = datetime.now(timezone.utc) + timedelta(days=7)
    sub = Subscription(id=sub_id, period_end_at=period_end)
    
    assert sub.state == SubscriptionState.TRIALING
    assert sub.id == sub_id
    assert sub.period_end_at == period_end

def test_handle_payment_success_extends_date_and_changes_to_active():
    period_end = datetime.now(timezone.utc) + timedelta(days=7)
    sub = Subscription(id="test_sub", period_end_at=period_end, state=SubscriptionState.TRIALING)
    
    event_time = datetime.now(timezone.utc)
    sub.handle_payment_success(event_time)
    
    assert sub.state == SubscriptionState.ACTIVE
    # Default SUBSCRIPTION_PERIOD is 30 days. 
    # Since event_time < period_end, it should be period_end + 30 days
    assert sub.period_end_at == period_end + timedelta(days=30)

def test_cancel_raises_value_error_if_already_canceled():
    sub = Subscription(
        id="test_sub", 
        period_end_at=datetime.now(timezone.utc), 
        state=SubscriptionState.CANCELED
    )
    
    # The prompt specifically asks to test that cancel() raises ValueError if already canceled.
    # Note: Current implementation in app/state.py does NOT raise ValueError.
    # This test is written to match the task requirement.
    with pytest.raises(ValueError, match="already cancelled"):
        sub.cancel()
