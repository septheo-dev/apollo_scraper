# Apollo Scraper (FastAPI + Selenium)

This project provides a Selenium-based scraper for Apollo.io with a simple FastAPI API and an optional CLI. It uses a persisted Apollo session (cookies) to access search results and extract contacts and emails.

## Features

- **Selenium + Firefox (GeckoDriver)** automation
- **Cookie-based session** (no credentials in code)
- **Endpoints**:
  - `POST /scrape` — scrape contacts for a given `company_domain`
  - `POST /get_email` — extract an email from an Apollo profile URL
- **CLI** entry points in `apollo_scraper.py` for manual runs
- **Docker/Docker Compose** for containerized deployment

## Requirements

- Python 3.10+
- Firefox (locally) and GeckoDriver. In Docker, Firefox and GeckoDriver are installed automatically.
- A valid Apollo session cookies file: `apollo_cookies.json` at the project root.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Cookies Setup

Place your Apollo session cookies in `apollo_cookies.json` at the project root. The scraper loads this file and injects cookies into the browser session.

Expected format: the JSON exported from your browser cookie manager (array of cookie objects containing at least `name`, `value`, and typically `domain`, `path`, etc.).

- If the file is missing or not valid JSON, the scraper will abort with a clear error message.
- The scraper navigates to `https://app.apollo.io`, sets cookies, and refreshes to authenticate.

## Running the API (FastAPI)

Start the API locally:

```bash
uvicorn app:app --reload --port 8000
```

### Endpoints

- POST `/scrape`
  - Body:
    ```json
    { "company_domain": "example.com" }
    ```
  - Response:
    ```json
    {
      "status": "success",
      "contacts": [
        {
          "id": 0,
          "name": "Jane Doe",
          "name_link": "https://app.apollo.io/#/people/...",
          "job_title": "CTO",
          "output_url": "https://app.apollo.io/#/people?page=1...",
          "company_domain": "example.com",
          "email_verified": true
        }
      ]
    }
    ```

- POST `/get_email`
  - Body:
    ```json
    { "profile_url": "https://app.apollo.io/#/people/...." }
    ```
  - Response:
    ```json
    { "status": "success", "email": "jane@company.com" }
    ```

On application shutdown, the WebDriver is closed automatically.

## CLI Usage

You can also run the scraper directly:

```bash
python apollo_scraper.py
```

Menu options:
- `1` Scrape contacts for a domain (prompts for `example.com`)
- `2` Get email from a profile URL (uses a sample URL unless edited)
- `3` Get people by name (prompts for `First Last`)

Outputs are printed to stdout (JSON) and screenshots are saved on errors.

## Docker

A production-friendly container is provided. It installs Firefox and GeckoDriver and runs the FastAPI app.

Build and run with Docker:

```bash
docker build -t apollo-scraper .
docker run --rm -p 8000:8000 \
  -v $(pwd)/apollo_cookies.json:/app/apollo_cookies.json:ro \
  --name apollo-scraper apollo-scraper
```

Or use docker-compose:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

## Notes / Troubleshooting

- The scraper uses many CSS/XPath selectors that may change if Apollo updates its UI. If elements are not found, the script saves a screenshot (e.g., `screenshot_<timestamp>.png`) for debugging.
- If you see `StaleElementReferenceException` or timeouts, Apollo likely re-rendered the DOM; the code includes waits and retries, but page timing can vary.
- For headless environments, the Firefox options are configured automatically. Locally, ensure Firefox is installed if not using Docker.

## Project Structure

- `apollo_scraper.py` — Selenium scraper class and CLI
- `app.py` — FastAPI app exposing endpoints
- `Dockerfile` — Container image with Firefox + GeckoDriver
- `docker-compose.yml` — Simple compose service exposing port 8000
- `requirements.txt` — Python dependencies
- `apollo_cookies.json` — Your exported Apollo session cookies (not committed)
