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
    
    def _initialize_driver_and_cookies(self):
        """Initializes the driver and sets cookies if not already done."""
        if self.driver is None:
            self.setup_driver()
            cookies = self.load_cookies()
            
            if cookies:
                self.driver.get("https://app.apollo.io")
                self.driver.maximize_window()
                self.driver.set_window_size(1920, 1080)
                self.set_cookies(cookies)
                self.driver.refresh()
            else:
                raise Exception("Cookies could not be loaded.")

    def scrape_apollo(self, company_domain: str):
        try:
            self._initialize_driver_and_cookies()
            
            target_url = "https://app.apollo.io/#/people?page=1&personTitles[]=it%20manager&personTitles[]=project%20manager&personTitles[]=talent%20acquisition&personTitles[]=rh&personTitles[]=senior&personTitles[]=developer&personTitles[]=ceo&personTitles[]=cto&personTitles[]=business%20manager&personTitles[]=ingenieur%20d%27affaires&prospectedByCurrentTeam[]=no&sortAscending=false&sortByField=recommendations_score&uniqueUrlId=4rhKtweaXd"
            print(f"Navigation vers: {target_url}")
            self.driver.get(target_url)
            self.driver.refresh()
            wait = WebDriverWait(self.driver, 5)
            
            print("Clic sur le premier élément...")
            first_element_xpath = "/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div/div[3]/div[2]/div[1]/div/div/div[2]/div[5]/div"
            first_element = wait.until(EC.element_to_be_clickable((By.XPATH, first_element_xpath)))
            first_element.click()
            
            # --- MODIFIÉ : Attente explicite pour le chargement du champ de recherche ---
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".Select-placeholder")))
            
            print("Clic sur le deuxième élément (le placeholder)...")
            placeholder_css = ".Select-placeholder"
            second_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, placeholder_css)))
            second_element.click()
            time.sleep(0.5)
            
            print(f"Envoi des touches pour le domaine: {company_domain}...")

            actions = ActionChains(self.driver)
            actions.send_keys(company_domain)
            actions.perform()
            
            # --- MODIFIÉ : Attente pour la suggestion de domaine avant d'appuyer sur Entrée ---
            time.sleep(3)
            print("send return ...")
            actions.send_keys(Keys.RETURN)
            actions.perform()            
            blocking_element_xpath = "/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div/div[3]/div[2]/div[2]/div/div/div/div/div/div"
            button_if_blocked_selector = "#main-container-column-2 > div > div > div > div.zp_p234g.people-finder-shell-container.people-finder-shell-empty-state-shown > div.zp_pxYrj > div.zp_FWOdG > div > div > div.zp_pDn5b.zp_T8qTB.zp_w3MDk > div:nth-child(4) > div.zp-accordion-header.zp_r3aQ1.zp_JoE0E > span > button"


            try:
                # On essaie de trouver directement la table de résultats
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table-row-0")))
            except:
                # Si la table n'est pas là, on vérifie si c'est à cause de l'élément bloquant
                blocking_elements = self.driver.find_elements(By.XPATH, blocking_element_xpath)

                if len(blocking_elements) > 0:
                    print("Élément bloquant détecté. Tentative de clic sur le bouton pour continuer...")
                    try:
                        button_to_click = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_if_blocked_selector)))
                        button_to_click.click()
                        print("Clic sur le bouton de contournement effectué. Attente du chargement des résultats...")
                        # On attend que la table apparaisse après le clic
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table-row-0")))
                    except Exception as e:
                        # Si le clic échoue, on lève une exception pour arrêter proprement
                        screenshot_path = f"screenshot_{time.time()}.png"
                        if self.driver:
                            self.driver.save_screenshot(screenshot_path)
                            print(f"Screenshot saved to {screenshot_path}")
                        raise Exception(f"Impossible de cliquer sur le bouton de contournement. Erreur: {e}")
                else:
                    # AMÉLIORATION : Si la table ET l'élément bloquant sont absents, on arrête.
                    print("ERREUR : La table de résultats est absente, et l'élément bloquant connu n'a pas été trouvé non plus.")
                    screenshot_path = f"screenshot_{time.time()}.png"
                    if self.driver:
                        self.driver.save_screenshot(screenshot_path)
                        print(f"Screenshot saved to {screenshot_path}")
                    raise Exception("État de la page inconnu, impossible de continuer le scraping.")

            
            # --- FIN DE LA NOUVELLE LOGIQUE ---


            # --- MODIFIÉ : Attente explicite du rechargement de la page après l'action ---
            
            

            # --- NOUVELLE LOGIQUE D'EXTRACTION AVEC PAGINATION ET JSON STRUCTURÉ ---
            print("Extraction des contacts de la page...")
            contacts = []
            CONTACT_LIMIT = 100
            
            while True:
                # Vérifier si la première ligne du tableau est présente
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table-row-0")))
                except:
                    print("Aucune ligne de résultats trouvée.")
                    break
                
                # Récupérer l'URL de la page actuelle pour l'inclure dans les données
                current_url = self.driver.current_url
                company1_XPATH = f"#table-row-0 > div:nth-child(3) > div > div > div > span > div > div > div > div.zp_PaniY > a > span"
                company2_XPATH = f"#table-row-1 > div:nth-child(3) > div > div > div > span > div > div > div > div.zp_PaniY > a > span"

                company1_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, company1_XPATH)))
                company2_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, company2_XPATH)))
                if company1_element.text != company2_element.text:
                    print("company1_element.text != company2_element.text")
                    screenshot_path = f"screenshot_{time.time()}.png"
                    if self.driver:
                        self.driver.save_screenshot(screenshot_path)
                        print(f"Screenshot saved to {screenshot_path}")
                    raise Exception("company1_element.text != company2_element.text")
                    
                    
                

                # Boucle pour itérer sur chaque ligne du tableau
                i = 0
                while True:
                    try:
                        # Construire les sélecteurs CSS pour le nom et le titre de poste
                        name_selector = f"#table-row-{i} > div.zp_biVWr.zp_wDB4y > div:nth-child(2) > div > div > a"
                        job_title_selector = f"#table-row-{i} > div:nth-child(2) > div > div > div.zp_YGDgt > span > span"
                        email_selector = f"#table-row-{i} > div:nth-child(4) > div > span > button"

                        # Attendre que les deux éléments soient présents et visibles
                        name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, name_selector)))
                        job_title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, job_title_selector)))
                        
                            
                        
                            
                        # Récupérer le lien associé au nom
                        name_link = name_element.get_attribute('href')

                        # Trouver le bouton de l'e-mail et vérifier son attribut
                        email_present = False
                        try:
                            email_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, email_selector)))
                            
                            # On vérifie la valeur de l'attribut data-tour-id
                            data_tour_id = email_button.get_attribute("data-tour-id")
                            
                            if data_tour_id == "email-cell-verified" or data_tour_id == "email-cell-unverified":
                                email_present = True
                            
                        except:
                            # Si le bouton n'est même pas présent, l'e-mail n'est pas vérifié
                            pass
                        
                        # Créer un dictionnaire pour le contact actuel
                        contact = {
                            "id": len(contacts),
                            "name": name_element.text,
                            "name_link": name_link,
                            "job_title": job_title_element.text,
                            "output_url": current_url,
                            "company_domain": company_domain,
                            "email_verified": email_present  # Utilisation d'un nom de champ plus précis

                        }
                        if email_present == True:
                            contacts.append(contact)
                        
                        
                        print(f"Extrait - ID: {contact['id']}, Nom: {contact['name']}, Titre: {contact['job_title']}, Email vérifié: {contact['email_verified']}")
                        i += 1
                    except:
                        # Si l'élément n'est pas trouvé, cela signifie
                        # que nous avons atteint la fin du tableau sur cette page
                        print(f"Fin de l'extraction de la page. {i} contacts trouvés.")
                        break
                if len(contacts) >= CONTACT_LIMIT:
                    print(f"Limite de {CONTACT_LIMIT} contacts atteinte. Arrêt de la pagination.")
                    break # Sort de la boucle externe (pagination)

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
            return contacts
            
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            screenshot_path = f"screenshot_{time.time()}.png"
            if self.driver:
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
            return None
    
    
    def get_people_by_name(self, name: str):
        """
        Recherche des personnes par nom et retourne les résultats sous forme de dictionnaire.
        """
        try:
            self._initialize_driver_and_cookies()
            time.sleep(2)
            self.driver.get(f"https://app.apollo.io/#/people?page=1&sortAscending=false&sortByField=recommendations_score&qKeywords={name.split(' ')[0]}%20{name.split(' ')[1]}")
            wait = WebDriverWait(self.driver, 15)
            people = []
            while True:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table-row-0")))
                except:
                    print("Aucune ligne de résultats trouvée.")
                    break
                i = 0
                while True:
                    try:
                        name_selector = f"#table-row-{i} > div.zp_biVWr.zp_wDB4y > div:nth-child(2) > div > div > a"
                        job_title_selector = f"#table-row-{i} > div:nth-child(2) > div > div > div.zp_YGDgt > span > span"
                        name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, name_selector)))
                        job_title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, job_title_selector)))
                        name_link = name_element.get_attribute('href')
                        person = {
                            "id": len(people),
                            "name": name_element.text,
                            "name_link": name_link,
                            "job_title": job_title_element.text
                        }
                        people.append(person)
                        print(f"Extrait - ID: {person['id']}, Nom: {person['name']}, Titre: {person['job_title']}")
                        i += 1
                    except:
                        print(f"Fin de l'extraction de la page. {i} personnes trouvées.")
                        break
            return people
        except Exception as e:
            screenshot_path = f"screenshot_{time.time()}.png"
            if self.driver:
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
            print(f"Erreur lors de la recherche par nom: {e}")
            raise e

    def get_email(self, profile_url: str):
        """
        Navigue vers une URL de profil et tente d'extraire l'adresse e-mail.
        """
        try:
            self._initialize_driver_and_cookies()
            self.driver.get(profile_url)
            self.driver.refresh()
            wait = WebDriverWait(self.driver, 7)

            print(f"Navigating to profile URL: {profile_url}")
            

            # Clic sur le bouton pour révéler l'e-mail
            try:
                email_button_xpath = '/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/div[1]/div[1]/div/div[2]/div/div/div[1]/div[2]/div[1]/div[2]/button'
                email_button = wait.until(EC.presence_of_element_located((By.XPATH, email_button_xpath)))
                email_button.click()
                time.sleep(1) # Attendre que l'e-mail apparai2sse

            except Exception:
                # Extraire l'adresse e-mail
                try:

                    print("Bouton non trouvé, on extrait l'e-mail directement")
                    email_selector = "/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/div/div[2]/div[1]/div[1]/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div/div[1]/div/div/div[2]/div/div/div[1]/div/div/div/div/div/div[1]/a"
                    email_element = wait.until(EC.presence_of_element_located((By.XPATH, email_selector)))
                    email = email_element.text
                    print(f"✅ E-mail extrait: {email}")
                    return {"status": "success", "email": email}

                except Exception as e:

                    print(f"Erreur lors de l'extraction de l'e-mail: {e}")
                    # --- NOUVEAU: Capture d'écran pour le débogage ---2
                    screenshot_path = f"email_error_screenshot_{time.time()}.png"
                    if self.driver:
                        self.driver.save_screenshot(screenshot_path)
                        print(f"Screenshot saved to {screenshot_path}")
                        
                    raise e



            # Extraire l'adresse e-mail
            email_selector = "/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/div/div[2]/div[1]/div[1]/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div/div[1]/div/div/div[2]/div/div/div[1]/div/div/div/div/div/div[1]/a"
            email_element = wait.until(EC.presence_of_element_located((By.XPATH, email_selector)))
            email = email_element.text
            
            print(f"✅ E-mail extrait: {email}")
            return {"status": "success", "email": email}

        except Exception as e:
            print(f"Erreur lors de l'extraction de l'e-mail: {e}")
            
            # --- NOUVEAU: Capture d'écran pour le débogage ---
            screenshot_path = f"email_error_screenshot_{time.time()}.png"
            if self.driver:
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
                
            raise e


    def quit_driver(self):
        """Quits the WebDriver instance."""
        if self.driver:
            self.driver.quit()
            self.driver = None


