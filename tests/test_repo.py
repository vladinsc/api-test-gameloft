import pytest
from datetime import datetime, timezone, timedelta
from app.repo import SubscriptionRepository
from app.state import Subscription, SubscriptionState
from app.models import AuditLogModel, SubscriptionModel

def test_saving_new_subscription_creates_audit_log(db_session):
    repo = SubscriptionRepository(db_session)
    period_end = datetime.now(timezone.utc) + timedelta(days=7)
    sub = Subscription(id="sub_repo_test", period_end_at=period_end, state=SubscriptionState.TRIALING)
    
    repo.save(sub, trigger="test_creation")
    db_session.commit()
    
    # Check subscription exists
    sub_model = db_session.query(SubscriptionModel).filter_by(id="sub_repo_test").first()
    assert sub_model is not None
    assert sub_model.state == "trialing"
    
    # Check audit log exists
    audit_logs = db_session.query(AuditLogModel).filter_by(subscription_id="sub_repo_test").all()
    assert len(audit_logs) == 1
    assert audit_logs[0].new_state == "trialing"
    assert audit_logs[0].trigger == "test_creation"
    assert audit_logs[0].previous_state is None

def test_is_event_processed_idempotency(db_session):
    repo = SubscriptionRepository(db_session)
    event_id = "evt_123"
    
    # First time returns False (not processed yet, but it marks it as added to session)
    assert repo.is_event_processed(event_id) is False
    db_session.commit()
    
    # Second time returns True
    assert repo.is_event_processed(event_id) is True
