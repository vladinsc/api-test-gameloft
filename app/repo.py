from sqlalchemy.orm import Session
from app.models import SubscriptionModel, ProcessedEventModel, AuditLogModel
from app.state import SubscriptionState, Subscription

class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_by_id(self, subscription_id: str) -> Subscription:
        model = self.db.query(SubscriptionModel).filter_by(id=subscription_id).first()
        if not model:
            return None
        return self._model_to_subscription(model)
    def get_by_id_for_update(self, subscription_id: str) -> Subscription:
        """Fetch subscription with FOR UPDATE lock for concurrency control"""
        model = self.db.query(SubscriptionModel).filter_by(id=subscription_id).with_for_update().first()
        if not model:
            return None
        return self._model_to_subscription(model)
    def save(self, subscription: Subscription, trigger: str="system_update"):
        model = self.db.query(SubscriptionModel).filter_by(id=subscription.id).first()
        isnew = False
        previous_state = None
        previous_period_end = None
        if not model:
            model = SubscriptionModel(id=subscription.id, user_id="unknown")
            isnew = True
            self.db.add(model)
        else:
            previous_state = model.state
            previous_period_end = model.period_end_at
        model.state = subscription.state.value
        model.period_end_at = subscription.period_end_at
        if isnew or (previous_state != model.state) or (previous_period_end != model.period_end_at):
            audit_log = AuditLogModel(
                subscription_id=model.id,
                previous_state=previous_state,
                new_state=model.state,
                trigger=trigger
            )
            self.db.add(audit_log)
    def is_event_processed(self, event_id: str) -> bool:
        exists = self.db.query(ProcessedEventModel).filter_by(event_id=event_id).first()
        if exists:
            return True
        self.db.add(ProcessedEventModel(event_id=event_id))
        return False
    def _model_to_subscription(self, model: SubscriptionModel) -> Subscription:
        """Convert SQLAlchemy model to StateMachine Subscription object"""
        return Subscription(
            id=model.id,
            state=SubscriptionState(model.state),
            period_end_at=model.period_end_at
        )
    
    def get_audit_history(self, sub_id: str) -> list[AuditLogModel]:
        """Fetches the chronological history of a subscription."""
        return self.db.query(AuditLogModel)\
            .filter_by(subscription_id=sub_id)\
            .order_by(AuditLogModel.timestamp.desc())\
            .all()