if __name__ == "__main__":
    cookies_file = "apollo_cookies.json"
    scraper = ApolloScraper(cookies_file)
    
    print("Choisissez une action :")
    print("1) Scraper des contacts (scrape_apollo)")
    print("2) Récupérer un e-mail (get_email)")
    print("3) Récupérer des personnes par nom (get_people_by_name)")
    choice = input("Entrez 1, 2 ou 3: ").strip()

    if choice == "1":
        domain = input("Entrez le domaine de l'entreprise (ex: example.com): ").strip()
        if domain:
            result_contacts = scraper.scrape_apollo(domain)
            if result_contacts:
                print("\n✅ Scraping terminé avec succès!")
                print("\nListe des contacts:")
                print(json.dumps(result_contacts, indent=2))
            else:
                print("\n❌ Aucun contact trouvé ou erreur lors du scraping.")
        else:
            print("\n❌ Domaine invalide.")
    elif choice == "2":
        profile_url = "https://app.apollo.io/#/people/6724c639258ded000196ec08?overrideScoreId=score"
        if profile_url:
            email_result = scraper.get_email(profile_url)
            print(json.dumps(email_result, indent=2))
        else:
            print("\n❌ URL de profil invalide.")
    elif choice == "3":
        name = input("Entrez le nom de la personne (ex: John Doe): ").strip()
        if name:
            people_result = scraper.get_people_by_name(name)
            print(json.dumps(people_result, indent=2))
        else:
            print("\n❌ Nom invalide.")
    else:
        print("\n❌ Choix invalide. Veuillez relancer et entrer 1 ou 2.")
    
    scraper.quit_driver()
