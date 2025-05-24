from flask import Flask, render_template, request, jsonify
from search_engine import SearchEngine
from crawler import WebCrawler
from google_search import GoogleSearchAPI
import os
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
search_engine = SearchEngine()
google_search = GoogleSearchAPI()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    logger.debug(f"Requête de recherche reçue: {query}")
    
    if not query:
        return jsonify({'results': []})
    
    # Récupérer les paramètres de filtrage et de tri
    filters = {}
    min_score = request.args.get('min_score')
    if min_score:
        filters['min_score'] = float(min_score)
    
    date_after = request.args.get('date_after')
    if date_after:
        filters['date_after'] = date_after
    
    sort_by = request.args.get('sort_by', 'relevance')
    
    try:
        # Obtenir les résultats des deux sources
        local_results = search_engine.search(query, filters, sort_by)
        logger.debug(f"Résultats locaux: {len(local_results)}")
        
        google_results = google_search.search(query)
        logger.debug(f"Résultats Google: {len(google_results)}")
        
        # Combiner les résultats
        all_results = local_results + google_results
        logger.debug(f"Total des résultats: {len(all_results)}")
        
        # Trier les résultats si nécessaire
        if sort_by == 'relevance':
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return jsonify({'results': all_results})
    
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/crawl', methods=['POST'])
def crawl():
    """Endpoint pour lancer le crawler."""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL requise'}), 400
    
    try:
        crawler = WebCrawler(
            start_url=data['url'],
            max_pages=int(data.get('max_pages', 100)),
            delay=float(data.get('delay', 1.0))
        )
        
        documents = crawler.crawl()
        
        # Indexer les documents collectés
        for url, content in documents.items():
            search_engine.index_document(url, content)
        
        return jsonify({
            'message': f'{len(documents)} documents indexés avec succès',
            'documents': list(documents.keys())
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    """Endpoint pour obtenir les statistiques du moteur de recherche."""
    return jsonify({
        'total_documents': len(search_engine.documents),
        'cache_size': len(search_engine.cache),
        'index_size': len(search_engine.index)
    })

if __name__ == '__main__':
    app.run(debug=True) 