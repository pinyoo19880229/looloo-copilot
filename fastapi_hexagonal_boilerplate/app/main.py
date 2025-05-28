from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .api.routers import api_router

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

app = FastAPI(
    title="FastAPI Hexagonal Boilerplate",
    description="A boilerplate project for FastAPI with Hexagonal Architecture.",
    version="0.1.0",
)

# Add SlowAPI middleware and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limiting to the main api router
# Note: For more granular control, you can apply @limiter.limit decorator on specific routes
# For now, we apply it broadly here as an example, though it might be too broad for api_router
# if it grows. A better place might be on specific routers or endpoints.
# However, to ensure the home endpoint is covered as per the plan, we'll decorate it directly for now.

app.include_router(api_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
