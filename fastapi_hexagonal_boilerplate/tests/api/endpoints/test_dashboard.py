import pytest
from httpx import AsyncClient
from fastapi import status
import zipfile
import io
from datetime import date, timedelta

from app.main import app # Import your FastAPI app instance
from app.api.security import VALID_API_KEY # To use the valid API key in tests

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Fixture for the async client
@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Fixture for common valid API key header
@pytest.fixture(scope="module")
def valid_headers():
    return {"X-API-KEY": VALID_API_KEY}

async def test_export_dashboard_data_success(client: AsyncClient, valid_headers):
    """Test successful data export with valid parameters."""
    start_date = (date.today() - timedelta(days=10)).isoformat()
    end_date = date.today().isoformat()
    
    response = await client.get(
        f"/api/v1/dashboard/data/exporter?workplace_ids=wp1,wp2&start_date={start_date}&end_date={end_date}&period=day&reports=activity_summary,item_statistics",
        headers=valid_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"
    assert "attachment; filename=" in response.headers["content-disposition"]

    # Check zip content (basic)
    zip_io = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_io, mode="r") as zip_ref:
        filenames_in_zip = zip_ref.namelist()
        assert f"activity_summary_day_{start_date}_to_{end_date}.csv" in filenames_in_zip
        assert f"item_statistics_day_{start_date}_to_{end_date}.csv" in filenames_in_zip
        
        # Optionally, check content of a CSV
        # with zip_ref.open(f"activity_summary_day_{start_date}_to_{end_date}.csv") as csv_file:
        #     csv_content = csv_file.read().decode('utf-8')
        #     assert "date,workplace_id,visits,new_memberships" in csv_content # Check header

async def test_export_dashboard_data_default_dates_and_period(client: AsyncClient, valid_headers):
    """Test with default dates and period."""
    today = date.today()
    year_ago = today - timedelta(days=365)
    
    response = await client.get(
        "/api/v1/dashboard/data/exporter?reports=activity_summary",
        headers=valid_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"
    
    zip_io = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_io, mode="r") as zip_ref:
        filenames_in_zip = zip_ref.namelist()
        # Default period is month
        assert f"activity_summary_month_{year_ago.isoformat()}_to_{today.isoformat()}.csv" in filenames_in_zip


async def test_export_dashboard_no_reports_param(client: AsyncClient, valid_headers):
    """Test request without the mandatory 'reports' parameter."""
    # FastAPI's Query(..., description="...") makes it required by default.
    # If it's truly optional with a default, this test would change.
    # The current implementation has `reports: str = Query(...)` which means it's required.
    response = await client.get(
        "/api/v1/dashboard/data/exporter?workplace_ids=wp1",
        headers=valid_headers
    )
    # Expecting a 422 Unprocessable Entity if a required query param is missing
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 

async def test_export_dashboard_empty_reports_string(client: AsyncClient, valid_headers):
    """Test request with an empty 'reports' string (which is invalid)."""
    response = await client.get(
        "/api/v1/dashboard/data/exporter?reports=", 
        headers=valid_headers
    )
    # Our endpoint code has: if not parsed_report_keys: raise HTTPException(400)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "reports' query parameter cannot be empty" in response.json()["detail"]


async def test_export_dashboard_no_api_key(client: AsyncClient):
    """Test request without API key."""
    response = await client.get(
        "/api/v1/dashboard/data/exporter?reports=activity_summary"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or missing API Key" in response.json()["detail"]


async def test_export_dashboard_invalid_api_key(client: AsyncClient):
    """Test request with an invalid API key."""
    response = await client.get(
        "/api/v1/dashboard/data/exporter?reports=activity_summary",
        headers={"X-API-KEY": "this_is_a_wrong_key"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or missing API Key" in response.json()["detail"]

async def test_export_dashboard_inaccessible_workplace(client: AsyncClient, valid_headers):
    """
    Test requesting a workplace the mock user 'user_from_api_key_abc123' might not have access to,
    or a non-existent one. The use case should filter this out.
    The current mock user 'user_from_api_key_abc123' is not in USER_ACCESS_DB in mock_workplace_adapter.
    So it gets the default list (wp1, wp2, wp3). Requesting 'wp4' (restricted) should result in it being ignored.
    If all requested workplaces are inaccessible, the use case returns an empty GeneratedReport.
    The endpoint then raises a 404.
    """
    response = await client.get(
        "/api/v1/dashboard/data/exporter?workplace_ids=wp4&reports=activity_summary", # wp4 is restricted
        headers=valid_headers
    )
    # The use case returns an empty GeneratedReport(files=[])
    # The endpoint then raises: HTTPException(status_code=404, detail="No data found...")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No data found" in response.json()["detail"]

async def test_export_dashboard_no_workplace_ids_uses_accessible(client: AsyncClient, valid_headers):
    """
    Test that if no workplace_ids are provided, it defaults to accessible ones for the user.
    Mock user 'user_from_api_key_abc123' (via VALID_API_KEY) is not in USER_ACCESS_DB,
    so MockWorkplaceAdapter's get_accessible_workplaces returns [wp1, wp2, wp3].
    The report should contain data related to these.
    """
    today = date.today()
    year_ago = today - timedelta(days=365)
    response = await client.get(
        "/api/v1/dashboard/data/exporter?reports=activity_summary", # No workplace_ids
        headers=valid_headers
    )
    assert response.status_code == status.HTTP_200_OK
    zip_io = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_io, mode="r") as zip_ref:
        filenames_in_zip = zip_ref.namelist()
        # Check if the file corresponding to default behavior is present
        assert f"activity_summary_month_{year_ago.isoformat()}_to_{today.isoformat()}.csv" in filenames_in_zip
        # Further check: the CSV should contain data for wp1, wp2, wp3
        # For example, open and read some lines from the CSV.
        # This part can be more detailed if needed.
        # with zip_ref.open(f"activity_summary_month_{year_ago.isoformat()}_to_{today.isoformat()}.csv") as csv_file:
        #     content = csv_file.read().decode()
        #     assert "wp1" in content and "wp2" in content and "wp3" in content
        #     assert "wp4" not in content # Ensure restricted one isn't there by default
