from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, timedelta

# Helper function for default dates
def default_start_date():
    return date.today() - timedelta(days=365)

class ReportRequestParams(BaseModel):
    workplace_ids: Optional[List[str]] = Field(default_factory=list, description="List of workplace_ids to filter. Empty means all accessible.")
    start_date: date = Field(default_factory=default_start_date, description="Start date for the report period.")
    end_date: date = Field(default_factory=date.today, description="End date for the report period.")
    period: str = Field(default="month", description="Group data by period: day, week, month, year.")
    reports: List[str] = Field(..., description="Keys of the data to export.")

    class Config:
        # Allow population by alias for query params like "workplace_ids" from "workplace_ids,"
        populate_by_name = True 
        # Example for alias if query params are different from model fields
        # field_serializers = {
        #     'workplace_ids': lambda v: ",".join(v) if v else None,
        # }
        # For now, we'll handle comma-separated string to list conversion in the endpoint.

class ReportFile(BaseModel):
    filename: str = Field(..., description="Filename for this part of the report (e.g., 'activity_summary.csv')")
    content: Any = Field(..., description="Data content for this file (e.g., list of dicts for CSV, or string for plain text)")
    content_type: str = Field(default="text/csv", description="MIME type for the content")


class GeneratedReport(BaseModel):
    files: List[ReportFile] = Field(..., description="List of files included in the zipped report")
    # metadata: Optional[dict] = None # Could include overall report metadata
