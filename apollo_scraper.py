# apollo_scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.action_chains import ActionChains

import json
import time

class ApolloScraper:
    def __init__(self, cookies_file_path):
        self.cookies_file_path = cookies_file_path
        self.driver = None
        
    def setup_driver(self):
        firefox_options = Options()
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--headless") # Added for running in a server environment
        
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference('useAutomationExtension', False)
        firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0")
        
        try:
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            print("✅ GeckoDriver installed automatically with webdriver-manager")
        except Exception as e:
            print(f"Erreur avec webdriver-manager: {e}")
            raise Exception("Impossible d'initialiser GeckoDriver.")
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def load_cookies(self):
        try:
            with open(self.cookies_file_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            return cookies
        except FileNotFoundError:
            print(f"Erreur: Fichier de cookies '{self.cookies_file_path}' introuvable")
            return None
        except json.JSONDecodeError:
            print(f"Erreur: Format JSON invalide dans '{self.cookies_file_path}'")
            return None
    
    def set_cookies(self, cookies):
        for cookie in cookies:
            try:
                cookie_dict = {'name': cookie.get('name'), 'value': cookie.get('value'), 'domain': cookie.get('domain', '.apollo.io')}
                if 'path' in cookie: cookie_dict['path'] = cookie['path']
                if 'secure' in cookie: cookie_dict['secure'] = cookie['secure']
                if 'httpOnly' in cookie: cookie_dict['httpOnly'] = cookie['httpOnly']
                self.driver.add_cookie(cookie_dict)
            except Exception as e:
                print(f"Erreur lors de l'ajout du cookie {cookie.get('name', 'inconnu')}: {e}")
                continue
    
    # MODIFIED: Accepts a 'company_domain' parameter
    def scrape_apollo(self, company_domain: str):
        try:
            self.setup_driver()
            cookies = self.load_cookies()
            if not cookies:
                return None
            
            target_url = "https://app.apollo.io/#/people?page=1&organizationLocations[]=Paris%2C%20France&prospectedByCurrentTeam[]=no&sortAscending=false&sortByField=recommendations_score&personTitles[]=it%20manager"
            print(f"Navigation vers: {target_url}")
            self.driver.get(target_url)
            
            print("Chargement des cookies...")
            self.set_cookies(cookies)
            
            print("Rechargement de la page pour activer la session...")
            self.driver.refresh()
            
            wait = WebDriverWait(self.driver, 15)
            
            print("Clic sur le premier élément...")
            first_element_xpath = "/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div/div[2]/div[2]/div[1]/div/div/div[2]/div[5]/div"
            first_element = wait.until(EC.element_to_be_clickable((By.XPATH, first_element_xpath)))
            first_element.click()
            
            time.sleep(1)
            
            print("Clic sur le deuxième élément (le placeholder)...")
            placeholder_css = ".Select-placeholder"
            second_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, placeholder_css)))
            second_element.click()
            
            print(f"Envoi des touches pour le domaine: {company_domain}...")
            time.sleep(2)

            actions = ActionChains(self.driver)
            # MODIFIED: Uses the company_domain parameter here
            actions.send_keys(company_domain)
            actions.perform()
            time.sleep(5)
            print("send return ...")
            actions.send_keys(Keys.RETURN)
            actions.perform()            
            
            print("Attente de 10 secondes...")
            time.sleep(10)
            
            current_url = self.driver.current_url
            print(f"URL actuelle copiée: {current_url}")
            
            return current_url
            
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            screenshot_path = "screenshot.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            return None
        
        finally:
            if self.driver:
                self.driver.quit()

# This part is no longer needed for the API but can be kept for testing
if __name__ == "__main__":
    cookies_file = "apollo_cookies.json"
    scraper = ApolloScraper(cookies_file)
    result_url = scraper.scrape_apollo("suez.com") # Example call
    
    if result_url:
        print(f"\n✅ Scraping terminé avec succès!")
        print(f"URL finale: {result_url}")
    else:
        print("\n❌ Échec du scraping")