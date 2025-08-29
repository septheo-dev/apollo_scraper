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
        """
        Initialise le scraper Apollo.io
        
        Args:
            cookies_file_path (str): Chemin vers le fichier JSON contenant les cookies
        """
        self.cookies_file_path = cookies_file_path
        self.driver = None
        
    def setup_driver(self):
        """Configure et initialise le driver Firefox avec gestion automatique de GeckoDriver"""
        firefox_options = Options()
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        
        # Options pour éviter la détection
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference('useAutomationExtension', False)
        firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0")
        
        try:
            # Utiliser webdriver-manager pour télécharger automatiquement la bonne version de GeckoDriver
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            print("✅ GeckoDriver installé automatiquement avec webdriver-manager")
        except Exception as e:
            print(f"Erreur avec webdriver-manager: {e}")
            print("Tentative d'utilisation du GeckoDriver système...")
            try:
                # Fallback vers le GeckoDriver système
                self.driver = webdriver.Firefox(options=firefox_options)
            except Exception as e2:
                print(f"Erreur avec GeckoDriver système: {e2}")
                raise Exception("Impossible d'initialiser GeckoDriver. Assurez-vous que Firefox est installé.")
        
        # Script pour masquer les traces d'automatisation
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def load_cookies(self):
        """Charge les cookies depuis le fichier JSON"""
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
    
    # MODIFIÉ : La méthode se contente maintenant d'ajouter les cookies sans naviguer.
    def set_cookies(self, cookies):
        """Applique les cookies au navigateur pour le domaine actuel"""
        for cookie in cookies:
            try:
                # Nettoyer le cookie pour Selenium
                cookie_dict = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain', '.apollo.io'),
                }
                
                # Ajouter les champs optionnels s'ils existent
                if 'path' in cookie:
                    cookie_dict['path'] = cookie['path']
                if 'secure' in cookie:
                    cookie_dict['secure'] = cookie['secure']
                if 'httpOnly' in cookie:
                    cookie_dict['httpOnly'] = cookie['httpOnly']
                
                self.driver.add_cookie(cookie_dict)
            except Exception as e:
                print(f"Erreur lors de l'ajout du cookie {cookie.get('name', 'inconnu')}: {e}")
                continue
    
    def scrape_apollo(self):
        """Fonction principale de scraping"""
        try:
            # Configuration du driver
            self.setup_driver()
            
            # Chargement des cookies depuis le fichier
            cookies = self.load_cookies()
            if not cookies:
                return None
            
            # MODIFIÉ : Réorganisation de la logique de connexion
            # 1. Navigation initiale vers l'URL cible pour être sur le bon domaine
            target_url = "https://app.apollo.io/#/people?page=1&organizationLocations[]=Paris%2C%20France&prospectedByCurrentTeam[]=no&sortAscending=false&sortByField=recommendations_score&personTitles[]=it%20manager"
            print(f"Navigation vers: {target_url}")
            self.driver.get(target_url)
            
            # 2. Ajout des cookies dans le contexte du navigateur
            print("Chargement des cookies...")
            self.set_cookies(cookies)
            
            # 3. Rechargement de la page. Le navigateur va maintenant utiliser les cookies pour s'authentifier.
            print("Rechargement de la page pour activer la session...")
            self.driver.refresh()

            # MODIFIÉ : Ajout d'une pause attendant une action de l'utilisateur
            #input("La page est chargée. Appuyez sur Entrée dans ce terminal pour continuer le script...")

            
            # Attendre que la page se charge après le rechargement
            wait = WebDriverWait(self.driver, 15)
            
            # Cliquer sur le premier élément
            print("Clic sur le premier élément...")
            first_element_xpath = "/html/body/div[2]/div/div[2]/div[2]/div/div[2]/div/div[2]/div/div/div/div/div[2]/div[2]/div[1]/div/div/div[2]/div[5]/div"
            first_element = wait.until(EC.element_to_be_clickable((By.XPATH, first_element_xpath)))
            first_element.click()
            
            # Attendre un peu pour que le menu s'ouvre
            time.sleep(1)
            
            # Cliquer sur le deuxième élément pour révéler le champ de saisie
            print("Clic sur le deuxième élément (le placeholder)...")
            # Utilisation d'un sélecteur CSS plus fiable basé sur l'enregistrement Selenium IDE
            placeholder_css = ".Select-placeholder"
            second_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, placeholder_css)))
            second_element.click()
            
            print("Envoi des touches à l'élément actif...")
            time.sleep(2) # Petite pause pour s'assurer que le focus est bien établi

            actions = ActionChains(self.driver)
            actions.send_keys("suez.com")
            actions.perform()
            time.sleep(5)
            print("send return ...")
            actions.send_keys(Keys.RETURN)
            actions.perform()            
            
            # Attendre 2 secondes que les résultats se chargent
            print("Attente de 2 secondes...")
            time.sleep(10)
            
            
            # Copier l'URL actuelle
            current_url = self.driver.current_url
            print(f"URL actuelle copiée: {current_url}")
            
            return current_url
            
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            return None
        
        finally:
            if self.driver:
                self.driver.quit()

