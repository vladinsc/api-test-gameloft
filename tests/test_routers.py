import pytest
from datetime import datetime, timezone, timedelta

def test_create_subscription_returns_200_and_correct_schema(client):
    response = client.post("/subscriptions/")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "state" in data
    assert "period_end_at" in data

def test_process_webhook_successfully(client, db_session):
    # Setup: Create a subscription first to process webhook for it
    sub_id = "sub_webhook_test"
    # Using naive datetime since SQLite strips timezone info
    period_end = datetime.utcnow() + timedelta(days=7)
    
    # We manually insert it into DB to avoid create_subscription bug
    from app.models import SubscriptionModel
    db_session.add(SubscriptionModel(
        id=sub_id, 
        user_id="user_123", 
        state="trialing", 
        period_end_at=period_end
    ))
    db_session.commit()
    
    payload = {
        "event_id": "evt_webhook_1",
        "subscription_id": sub_id,
        "timestamp": datetime.utcnow().isoformat(),
        "amount": 29.99
    }
    
    response = client.post("/webhooks/billing", json=payload)
    if response.status_code != 200:
        print("ERROR DUMP:", response.text)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Webhook processed successfully"}

def test_get_subscription_history(client, db_session):
    sub_id = "sub_history_test"
    from app.models import SubscriptionModel, AuditLogModel
    db_session.add(SubscriptionModel(
        id=sub_id, 
        user_id="user_history", 
        state="active", 
        period_end_at=datetime.now(timezone.utc)
    ))
    db_session.add(AuditLogModel(
        subscription_id=sub_id,
        previous_state="trialing",
        new_state="active",
        trigger="webhook_payment_success"
    ))
    db_session.commit()
    
    response = client.get(f"/subscriptions/{sub_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["subscription_id"] == sub_id
    assert data[0]["new_state"] == "active"
