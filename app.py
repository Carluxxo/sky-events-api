import requests
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)
executor = ThreadPoolExecutor(3)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache de dados
event_cache = {
    'last_updated': None,
    'data': None
}

def fetch_nasa_approaches():
    """Obtém dados de aproximação de objetos da NASA"""
    try:
        url = "https://ssd-api.jpl.nasa.gov/cad.api"
        params = {
            'date-min': datetime.now().strftime('%Y-%m-%d'),
            'date-max': '2025-12-31',
            'dist-max': '0.1',
            'fullname': 'true'
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        return [{
            'name': item[0],
            'type': 'close_approach',
            'date': item[3],
            'distance_au': float(item[4]),
            'velocity_km_s': float(item[7]),
            'visibility': 'Global',
            'source': url
        } for item in data.get('data', [])]
    
    except Exception as e:
        logger.error(f"NASA Approaches Error: {str(e)}")
        return []

def fetch_nasa_eclipses():
    """Obtém dados de eclipses da NASA"""
    try:
        url = "https://ssd-api.jpl.nasa.gov/eclipse.api"
        params = {'year': '2025', 'type': 'solar'}
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        return [{
            'name': f"{eclipse['type']} Eclipse",
            'type': 'eclipse',
            'date': eclipse['date'],
            'visibility': eclipse['region'],
            'coordinates': eclipse.get('path_coordinates'),
            'source': url
        } for eclipse in data.get('eclipses', [])]
    
    except Exception as e:
        logger.error(f"NASA Eclipses Error: {str(e)}")
        return []

def fetch_imo_meteors():
    """Obtém dados de chuvas de meteoros da IMO com tratamento seguro"""
    try:
        url = "https://data.imo.net/members/imo_v3/calendar/2025/"
        response = requests.get(url, timeout=15, verify=False)  # SSL desabilitado temporariamente
        response.raise_for_status()
        data = response.json()
        
        processed = []
        for shower in data:
            try:
                # Converter formato de data '2025-Apr-25' para ISO
                date_obj = datetime.strptime(shower['peak'], '%Y-%b-%d')
                processed.append({
                    'name': shower['name'],
                    'type': 'meteor_shower',
                    'date': date_obj.isoformat(),
                    'visibility': 'Global',
                    'rate': shower.get('zhr'),
                    'source': url
                })
            except (KeyError, ValueError) as e:
                logger.warning(f"Erro processando chuva {shower.get('name')}: {str(e)}")
        return processed
    
    except Exception as e:
        logger.error(f"IMO Meteors Error: {str(e)}")
        return []

def safe_date_sort(event):
    """Ordenação segura com tratamento de datas inválidas"""
    try:
        return datetime.fromisoformat(event['date'].split('T')[0])
    except Exception as e:
        logger.warning(f"Data inválida no evento {event.get('name')}: {str(e)}")
        return datetime.max  # Coloca eventos com datas inválidas no final

def update_event_cache():
    """Atualiza o cache com tratamento robusto de erros"""
    with app.app_context():
        logger.info("Iniciando atualização do cache...")
        
        futures = {
            'approaches': executor.submit(fetch_nasa_approaches),
            'eclipses': executor.submit(fetch_nasa_eclipses),
            'meteors': executor.submit(fetch_imo_meteors)
        }
        
        results = []
        for name, future in futures.items():
            try:
                result = future.result()
                logger.info(f"{name}: {len(result)} eventos coletados")
                results.extend(result)
            except Exception as e:
                logger.error(f"Falha na coleta de {name}: {str(e)}")

        # Ordenação segura
        event_cache['data'] = sorted(results, key=safe_date_sort)
        event_cache['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Cache atualizado com {len(results)} eventos")

@app.route('/api/events', methods=['GET'])
def get_all_events():
    """Endpoint principal para obter todos os eventos"""
    if not event_cache['data']:
        update_event_cache()
    
    return jsonify({
        'count': len(event_cache['data']),
        'events': event_cache['data'],
        'last_updated': event_cache['last_updated'],
        'sources': [
            'NASA Close Approach Data API',
            'NASA Eclipse API',
            'International Meteor Organization'
        ]
    })

@app.route('/api/update', methods=['POST'])
def force_update():
    """Força a atualização do cache"""
    update_event_cache()
    return jsonify({'status': 'cache atualizado'})

if __name__ == '__main__':
    # Configuração inicial
    with app.app_context():
        try:
            update_event_cache()
        except Exception as e:
            logger.critical(f"Falha crítica na inicialização: {str(e)}")
    
    # Configuração do servidor
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,
        use_reloader=False
    )