# Fonction d'exemple pour créer un fichier de cookies de template
def create_cookies_template():
    """Crée un fichier de template pour les cookies"""
    template_cookies = [
        {
            "name": "session_id",
            "value": "VOTRE_SESSION_ID_ICI",
            "domain": ".apollo.io",
            "path": "/",
            "secure": True,
            "httpOnly": True
        },
        {
            "name": "auth_token",
            "value": "VOTRE_AUTH_TOKEN_ICI",
            "domain": ".apollo.io",
            "path": "/",
            "secure": True,
            "httpOnly": False
        }
        # Ajoutez d'autres cookies nécessaires ici
    ]
    
    with open('apollo_cookies_template.json', 'w', encoding='utf-8') as f:
        json.dump(template_cookies, f, indent=2, ensure_ascii=False)
    
    print("Template de cookies créé dans 'apollo_cookies_template.json'")
    print("Remplacez les valeurs par vos vrais cookies Apollo.io")

# Utilisation du script
if __name__ == "__main__":
    # Créer le template de cookies si nécessaire
    # create_cookies_template()
    
    # Utilisation du scraper
    cookies_file = "apollo_cookies.json"  # Remplacez par le chemin de votre fichier de cookies
    
    scraper = ApolloScraper(cookies_file)
    result_url = scraper.scrape_apollo()
    
    if result_url:
        print(f"\n✅ Scraping terminé avec succès!")
        print(f"URL finale: {result_url}")
    else:
        print("\n❌ Échec du scraping")

# Instructions d'utilisation:
"""
INSTALLATION ET CONFIGURATION POUR FIREFOX:

1. Installez les dépendances:
   pip install selenium webdriver-manager

2. Assurez-vous que Firefox est installé sur votre système:
   - macOS: Téléchargez depuis https://www.mozilla.org/firefox/
   - ou avec Homebrew: brew install --cask firefox

3. Le script téléchargera automatiquement la bonne version de GeckoDriver

4. Créez votre fichier de cookies JSON avec vos vrais cookies Apollo.io

5. Exécutez le script: python apollo_scraper.py

SOLUTIONS ALTERNATIVES SI LE PROBLÈME PERSISTE:

Option A - Installation manuelle de GeckoDriver:
1. Téléchargez GeckoDriver: https://github.com/mozilla/geckodriver/releases
2. Décompressez et placez le fichier dans votre PATH
3. ou avec Homebrew: brew install geckodriver

Option B - Mode headless (sans interface graphique):
- Ajoutez firefox_options.add_argument("--headless") dans setup_driver()

Option C - Vérifier l'installation de Firefox:
- Ouvrez un terminal et tapez: firefox --version
- Si Firefox n'est pas trouvé, installez-le depuis le site officiel

AVANTAGES DE FIREFOX POUR LE SCRAPING:
- Plus stable que Chrome pour l'automatisation
- Moins de problèmes de compatibilité
- Meilleure gestion des cookies
- Interface plus prévisible

Pour obtenir vos cookies Apollo.io:
- Connectez-vous manuellement à Apollo.io avec FIREFOX
- Ouvrez les outils de développement (F12)
- Allez dans l'onglet "Stockage" > "Cookies" > "https://app.apollo.io"
- Copiez les cookies importants (session_id, auth_token, etc.)
- Créez votre fichier JSON avec ces cookies

STRUCTURE DU FICHIER COOKIES:
[
  {
    "name": "nom_du_cookie",
    "value": "valeur_du_cookie",
    "domain": ".apollo.io",
    "path": "/",
    "secure": true,
    "httpOnly": true
  }
]

REMARQUE IMPORTANTE:
Les cookies peuvent être légèrement différents entre Chrome et Firefox.
Assurez-vous de récupérer les cookies depuis Firefox si vous utilisez ce navigateur.
"""
