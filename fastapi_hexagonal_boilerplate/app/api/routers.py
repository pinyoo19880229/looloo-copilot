from fastapi import APIRouter
from .endpoints import home # Assuming home is still there
from .endpoints import dashboard # New import

api_router = APIRouter()

# Include existing routers (if any)
api_router.include_router(home.router, tags=["Home"]) 

# Include the new dashboard router
api_router.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"]) # Example prefix
