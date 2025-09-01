# app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apollo_scraper import ApolloScraper

# Initialize the FastAPI app
app = FastAPI()

# Global scraper instance. It will be initialized once.
# This avoids creating a new WebDriver for each request, which is very slow.
scraper = ApolloScraper("apollo_cookies.json")

# Define the request data models
class ScrapeRequest(BaseModel):
    company_domain: str

class EmailRequest(BaseModel):
    profile_url: str

@app.post("/scrape")
async def scrape_domain(request: ScrapeRequest):
    """
    This endpoint receives a company domain, scrapes Apollo.io,
    and returns the resulting contacts.
    """
    print(f"Received request to scrape for domain: {request.company_domain}")
    
    try:
        result_contacts = scraper.scrape_apollo(request.company_domain)
        
        if result_contacts is not None:
            print(f"Successfully scraped. Found {len(result_contacts)} contacts.")
            return {"status": "success", "contacts": result_contacts}
        else:
            print("Scraping failed, scraper returned None.")
            raise HTTPException(status_code=500, detail="Scraping failed. Check the API logs for more details.")
            
    except Exception as e:
        print(f"An exception occurred during scraping: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

@app.post("/get_email")
async def get_email_from_profile(request: EmailRequest):
    """
    This endpoint receives a profile URL, scrapes the email,
    and returns it.
    """
    print(f"Received request to get email for profile URL: {request.profile_url}")
    
    try:
        email_result = scraper.get_email(request.profile_url)
        return email_result
    except Exception as e:
        print(f"An exception occurred during email scraping: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

# This part ensures the driver is closed properly on shutdown
@app.on_event("shutdown")
def shutdown_event():
    scraper.quit_driver()
    print("Application shutdown. WebDriver closed.")
