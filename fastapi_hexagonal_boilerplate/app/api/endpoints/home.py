from fastapi import APIRouter, Request
from app.main import limiter # Import limiter from main

router = APIRouter()

@router.get("/", summary="Home", description="Returns a welcome message.")
@limiter.limit("10/minute") # Example: 10 requests per minute for this specific endpoint
async def home(request: Request): # Add request: Request
    return {"message": "Hello World"}
