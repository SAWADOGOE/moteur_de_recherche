from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()

class GoogleSearchAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = "2508fa652a95043c0"  # Votre ID de moteur de recherche
        self.service = build("customsearch", "v1", developerKey=self.api_key)

    def search(self, query, num_results=10):
        """
        Effectue une recherche via l'API Google Custom Search
        
        Args:
            query (str): La requête de recherche
            num_results (int): Nombre de résultats à retourner
        
        Returns:
            list: Liste des résultats de recherche formatés
        """
        try:
            result = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=num_results
            ).execute()
            
            formatted_results = []
            if 'items' in result:
                for item in result['items']:
                    formatted_results.append({
                        'title': item['title'],
                        'url': item['link'],
                        'snippet': item['snippet'],
                        'source': 'google',
                        'score': 1.0  # Score par défaut pour les résultats Google
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"Erreur lors de la recherche Google : {str(e)}")
            return [] 