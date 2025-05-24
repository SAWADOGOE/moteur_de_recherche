from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# Télécharger les ressources NLTK nécessaires
nltk.download('punkt')
nltk.download('stopwords')

load_dotenv()

class GoogleSearchAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = "2508fa652a95043c0"  # Votre ID de moteur de recherche
        self.service = build("customsearch", "v1", developerKey=self.api_key)
        self.stop_words = set(stopwords.words('french') + stopwords.words('english'))

    def calculate_score(self, result, query):
        """
        Calcule un score pour un résultat de recherche
        
        Args:
            result (dict): Le résultat de recherche
            query (str): La requête de recherche
        
        Returns:
            float: Score entre 0 et 1
        """
        score = 0.0
        query_terms = set(word.lower() for word in word_tokenize(query) if word.lower() not in self.stop_words)
        
        # Score de base pour les résultats Google
        score += 0.3
        
        # Score basé sur la présence des mots-clés dans le titre
        title = result.get('title', '').lower()
        title_matches = sum(1 for term in query_terms if term in title)
        score += 0.2 * (title_matches / len(query_terms)) if query_terms else 0
        
        # Score basé sur la présence des mots-clés dans le snippet
        snippet = result.get('snippet', '').lower()
        snippet_matches = sum(1 for term in query_terms if term in snippet)
        score += 0.3 * (snippet_matches / len(query_terms)) if query_terms else 0
        
        # Score basé sur la longueur du contenu
        content_length = len(snippet)
        if content_length > 200:
            score += 0.1
        elif content_length > 100:
            score += 0.05
        
        # Score basé sur la qualité de l'URL
        url = result.get('link', '')
        if any(domain in url.lower() for domain in ['.edu', '.gov', '.org']):
            score += 0.1
        
        return min(score, 1.0)  # Normaliser le score entre 0 et 1

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
                    # Calculer le score pour ce résultat
                    score = self.calculate_score(item, query)
                    
                    formatted_results.append({
                        'title': item['title'],
                        'url': item['link'],
                        'snippet': item['snippet'],
                        'source': 'google',
                        'score': score
                    })
            
            # Trier les résultats par score
            formatted_results.sort(key=lambda x: x['score'], reverse=True)
            
            return formatted_results
        
        except Exception as e:
            print(f"Erreur lors de la recherche Google : {str(e)}")
            return [] 