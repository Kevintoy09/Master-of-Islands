"""
=================================================================
MARKET_ROUTES.PY - Routes API pour le système de marché
=================================================================

RESPONSABILITÉS:
- API pour créer des offres de vente
- API pour lister les offres disponibles dans le rayon d'action
- API pour acheter des offres
- API pour annuler ses propres offres
- API pour consulter ses offres actives

ROUTES DISPONIBLES:
- GET /api/market/<city_id>/offers - Lister offres disponibles
- POST /api/market/<city_id>/create-offer - Créer une offre
- POST /api/market/<city_id>/buy-offer - Acheter une offre
- DELETE /api/market/<city_id>/cancel-offer/<offer_id> - Annuler offre
- GET /api/market/player/<player_id>/my-offers - Mes offres

AVANT D'AJOUTER UNE ROUTE:
- Utiliser MarketService pour la logique métier
- Valider les données d'entrée
- Gérer les erreurs proprement

DÉPENDANCES:
- MarketService pour la logique
- DataManager pour les données
=================================================================
"""

from flask import Blueprint, request, jsonify
from ..core.decorators import handle_errors, validate_json
from ..core.exceptions import GameValidationError, CityNotFoundError
from ..business.market_service import MarketService
from ..data_manager import DataManager

# Initialiser le blueprint
market_bp = Blueprint('market', __name__, url_prefix='/api/city')

# Services à injecter
data_manager = None
market_service = None

def init_market_routes(dm):
    """Initialise les routes avec les services"""
    global data_manager, market_service
    data_manager = dm
    market_service = MarketService(dm)

@market_bp.route('/<city_id>/market/capabilities', methods=['GET'])
@handle_errors
def get_market_capabilities(city_id):
    """Récupère les capacités du marché d'une ville"""
    capabilities = market_service.get_market_capabilities_detailed(city_id)
    
    if not capabilities:
        return jsonify({
            'success': False,
            'message': 'Cette ville n\'a pas de marché'
        }), 404
    
    return jsonify({
        'success': True,
        'capabilities': capabilities
    })

@market_bp.route('/<city_id>/market/available-offers', methods=['GET'])
@handle_errors
def get_available_offers(city_id):
    """Récupère toutes les offres disponibles dans le rayon d'action"""
    offers = market_service.get_available_offers(city_id)
    
    # Enrichir les offres avec des informations supplémentaires pour le frontend
    enriched_offers = []
    
    # Charger les données pour enrichissement
    savegame_data = data_manager.load_savegame()
    universe_data = data_manager.load_universe()
    players_data = data_manager.load_players()
    
    for offer in offers:
        # Trouver les informations du vendeur
        seller_city_id = offer.get('seller_city_id')
        seller_player_id = offer.get('seller_player_id')
        seller_island_id = offer.get('seller_island_id')
        
        # Trouver le nom de la ville vendeuse
        seller_city_name = offer.get('seller_city_name', 'Ville inconnue')
        if seller_city_name == 'Ville inconnue' and seller_city_id:
            # Chercher dans savegame_data
            for city in savegame_data.get('cities', []):
                if city.get('id') == seller_city_id:
                    seller_city_name = city.get('name', 'Ville inconnue')
                    break
        
        # Nom du joueur
        seller_player_name = 'Joueur inconnu'
        if seller_player_id and players_data:
            for player in players_data.get('players', []):
                if player.get('id') == seller_player_id:
                    seller_player_name = player.get('username', seller_player_id)
                    break
        
        # Informations de l'île
        seller_island_name = 'Île inconnue'
        seller_island_coords = [0, 0]
        if seller_island_id and universe_data:
            for island in universe_data.get('islands', []):
                if island.get('id') == seller_island_id:
                    seller_island_name = island.get('name', 'Île inconnue')
                    seller_island_coords = island.get('coords', [0, 0])
                    break
        
        # Coût total
        quantity = offer.get('quantity', 0)
        price_per_unit = offer.get('price_per_unit', 0)
        total_cost = quantity * price_per_unit
        
        # Émoji de la ressource (mapping côté serveur pour cohérence)
        resource_emojis = {
            'wood': '🪵',
            'stone': '🗿',
            'iron': '⛏️',
            'cereal': '🌾',
            'papyrus': '📜',
            'horse': '🐎',
            'marble': '🏛️',
            'glass': '🔷',
            'wine': '🍷',
            'coal': '⚫',
            'gunpowder': '💥',
            'spices': '🌶️',
            'cotton': '☁️'
        }
        resource_type = offer.get('resource_type', '')
        resource_emoji = resource_emojis.get(resource_type, '❓')
        
        enriched_offer = {
            'id': offer.get('id'),
            'seller_city_id': offer.get('seller_city_id'),
            'seller_city_name': seller_city_name,
            'seller_player_id': seller_player_id,
            'seller_player_name': seller_player_name,
            'seller_island_id': seller_island_id,
            'seller_island_name': seller_island_name,
            'seller_island_coords': seller_island_coords,
            'resource_type': resource_type,
            'resource_emoji': resource_emoji,
            'quantity': quantity,
            'price_per_unit': price_per_unit,
            'total_cost': total_cost,
            'distance': offer.get('distance', 0),
            'created_at': offer.get('created_at')
        }
        enriched_offers.append(enriched_offer)
    
    return jsonify({
        'success': True,
        'offers': enriched_offers,
        'count': len(enriched_offers)
    })

