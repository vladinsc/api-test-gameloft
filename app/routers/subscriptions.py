from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services import SubscriptionService    
from app.schemas import AuditLogResponse, SubscriptionResponse, CancelResponse
router = APIRouter()

def get_subscription_service(db: Session = Depends(get_db)):
    return SubscriptionService(db)

@router.post("/", response_model=SubscriptionResponse)
def create_subscription(service: SubscriptionService = Depends(get_subscription_service)):
    """Creates a new subscription with default trial period and returns it
    """
    subscription = service.create_subscription()
    return subscription

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: str, service: SubscriptionService = Depends(get_subscription_service)):
    """Returns the subscrption's state, by subscription_id"""
    subscription = service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@router.post("/{subscription_id}/cancel", response_model=CancelResponse)
def cancel_subscription(subscription_id: str, service: SubscriptionService = Depends(get_subscription_service)):
    """User-initiated cancelation of subscription"""
    try: 
        subscription = service.cancel_subscription(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return {
            "message": f"Subscription cancelled successfully",
            "subscription": subscription
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{subscription_id}/history", response_model=list[AuditLogResponse])
def get_subscription_history(
    subscription_id: str, 
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Fetches the complete audit log of state changes for a subscription."""
    try:
        return service.get_subscription_history(subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))