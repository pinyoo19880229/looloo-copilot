# FastAPI Hexagonal Boilerplate & Library Data Exporter

This project provides a boilerplate for FastAPI applications using Hexagonal Architecture (Ports and Adapters) and includes a data exporter API for a conceptual library system.

## Architecture

The project follows the principles of Hexagonal Architecture to promote separation of concerns, making the core domain logic independent of infrastructure details (like web frameworks, databases, etc.).

-   **`app/core`**: Contains the domain models, ports (interfaces), and use cases (application logic).
-   **`app/api`**: Handles HTTP request/response specifics, routing, and request/response models using FastAPI.
-   **`app/infrastructure`**: Provides concrete implementations (adapters) for the ports defined in the core. This includes database access, external service integrations, etc. For the data exporter, mock adapters are currently used.

## Features

-   FastAPI backend framework.
-   Hexagonal Architecture foundation.
-   **Data Exporter API**: Secure endpoint to export library system data as a ZIP file.
-   Ruff for linting and code formatting.
-   Docker and Docker Compose support for containerization.
-   GitHub Actions CI for automated checks.
-   Rate Limiting on public-facing endpoints (e.g., Home).
-   Conceptual Circuit Breaker pattern example.
-   Basic API Key authentication for secure endpoints.
-   Unit and Integration tests using Pytest.

## Prerequisites

-   Python 3.9+
-   Poetry (for dependency management)
-   Docker (for running with Docker)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd fastapi_hexagonal_boilerplate
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

3.  **Set up Environment Variables:**
    The application uses an API key for the `/dashboard/data/exporter` endpoint. You can set it via an environment variable. Create a `.env` file in the project root (it's in `.gitignore`):
    ```env
    SERVER_API_KEY="your_chosen_strong_api_key" 
    ```
    If not set, a default key "your_secret_api_key_here" will be used (not recommended for production).

## Running the Application

### Locally with Uvicorn

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`.

### With Docker Compose

This is useful for a containerized setup.

```bash
docker-compose up --build
```
The API will be available at `http://localhost:8000`.

## Running Tests

Tests are written using Pytest.

```bash
poetry run pytest
```

## API Endpoints

### Health Check

-   **GET** `/health`
-   **Description:** Returns the health status of the application.
-   **Authentication:** None.
-   **Response:** `{"status": "healthy"}`

### Home

-   **GET** `/`
-   **Description:** Simple welcome endpoint.
-   **Authentication:** None.
-   **Rate Limit:** Yes (e.g., 10/minute).
-   **Response:** `{"message": "Hello World"}`

### Dashboard Data Exporter

-   **GET** `/api/v1/dashboard/data/exporter`
-   **Description:** Exports specified reports for given workplaces and time period as a ZIP archive. Each report is a CSV file within the archive.
-   **Authentication:** Required. Provide an API key via the `X-API-KEY` header.
    -   Set the valid key using the `SERVER_API_KEY` environment variable.
-   **Query Parameters:**
    -   `workplace_ids` (string, optional): Comma-separated list of workplace IDs to filter by (e.g., `wp1,wp2`). If omitted, data for all workplaces accessible to the authenticated user will be included.
    -   `start_date` (string, YYYY-MM-DD, optional): The start date for the report data. Defaults to 365 days ago from the current date.
    -   `end_date` (string, YYYY-MM-DD, optional): The end date for the report data. Defaults to the current date.
    -   `period` (string, optional): The time period to group data by.
        -   Allowed values: `day`, `week`, `month`, `year`.
        -   Default: `month`.
    -   `reports` (string, required): Comma-separated list of report keys to include in the export.
        -   Example mock keys: `activity_summary`, `item_statistics`, `financial_overview`.
-   **Example Request (using curl):**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/dashboard/data/exporter?workplace_ids=wp1&reports=activity_summary,item_statistics&start_date=2023-01-01&end_date=2023-12-31" \
         -H "X-API-KEY: your_chosen_strong_api_key" \
         --output report_export.zip
    ```
-   **Success Response:**
    -   Status Code: `200 OK`
    -   Content-Type: `application/zip`
    -   Body: A ZIP file containing CSVs for each requested report. Error files (as .txt) might be included if specific reports fail or have no data.

## Code Formatting and Linting

This project uses Ruff for extremely fast Python linting and formatting.

-   **Check formatting and lint issues:**
    ```bash
    poetry run ruff check .
    ```
-   **Apply formatting:**
    ```bash
    poetry run ruff format .
    ```
The CI pipeline also runs these checks.
