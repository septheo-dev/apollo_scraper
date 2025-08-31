# app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apollo_scraper import ApolloScraper # Import our class

# Initialize the FastAPI app
app = FastAPI()

# Define the request data model using Pydantic for validation
class ScrapeRequest(BaseModel):
    company_domain: str

# Define the POST endpoint at /scrape
@app.post("/scrape")
async def scrape_domain(request: ScrapeRequest):
    """
    This endpoint receives a company domain, scrapes Apollo.io,
    and returns the resulting URL.
    """
    print(f"Received request to scrape for domain: {request.company_domain}")
    
    # Path to your cookies file inside the Docker container
    cookies_file = "apollo_cookies.json"
    
    scraper = ApolloScraper(cookies_file)
    
    try:
        # Call the scraper method with the domain from the request
        result_url = scraper.scrape_apollo(request.company_domain)
        
        if result_url:
            print(f"Successfully scraped. URL: {result_url}")
            return {"status": "success", "url": result_url}
        else:
            print("Scraping failed, scraper returned None.")
            raise HTTPException(status_code=500, detail="Scraping failed. Check the API logs for more details.")
            
    except Exception as e:
        print(f"An exception occurred during scraping: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")