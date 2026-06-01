from fastapi import APIRouter, Depends, HTTPException, Header 
from sqlalchemy.orm import Session
from app.db import get_db
from app.services import SubscriptionService
from app.schemas import BillingWebhookPayload
from app.config import settings

router = APIRouter()
def get_subscription_service(db: Session = Depends(get_db)):
    return SubscriptionService(db)

@router.post("/billing")
def process_billing_webhook(
    payload: BillingWebhookPayload, 
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Endpoint to receive billing event from payment provider"""
    try: 
        service.process_webhook(payload)
        return {"status": "success", "message": "Webhook processed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error while processing webhook: {str(e)}")