from fastapi import FastAPI
from  app.db import engine, get_db
from app.models import Base
from app.config import settings
from app.routers import subscriptions, webhooks

Base.metadata.create_all(bind=engine) # nu ma complic cu migratii 
app = FastAPI(title="Subscription Management API", version="1.0", description="Merge bine I hope))")

app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
@app.get("/health")
async def health_check():
    return {"message": "API is running smoothly"}
