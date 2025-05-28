from typing import List, Optional, Dict, Any
from app.core.models.report import ReportRequestParams, GeneratedReport, ReportFile
from app.core.models.workplace import Workplace
from app.core.ports.workplace_port import WorkplacePort
from app.core.ports.report_port import ReportPort
import logging # For logging

logger = logging.getLogger(__name__)

class GenerateDashboardReportUseCase:
    def __init__(self, workplace_port: WorkplacePort, report_port: ReportPort):
        self.workplace_port = workplace_port
        self.report_port = report_port

    async def execute(self, params: ReportRequestParams, user_id: Optional[str] = None) -> GeneratedReport:
        logger.info(f"Executing GenerateDashboardReportUseCase for user '{user_id}' with params: {params}")

        accessible_workplaces: List[Workplace] = await self.workplace_port.get_accessible_workplaces(user_id)
        accessible_workplace_ids: List[str] = [wp.id for wp in accessible_workplaces]

        # Filter requested workplace_ids against accessible ones
        # If no workplace_ids are requested in params, use all accessible ones.
        if params.workplace_ids:
            # User requested specific workplaces, check if they have access
            requested_and_accessible_ids = []
            for req_id in params.workplace_ids:
                if req_id not in accessible_workplace_ids:
                    logger.warning(f"User '{user_id}' requested workplace_id '{req_id}' but does not have access. Skipping.")
                else:
                    requested_and_accessible_ids.append(req_id)
            
            if not requested_and_accessible_ids:
                logger.warning(f"User '{user_id}' has no access to any of the specifically requested workplace_ids: {params.workplace_ids}. Returning empty report.")
                return GeneratedReport(files=[])
            
            # Update params to only include workplaces they have access to AND requested
            final_workplace_ids_for_report = requested_and_accessible_ids
        else:
            # No specific workplaces requested, use all accessible ones
            if not accessible_workplace_ids:
                logger.warning(f"User '{user_id}' has no accessible workplaces. Returning empty report.")
                return GeneratedReport(files=[])
            final_workplace_ids_for_report = accessible_workplace_ids

        # Update params with the filtered list of workplace_ids to be used in report generation
        # This ensures the report_port only receives IDs the user is authorized for and requested (if any)
        # or all accessible if none were specified.
        params_for_adapter = params.copy(update={"workplace_ids": final_workplace_ids_for_report})

        report_files: List[ReportFile] = []

        for report_key in params.reports:
            logger.info(f"Generating data for report key: '{report_key}' with effective workplace_ids: {final_workplace_ids_for_report}")
            try:
                # Data generation is now based on filtered workplace_ids in params_for_adapter
                data_content: Any = await self.report_port.generate_report_data(
                    report_key=report_key,
                    params=params_for_adapter 
                )
                
                if data_content:
                    # Determine filename, e.g., based on report_key and period
                    filename = f"{report_key}_{params.period}_{params.start_date}_to_{params.end_date}.csv"
                    report_files.append(
                        ReportFile(
                            filename=filename,
                            content=data_content, # This will be List[Dict] from mock adapter
                            content_type="text/csv" # Assuming CSV for now
                        )
                    )
                    logger.info(f"Successfully generated data for report key: '{report_key}'")
                else:
                    logger.warning(f"No data returned for report key: '{report_key}'")
                    # Optionally add a file indicating no data, or just skip
                    report_files.append(
                        ReportFile(
                            filename=f"{report_key}_no_data.txt",
                            content=f"No data found for report '{report_key}' with the given parameters.",
                            content_type="text/plain"
                        )
                    )

            except Exception as e:
                logger.error(f"Error generating report for key '{report_key}': {e}", exc_info=True)
                # Add a file indicating error for this specific report
                report_files.append(
                    ReportFile(
                        filename=f"{report_key}_error.txt",
                        content=f"An error occurred while generating report '{report_key}': {str(e)}",
                        content_type="text/plain"
                    )
                )
        
        logger.info(f"Report generation complete. {len(report_files)} file(s) prepared.")
        return GeneratedReport(files=report_files)