@market_bp.route('/<city_id>/market/create-offer', methods=['POST'])
@handle_errors
def create_offer(city_id):
    """Crée une nouvelle offre de vente"""
    data = request.get_json()
    
    # Validation manuelle pour le test
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    
    required_fields = ['resource_type', 'quantity', 'price_per_unit']
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        return jsonify({'error': f"Champs requis manquants: {', '.join(missing_fields)}"}), 400
    
    resource = data['resource_type']  # Le popup envoie 'resource_type'
    quantity = int(data['quantity'])
    price_per_unit = float(data['price_per_unit'])
    
    # Validations
    if quantity <= 0:
        raise GameValidationError("La quantité doit être positive")
    
    if price_per_unit <= 0:
        raise GameValidationError("Le prix doit être positif")
    
    # Ressources autorisées (toutes sauf l'or et les points de recherche)
    allowed_resources = [
        'wood', 'stone', 'iron', 'cereal', 'papyrus', 'marble', 
        'wine', 'horse', 'glass', 'coal', 'gunpowder', 'spices', 'cotton'
    ]
    
    if resource not in allowed_resources:
        raise GameValidationError(f"Ressource non autorisée: {resource}")
    
    result = market_service.create_offer(city_id, resource, quantity, price_per_unit)
    
    return jsonify(result)

@market_bp.route('/<city_id>/market/buy-offer/<offer_id>', methods=['POST'])
@handle_errors
def buy_offer(city_id, offer_id):
    """Achète une offre complètement"""
    result = market_service.buy_offer_complete(city_id, offer_id)
    
    return jsonify(result)

@market_bp.route('/<city_id>/market/cancel-offer/<offer_id>', methods=['DELETE'])
@handle_errors
def cancel_offer(city_id, offer_id):
    """Annule une offre et rend les ressources"""
    result = market_service.cancel_offer(city_id, offer_id)
    
    return jsonify(result)

@market_bp.route('/<city_id>/market/my-offers', methods=['GET'])
@handle_errors
def get_my_offers(city_id):
    """Récupère toutes les offres de cette ville"""
    
    # Trouver le joueur propriétaire de cette ville
    savegame_data = data_manager.load_savegame()
    if not savegame_data:
        return jsonify({'success': True, 'offers': []})
    
    # Trouver la ville pour récupérer le player_id
    city = None
    for c in savegame_data['cities']:
        if c['id'] == city_id:
            city = c
            break
    
    if not city:
        return jsonify({'success': True, 'offers': []})
    
    player_id = city['owner']  # Utiliser 'owner' au lieu de 'player_id'
    
    # Utiliser le nouveau service market pour récupérer les offres du joueur
    try:
        player_offers = market_service.get_player_offers(player_id)
        
        # Filtrer pour ne garder que les offres de cette ville
        city_offers = [offer for offer in player_offers if offer.get('seller_city_id') == city_id]
        
        # Formater pour le popup
        formatted_offers = []
        
        # Émojis des ressources (même mapping que pour available-offers)
        resource_emojis = {
            'wood': '🪵',
            'stone': '🗿',
            'iron': '⛏️',
            'cereal': '🌾',
            'papyrus': '📜',
            'horse': '🐎',
            'marble': '🏛️',
            'glass': '🔷',
            'wine': '🍷',
            'coal': '⚫',
            'gunpowder': '💥',
            'spices': '🌶️',
            'cotton': '☁️'
        }
        
        for offer in city_offers:
            resource_type = offer.get('resource_type', '')
            resource_emoji = resource_emojis.get(resource_type, '❓')
            
            formatted_offer = {
                'id': offer.get('id'),
                'seller_city_id': offer.get('seller_city_id'),
                'seller_name': 'Ma ville',  # C'est notre ville
                'resource_type': resource_type,
                'resource_emoji': resource_emoji,
                'quantity': offer.get('quantity'),
                'price_per_unit': offer.get('price_per_unit'),
                'total_price': offer.get('quantity', 0) * offer.get('price_per_unit', 0),
                'created_at': offer.get('created_at')
            }
            formatted_offers.append(formatted_offer)

        return jsonify({
            'success': True,
            'offers': formatted_offers,
            'count': len(formatted_offers)
        })
        
    except Exception as e:
        print(f"🚨 ERROR in get_my_offers: {str(e)}")
        return jsonify({'success': True, 'offers': [], 'count': 0})

