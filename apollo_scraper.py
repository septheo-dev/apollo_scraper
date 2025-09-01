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
        #firefox_options.add_argument("--headless") # Added for running in a server environment
        
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
            
            target_url = "https://app.apollo.io/#/people?page=1&personTitles[]=it%20manager&personLocations[]=Paris%2C%20France&prospectedByCurrentTeam[]=no&sortAscending=false&sortByField=recommendations_score"
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
            time.sleep(3)
            print("send return ...")
            actions.send_keys(Keys.RETURN)
            actions.perform()            
            
            print("Attente de 2 secondes...")
            time.sleep(2)


            # --- NOUVELLE LOGIQUE D'EXTRACTION AVEC PAGINATION ET JSON STRUCTURÉ ---
            print("Extraction des contacts de la page...")
            contacts = []
            
            while True:
                # Vérifier si la première ligne du tableau est présente
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table-row-0")))
                except:
                    print("Aucune ligne de résultats trouvée.")
                    break
                
                # Récupérer l'URL de la page actuelle pour l'inclure dans les données
                current_url = self.driver.current_url

                # Boucle pour itérer sur chaque ligne du tableau
                i = 0
                while True:
                    try:
                        # Construire les sélecteurs CSS pour le nom et le titre de poste
                        name_selector = f"#table-row-{i} > div.zp_biVWr.zp_wDB4y > div:nth-child(2) > div > div > a"
                        job_title_selector = f"#table-row-{i} > div:nth-child(2) > div > div > div.zp_YGDgt > span > span"

                        # Attendre que les deux éléments soient présents et visibles
                        name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, name_selector)))
                        job_title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, job_title_selector)))
                        
                        # Récupérer le lien associé au nom
                        name_link = name_element.get_attribute('href')
                        
                        # Créer un dictionnaire pour le contact actuel
                        contact = {
                            "id": len(contacts),
                            "name": name_element.text,
                            "name_link": name_link,
                            "job_title": job_title_element.text,
                            #"output_url": current_url,
                            "company_domain": company_domain
                        }
                        contacts.append(contact)
                        
                        print(f"Extrait - ID: {contact['id']}, Nom: {contact['name']}, Titre: {contact['job_title']}")
                        i += 1
                    except:
                        # Si l'élément n'est pas trouvé, cela signifie
                        # que nous avons atteint la fin du tableau sur cette page
                        print(f"Fin de l'extraction de la page. {i} contacts trouvés.")
                        break

                # Vérifier s'il y a 25 contacts sur la page (indice 0 à 24)
                if i < 25:
                    print("Moins de 25 contacts sur la page. Fin de la pagination.")
                    break
                
                # Clic sur le bouton "next"
                try:
                    next_button_selector = "#main-container-column-2 > div > div > div > div.zp_p234g.people-finder-shell-container > div.zp_pxYrj > div.zp_lYmVV > div.zp_DhjQ0.zp_a7xaB > div > div.zp_l0qux > button:nth-child(4)"
                    next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector)))
                    next_button.click()
                    print("Clic sur le bouton 'Suivant'. Attente du chargement de la nouvelle page.")
                    time.sleep(3) # Laisser le temps à la page de charger
                except:
                    print("Bouton 'Suivant' non trouvé ou non cliquable. Fin de la pagination.")
                    break


            print(f"✅ {len(contacts)} contacts extraits au total.")
                        
            # Le retour final est une liste des contacts extraits
            return contacts
            
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
    result = scraper.scrape_apollo("suez.com") # Exemple d'appel
    
    if result:
        print(f"\n✅ Scraping terminé avec succès!")
        print(f"\nListe des contacts:")
        # Utiliser un dictionnaire pour un affichage plus lisible si le résultat est une liste d'objets
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ Échec du scraping")
