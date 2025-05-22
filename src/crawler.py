import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import Set, List, Dict
import re

class WebCrawler:
    def __init__(self, start_url: str, max_pages: int = 100, delay: float = 1.0):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.documents: Dict[str, str] = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Configuration du logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def is_valid_url(self, url: str) -> bool:
        """Vérifie si l'URL est valide et appartient au même domaine."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def get_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL."""
        return urlparse(url).netloc

    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait."""
        # Supprime les caractères spéciaux et les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprime les caractères non imprimables
        text = ''.join(char for char in text if char.isprintable())
        return text.strip()

    def extract_text(self, soup: BeautifulSoup) -> str:
        """Extrait le texte pertinent d'une page."""
        # Supprime les balises script et style
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extrait le texte
        text = soup.get_text()
        return self.clean_text(text)

    def crawl(self) -> Dict[str, str]:
        """Crawl le site web à partir de l'URL de départ."""
        queue = [self.start_url]
        start_domain = self.get_domain(self.start_url)
        
        while queue and len(self.visited_urls) < self.max_pages:
            url = queue.pop(0)
            
            if url in self.visited_urls:
                continue
                
            try:
                self.logger.info(f"Crawling: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text = self.extract_text(soup)
                
                if text:
                    self.documents[url] = text
                
                self.visited_urls.add(url)
                
                # Trouve les nouveaux liens
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(url, link['href'])
                    if (self.is_valid_url(next_url) and 
                        self.get_domain(next_url) == start_domain and 
                        next_url not in self.visited_urls):
                        queue.append(next_url)
                
                time.sleep(self.delay)  # Respect des robots.txt
                
            except Exception as e:
                self.logger.error(f"Erreur lors du crawl de {url}: {str(e)}")
                continue
        
        return self.documents

    def save_documents(self, filename: str):
        """Sauvegarde les documents collectés dans un fichier."""
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2) 