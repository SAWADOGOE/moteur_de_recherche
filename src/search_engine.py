import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pickle
from functools import lru_cache

class SearchEngine:
    def __init__(self):
        # Télécharger les ressources NLTK nécessaires
        nltk.download('punkt')
        nltk.download('stopwords')
        
        self.vectorizer = TfidfVectorizer()
        self.documents = []
        self.index = {}
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.cache_dir = os.path.join(self.data_dir, 'cache')
        
        # Créer les dossiers nécessaires
        for directory in [self.data_dir, self.cache_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Initialiser le cache
        self.cache = {}
        self.cache_expiry = timedelta(hours=1)
        self.load_cache()
    
    def preprocess_text(self, text):
        """Prétraite le texte en le tokenisant et en retirant les mots vides."""
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('french'))
        return [token for token in tokens if token.isalnum() and token not in stop_words]
    
    def index_document(self, doc_id, content):
        """Indexe un nouveau document."""
        processed_content = ' '.join(self.preprocess_text(content))
        self.documents.append(processed_content)
        self.index[doc_id] = len(self.documents) - 1
        
        # Sauvegarder l'index
        self._save_index()
        # Invalider le cache
        self.clear_cache()
    
    @lru_cache(maxsize=1000)
    def _get_cached_results(self, query: str, filters: str) -> Optional[List[Dict]]:
        """Récupère les résultats du cache."""
        cache_key = f"{query}_{filters}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['results']
        return None
    
    def search(self, query: str, filters: Dict = None, sort_by: str = 'relevance') -> List[Dict]:
        """Recherche des documents pertinents pour une requête avec filtres et tri."""
        if not self.documents:
            return []
        
        # Vérifier le cache
        filters_str = json.dumps(filters or {}, sort_keys=True)
        cached_results = self._get_cached_results(query, filters_str)
        if cached_results is not None:
            return cached_results
        
        # Vectoriser les documents et la requête
        tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        query_vector = self.vectorizer.transform([query])
        
        # Calculer la similarité cosinus
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Trier les résultats par pertinence
        results = []
        for idx, score in enumerate(similarities):
            if score > 0:
                doc_id = [k for k, v in self.index.items() if v == idx][0]
                result = {
                    'id': doc_id,
                    'score': float(score),
                    'content': self.documents[idx],
                    'timestamp': datetime.now().isoformat()
                }
                
                # Appliquer les filtres
                if filters:
                    if not self._apply_filters(result, filters):
                        continue
                
                results.append(result)
        
        # Trier les résultats
        if sort_by == 'relevance':
            results.sort(key=lambda x: x['score'], reverse=True)
        elif sort_by == 'date':
            results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Mettre en cache les résultats
        self.cache[f"{query}_{filters_str}"] = {
            'results': results,
            'timestamp': datetime.now()
        }
        self._save_cache()
        
        return results
    
    def _apply_filters(self, result: Dict, filters: Dict) -> bool:
        """Applique les filtres aux résultats."""
        for key, value in filters.items():
            if key == 'min_score' and result['score'] < value:
                return False
            if key == 'date_after':
                result_date = datetime.fromisoformat(result['timestamp'])
                filter_date = datetime.fromisoformat(value)
                if result_date < filter_date:
                    return False
        return True
    
    def _save_index(self):
        """Sauvegarde l'index sur disque."""
        index_file = os.path.join(self.data_dir, 'index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                'index': self.index,
                'documents': self.documents
            }, f, ensure_ascii=False, indent=2)
    
    def load_index(self):
        """Charge l'index depuis le disque."""
        index_file = os.path.join(self.data_dir, 'index.json')
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.index = data['index']
                self.documents = data['documents']
    
    def _save_cache(self):
        """Sauvegarde le cache sur disque."""
        cache_file = os.path.join(self.cache_dir, 'search_cache.pkl')
        with open(cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def load_cache(self):
        """Charge le cache depuis le disque."""
        cache_file = os.path.join(self.cache_dir, 'search_cache.pkl')
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                self.cache = pickle.load(f)
    
    def clear_cache(self):
        """Vide le cache."""
        self.cache.clear()
        self._save_cache()
        self._get_cached_results.cache_clear() 