from pydantic import BaseModel, Field
from typing import Optional

class Workplace(BaseModel):
    id: str = Field(..., description="Unique identifier for the workplace")
    name: str = Field(..., description="Name of the workplace")
    # Add any other relevant fields for a workplace
