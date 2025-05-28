from fastapi import APIRouter
from .endpoints import home

api_router = APIRouter()
api_router.include_router(home.router, prefix="", tags=["Home"])
