from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone
Base = declarative_base()

class SubscriptionModel(Base):
    __tablename__ = 'subscriptions'

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    state = Column(String, nullable=False)
    period_end_at = Column(DateTime, nullable=False)
    audit_logs = relationship("AuditLogModel", back_populates="subscription")

class ProcessedEventModel(Base):
    """Table for idempotency check of billing events"""
    __tablename__ = 'processed_events'
    event_id = Column(String, primary_key=True, index=True)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLogModel(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subscription_id = Column(String, ForeignKey('subscriptions.id'))
    subscription = relationship("SubscriptionModel", back_populates="audit_logs")
    previous_state = Column(String, nullable=True) # Creation has no previous state
    new_state = Column(String, nullable=False)
    trigger = Column(String, nullable=False) # user_action, webhook_payment_success, webhook_payment_failure, etc. 
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))