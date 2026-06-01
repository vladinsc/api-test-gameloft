from typing import Optional

from pydantic import BaseModel, Field,ConfigDict
from datetime import datetime
from app.state import SubscriptionState

# inbound
class  SubscriptionCreateRequest(BaseModel):
    pass

class BillingWebhookPayload(BaseModel):
    event_id: str = Field(..., description="The unique identifier of the billing event for idempotency")
    subscription_id: str = Field(..., description="The unique identifier of the subscription in our system")
    timestamp: datetime = Field(..., description="The timestamp of when the billing event occurred")
    amount: float = Field(..., description="The amount billed for the subscription event")

# outbound 
class SubscriptionResponse(BaseModel):
    id: str
    state: SubscriptionState
    period_ned_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CancelResponse(BaseModel):
    message: str
    subscription: SubscriptionResponse

class AuditLogResponse(BaseModel):
    id: int
    subscription_id: str
    previous_state: Optional[str]
    new_state: str
    trigger: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)