@market_bp.route('/<city_id>/cities-in-range', methods=['GET'])
@handle_errors
def get_cities_in_range(city_id):
    """Récupère les villes dans le rayon d'action du marché"""
    cities_in_range = market_service.get_cities_in_range(city_id)
    
    # Récupérer les informations des villes
    savegame_data = data_manager.load_savegame()
    city_info = []
    
    if savegame_data:
        for city_id_in_range in cities_in_range:
            city = next((c for c in savegame_data.get('cities', []) 
                        if c['id'] == city_id_in_range), None)
            if city:
                city_info.append({
                    'id': city['id'],
                    'name': city.get('name', 'Ville inconnue'),
                    'owner': city.get('owner'),
                    'island_id': city.get('island_id')
                })
    
    return jsonify({
        'success': True,
        'cities': city_info,
        'count': len(city_info)
    })

@market_bp.route('/global-offers', methods=['GET'])
@handle_errors  
def get_global_offers():
    """Récupère toutes les offres disponibles sur le marché global (pour admin/debug)"""
    savegame_data = data_manager.load_savegame()
    
    if not savegame_data:
        return jsonify({
            'success': False,
            'message': 'Erreur de chargement des données'
        }), 500
    
    all_offers = savegame_data.get('market_offers', [])
    
    # Ajouter les informations des villes
    for offer in all_offers:
        seller_city = next((c for c in savegame_data.get('cities', []) 
                          if c['id'] == offer.get('seller_city_id')), None)
        if seller_city:
            offer['seller_city_name'] = seller_city.get('name', 'Ville inconnue')
            offer['seller_island_id'] = seller_city.get('island_id')
    
    return jsonify({
        'success': True,
        'offers': all_offers,
        'count': len(all_offers)
    })

@market_bp.route('/statistics', methods=['GET'])
@handle_errors
def get_market_statistics():
    """Récupère les statistiques du marché"""
    savegame_data = data_manager.load_savegame()
    
    if not savegame_data:
        return jsonify({
            'success': False,
            'message': 'Erreur de chargement des données'
        }), 500
    
    all_offers = savegame_data.get('market_offers', [])
    
    # Statistiques par ressource
    resource_stats = {}
    total_value = 0
    
    for offer in all_offers:
        resource = offer.get('resource')
        quantity = offer.get('quantity', 0)
        total_price = offer.get('total_price', 0)
        
        if resource not in resource_stats:
            resource_stats[resource] = {
                'total_quantity': 0,
                'total_value': 0,
                'offer_count': 0,
                'avg_price': 0
            }
        
        resource_stats[resource]['total_quantity'] += quantity
        resource_stats[resource]['total_value'] += total_price
        resource_stats[resource]['offer_count'] += 1
        total_value += total_price
    
    # Calculer prix moyens
    for resource, stats in resource_stats.items():
        if stats['total_quantity'] > 0:
            stats['avg_price'] = stats['total_value'] / stats['total_quantity']
    
    return jsonify({
        'success': True,
        'statistics': {
            'total_offers': len(all_offers),
            'total_market_value': total_value,
            'resource_breakdown': resource_stats
        }
    })
