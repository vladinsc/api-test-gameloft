from uuid_extensions import uuid7
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.repo import SubscriptionRepository
from app.state import Subscription, SubscriptionState
from app.schemas import BillingWebhookPayload
from app.config import settings

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SubscriptionRepository(db)
    def create_subscription(self) -> Subscription: 
        """Create new subscription with default trial period and return it"""
        subscription = Subscription(
            id=f"sub_{uuid7().hex}",
            state=SubscriptionState.trial,
            period_end_at=datetime.now(timezone.utc) + timedelta(days=settings.trial_period_days)
        )
        try: 
            self.repo.save(subscription, trigger="subscription_created")
            self.db.commit()
            return subscription
        except Exception as e:
            self.db.rollback()
            raise e
    def get_subscription(self, subscription_id: str) -> Subscription:
        """Fetch subscription by ID"""
        return self.repo.get_by_id(subscription_id)
    
    def cancel_subscription(self, subscription_id: str) -> Subscription:
        """User initiaded cancellation"""
        try: 
            subscription = self.repo.get_by_id_for_update(subscription_id)
            if not subscription:
                return None
            subscription.cancel()
            self.repo.save(subscription, trigger="user_cancellation")
            self.db.commit()
            return subscription 
        except Exception as e:
            self.db.rollback()
            raise e
    
    def process_webhook(self, payload: BillingWebhookPayload) -> Subscription:
        """Process incoming billing event webhook from payment provider and update subscription state accordingly"""
        try: 
            if self.repo.is_event_processed(payload.event_id):
                self.db.commit() # commit to release the lock acquired by is_event_processed
                return 
            
            subscription = self.repo.get_by_id_for_update(payload.subscription_id)
            if not subscription:
                self.db.rollback()
                raise ValueError(f"Subscription with id {payload.subscription_id} not found")
            
            if payload.amount > 0:
                subscription.handle_payment_success(payload.timestamp)
                trigger = "webhook_payment_success"
            else:
                subscription.handle_payment_failure(payload.timestamp)
                trigger = "webhook_payment_failure"
            self.repo.save(subscription, trigger=trigger)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_subscription_history(self, subscription_id: str) -> list:
        """Retrieves the audit trail for a specific subscription."""
        subscription = self.repo.get_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        return self.repo.get_audit_history(subscription_id)
        