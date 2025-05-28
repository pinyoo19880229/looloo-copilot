from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import date, timedelta
import io
import csv
import zipfile # Standard library for zip file creation

from app.core.models.report import ReportRequestParams, GeneratedReport, ReportFile
from app.core.use_cases.generate_dashboard_report_use_case import GenerateDashboardReportUseCase
# For dependency injection of use case (to be set up)
from app.infrastructure.adapters.mock_workplace_adapter import MockWorkplaceAdapter # Temporary direct use
from app.infrastructure.adapters.mock_report_adapter import MockReportAdapter   # Temporary direct use
from app.api.security import get_current_user_id_from_api_key # ADD THIS LINE

router = APIRouter()

# Helper function for default dates (matching Pydantic model defaults)
def default_start_date_param():
    return date.today() - timedelta(days=365)

def default_end_date_param():
    return date.today()

# Temporary direct instantiation of use case with mock adapters
# In a real app, this would use FastAPI's dependency injection system
# to provide port implementations.
def get_generate_dashboard_report_use_case():
    # This is a simplified DI for now.
    # Ideally, ports are bound to implementations elsewhere (e.g., in main.py or a container)
    workplace_port = MockWorkplaceAdapter()
    report_port = MockReportAdapter()
    return GenerateDashboardReportUseCase(workplace_port=workplace_port, report_port=report_port)


@router.get(
    "/dashboard/data/exporter",
    summary="Export dashboard data as a ZIP file",
    description="Generates selected reports for specified workplaces and period, then returns them as a ZIP archive.",
    response_description="A ZIP file containing the requested reports in CSV format."
    # In OpenAPI, explicitly defining response for zip might be tricky.
    # FastAPI will handle StreamingResponse correctly.
    # responses={200: {"content": {"application/zip": {}}}}, # This is more for OpenAPI spec
)
async def export_dashboard_data(
    request: Request, # To get user if auth is implemented via request state
    workplace_ids: Optional[str] = Query(None, description="Comma-separated workplace_ids. All accessible if not provided."),
    start_date: date = Query(default_factory=default_start_date_param, description="Start date (YYYY-MM-DD). Default: 1 year ago."),
    end_date: date = Query(default_factory=default_end_date_param, description="End date (YYYY-MM-DD). Default: today."),
    period: str = Query("month", description="Group data by: day, week, month, year. Default: month."),
    reports: str = Query(..., description="Comma-separated report keys to export (e.g., activity_summary,item_statistics)."),
    use_case: GenerateDashboardReportUseCase = Depends(get_generate_dashboard_report_use_case),
    current_user_id: str = Depends(get_current_user_id_from_api_key) # ADD THIS LINE
):
    parsed_workplace_ids = [wp_id.strip() for wp_id in workplace_ids.split(',')] if workplace_ids else []
    parsed_report_keys = [key.strip() for key in reports.split(',')]
    
    if not parsed_report_keys:
        raise HTTPException(status_code=400, detail="The 'reports' query parameter cannot be empty.")

    request_params = ReportRequestParams(
        workplace_ids=parsed_workplace_ids,
        start_date=start_date,
        end_date=end_date,
        period=period,
        reports=parsed_report_keys
    )

    # Placeholder for user ID - replace with actual auth if available
    # For now, using a mock user or None
    # mock_user_id = "user123" # Or extract from request.state.user if auth middleware sets it # REMOVE THIS
    
    generated_report_data: GeneratedReport = await use_case.execute(params=request_params, user_id=current_user_id) # USE current_user_id

    if not generated_report_data.files:
        # This case should ideally be handled by the use case returning specific error files
        # but as a fallback:
        raise HTTPException(status_code=404, detail="No data found for the requested reports or parameters.")

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for report_file_model in generated_report_data.files:
            file_content = report_file_model.content
            file_name = report_file_model.filename

            if report_file_model.content_type == "text/csv" and isinstance(file_content, list) and file_content:
                # Convert list of dicts to CSV string
                csv_io = io.StringIO()
                if isinstance(file_content[0], dict): # Ensure it's list of dicts
                    writer = csv.DictWriter(csv_io, fieldnames=file_content[0].keys())
                    writer.writeheader()
                    writer.writerows(file_content)
                else: # Fallback for simple list of strings or other non-dict list
                    writer = csv.writer(csv_io)
                    writer.writerows(file_content) # Assumes list of lists/tuples
                
                zip_file.writestr(file_name, csv_io.getvalue())
                csv_io.close()
            elif report_file_model.content_type == "text/plain" and isinstance(file_content, str):
                zip_file.writestr(file_name, file_content)
            else:
                # Fallback for other content types or if content is already bytes
                if isinstance(file_content, bytes):
                    zip_file.writestr(file_name, file_content)
                elif isinstance(file_content, str): # Default to encode string content
                    zip_file.writestr(file_name, file_content.encode('utf-8'))
                else:
                    # Skip or log unsupported content for zipping
                    print(f"Skipping file {file_name} due to unsupported content type for zipping.")


    zip_io.seek(0)
    
    # Define the filename for the downloaded zip file
    zip_filename = f"dashboard_export_{date.today().strftime('%Y%m%d')}.zip"
    
    return StreamingResponse(
        zip_io,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )
