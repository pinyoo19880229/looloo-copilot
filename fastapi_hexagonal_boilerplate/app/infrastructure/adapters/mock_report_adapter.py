from typing import Any, List, Dict
from app.core.models.report import ReportRequestParams
from app.core.ports.report_port import ReportPort
from datetime import timedelta, datetime

class MockReportAdapter(ReportPort):
    """
    Mock implementation of the ReportPort.
    Simulates generating report data.
    """

    async def generate_report_data(
        self, 
        report_key: str,
        params: ReportRequestParams,
        # accessible_workplace_ids: List[str] # Use this if filtering by workplace is done here
    ) -> Any: # Return type could be List[Dict] for CSV conversion
        
        # Simulate data generation based on report_key and params
        # This data would typically come from database queries and processing
        
        report_data = []
        # Generate some time-series data for the example
        current_date = params.start_date
        while current_date <= params.end_date:
            for wp_id in params.workplace_ids or ["all_mocked"]: # Use provided or a default
                if report_key == "activity_summary":
                    report_data.append({
                        "date": current_date.isoformat(),
                        "workplace_id": wp_id,
                        "visits": 100 + (current_date.day % 10) * 10, # Some variance
                        "new_memberships": 5 + (current_date.day % 5),
                    })
                elif report_key == "item_statistics":
                    report_data.append({
                        "date": current_date.isoformat(),
                        "workplace_id": wp_id,
                        "items_loaned": 500 + (current_date.day % 20) * 5,
                        "items_returned": 480 + (current_date.day % 20) * 4,
                    })
                elif report_key == "financial_overview":
                     report_data.append({
                        "date": current_date.isoformat(),
                        "workplace_id": wp_id,
                        "revenue_books_usd": 1000.00 + (current_date.day % 10) * 100,
                        "revenue_events_usd": 200.00 + (current_date.day % 5) * 20,
                        "late_fees_usd": 50.00 + (current_date.day % 7) * 5,
                    })


            # Increment date based on period (simplified for mock)
            if params.period == "day":
                current_date += timedelta(days=1)
            elif params.period == "week":
                current_date += timedelta(weeks=1)
            elif params.period == "month":
                # This is a simplification; real month increment is more complex
                current_date += timedelta(days=30) 
            elif params.period == "year":
                current_date += timedelta(days=365)
            else: # Default to month if period is unknown
                current_date += timedelta(days=30)
            
            # Ensure we don't overshoot end_date significantly in loops
            if params.period != "day" and current_date > params.end_date and len(report_data)>0 :
                # If we jumped past end_date with a large step (week/month/year)
                # and generated at least one entry, break.
                # Or adjust last entry's date to end_date. For mock, this is fine.
                break


        if not report_data:
            return [{"message": f"No data found or report key '{report_key}' not recognized for the given parameters."}]
        
        return report_data # Typically a list of dicts, where each dict is a row for a CSV
