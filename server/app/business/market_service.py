import time
import uuid
import math
from typing import Dict, List, Any, Optional, Tuple
from ..core.exceptions import GameValidationError
from ..data_manager import DataManager
from ..game_logic import GameLogic
from ..services.save_service import get_save_service
from ..transition_utils import load_savegame_transition, save_savegame_transition


class MarketOffer:
    def __init__(self, id: str, seller_city_id: str, seller_player_id: str, 
                 resource_type: str, quantity: int, price_per_unit: int, created_at: int):
        self.id = id
        self.seller_city_id = seller_city_id
        self.seller_player_id = seller_player_id
        self.resource_type = resource_type
        self.quantity = quantity
        self.price_per_unit = price_per_unit
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketOffer':
        return cls(
            id=data['id'],
            seller_city_id=data['seller_city_id'],
            seller_player_id=data['seller_player_id'],
            resource_type=data['resource_type'],
            quantity=data['quantity'],
            price_per_unit=data['price_per_unit'],
            created_at=data['created_at']
        )


class MarketService:
    def __init__(self, data_manager: DataManager, transport_manager=None):
        self.data_manager = data_manager
        self.game_logic = GameLogic(data_manager)
        self.transport_manager = transport_manager

    def _calculate_virtual_transport(self, source_city_id: str, destination_city_id: str, 
                                   resource_type: str, quantity: int, universe: Dict) -> Dict[str, Any]:
        """Calcule les paramètres d'un transport virtuel pour un achat de marché."""
        
        # Trouver les coordonnées des villes dans l'univers
        source_coords = None
        dest_coords = None
        
        for island in universe.get('islands', []):
            for city in island.get('cities', []):
                if city['id'] == source_city_id:
                    source_coords = island['coordinates']
                elif city['id'] == destination_city_id:
                    dest_coords = island['coordinates']
        
        if not source_coords or not dest_coords:
            # Valeurs par défaut si coordonnées introuvables
            distance = 100.0
        else:
            # Calculer la distance euclidienne avec coefficient d'échelle
            from app.city_constants import TRANSPORT_CONSTANTS
            dx = abs(source_coords[0] - dest_coords[0])
            dy = abs(source_coords[1] - dest_coords[1])
            raw_distance = math.sqrt(dx*dx + dy*dy)
            distance = raw_distance * TRANSPORT_CONSTANTS['DISTANCE_SCALE_FACTOR']
        
        # Calculer les besoins en transport
        # Règle simple : 1 bateau peut transporter 100 unités de base
        cargo_per_ship = 100
        ships_needed = max(1, math.ceil(quantity / cargo_per_ship))
        
        # Temps de chargement : 1 seconde par unité de ressource
        loading_time = max(5.0, quantity * 0.1)  # Minimum 5 secondes
        
        # Temps de transport ALLER (le retour aura la même durée automatiquement)
        transport_time = max(10.0, distance * 0.1)  # Minimum 10 secondes
        
        # Temps total estimé = chargement + aller + retour
        total_estimated_time = loading_time + (2 * transport_time)
        
        return {
            'ships_needed': ships_needed,
            'loading_time': loading_time,
            'transport_time': transport_time,
            'total_estimated_time': total_estimated_time,
            'distance': distance
        }

    def _save_with_sync(self, savegame: Dict[str, Any], force_save: bool = True) -> None:
        """Sauvegarde avec synchronisation automatique du cache SaveService"""
        self.data_manager.save_savegame(savegame, force_save=force_save)
        
        # Synchroniser le cache SaveService pour éviter les conflits
        save_service = get_save_service()
        save_service._cache = savegame.copy()
        save_service._cache_timestamp = time.time()

    def create_offer(self, seller_city_id: str, resource_type: str, quantity: int, price_per_unit: int) -> Dict[str, Any]:
        """Crée une nouvelle offre de marché"""
        # Charger les données nécessaires - COHÉRENCE: même source pour load/save
        savegame = self.data_manager.load_savegame()
        universe = self.data_manager.load_universe()
        market_data = self.data_manager.load_market()
        
        # Valider que la ville appartient au joueur actuel
        player_id = savegame['current_player']
        
        # Trouver la ville du vendeur
        seller_city = None
        for city in savegame['cities']:
            if city['id'] == seller_city_id:
                seller_city = city
                break
        
        if not seller_city:
            raise GameValidationError("Ville vendeuse introuvable")
        
        if seller_city['owner'] != player_id:
            raise GameValidationError("Vous ne pouvez pas vendre depuis cette ville")
        
        # Vérifier que la ville a un marché
        market_building = None
        for building in seller_city['buildings']:
            if building.get('name', '').lower() == 'market':
                market_building = building
                break
        
        if not market_building:
            raise GameValidationError("Cette ville n'a pas de marché")
        
        # Vérifier la disponibilité des ressources
        if seller_city['resources'].get(resource_type, 0) < quantity:
            raise GameValidationError(f"Ressources insuffisantes : {resource_type}")
        
        # Déduire les ressources immédiatement
        seller_city['resources'][resource_type] -= quantity
        
        # Créer l'offre
        offer_id = str(uuid.uuid4())
        offer = {
            'id': offer_id,
            'seller_city_id': seller_city_id,
            'seller_player_id': player_id,
            'resource_type': resource_type,
            'quantity': quantity,
            'price_per_unit': price_per_unit,
            'created_at': int(time.time())
        }
        
        # Ajouter l'offre à market.json
        market_data['offers'].append(offer)
        
        # Sauvegarder les données (DataManager + synchronisation cache SaveService)
        self.data_manager.save_savegame(savegame, force_save=True)
        
        # Synchroniser le cache SaveService pour éviter les conflits
        save_service = get_save_service()
        save_service._cache = savegame.copy()
        save_service._cache_timestamp = time.time()
        
        # Sauvegarder market.json
        self.data_manager.save_market(market_data)
        
        return {
            'success': True,
            'offer': offer,
            'message': f"Offre créée : {quantity} {resource_type} à {price_per_unit} par unité"
        }

    def get_available_offers(self, buyer_city_id: str) -> List[Dict[str, Any]]:
        """Récupère les offres disponibles dans le rayon d'action"""
        # Charger les données avec optimisation
        market_data = self.data_manager.load_market()
        savegame = load_savegame_transition()
        universe = self.data_manager.load_universe()
        
        # Trouver la ville acheteuse
        buyer_city = None
        for city in savegame['cities']:
            if city['id'] == buyer_city_id:
                buyer_city = city
                break
        
        if not buyer_city:
            raise GameValidationError("Ville acheteuse introuvable")
        
        # Vérifier que la ville a un marché
        market_building = None
        for building in buyer_city['buildings']:
            if building.get('name', '').lower() == 'market':
                market_building = building
                break
        
        if not market_building:
            raise GameValidationError("Cette ville n'a pas de marché")
        
        # Calculer le rayon d'action
        market_level = market_building.get('level', 1)
        action_radius = self._calculate_market_radius(market_level)
        
        # Filtrer les offres dans le rayon d'action
        available_offers = []
        buyer_island_id = buyer_city['island_id']
        
        for offer in market_data['offers']:
            # Trouver la ville vendeuse
            seller_city = None
            for city in savegame['cities']:
                if city['id'] == offer['seller_city_id']:
                    seller_city = city
                    break
            
            if not seller_city:
                continue  # Ville vendeuse introuvable, ignorer l'offre
            
            # Exclure ses propres offres
            if offer['seller_player_id'] == buyer_city['owner']:
                continue
            
            # Vérifier la distance
            distance = self._calculate_distance(buyer_island_id, seller_city['island_id'], universe)
            
            if self._is_within_market_radius(buyer_island_id, seller_city['island_id'], action_radius, universe):
                # Enrichir l'offre avec des informations supplémentaires
                enriched_offer = offer.copy()
                enriched_offer['seller_city_name'] = seller_city['name']
                enriched_offer['seller_island_id'] = seller_city['island_id']
                enriched_offer['distance'] = distance
                
                available_offers.append(enriched_offer)
        
        return available_offers

    def buy_offer(self, buyer_city_id: str, offer_id: str, quantity: int) -> Dict[str, Any]:
        """Achète tout ou partie d'une offre"""
        # Charger les données avec optimisation
        savegame = load_savegame_transition()
        universe = self.data_manager.load_universe()
        market_data = self.data_manager.load_market()
        
        # Trouver l'offre
        offer_data = self._find_offer_by_id(offer_id)
        if not offer_data:
            raise GameValidationError("Offre introuvable")
        
        offer = MarketOffer.from_dict(offer_data)
        
        # Valider la quantité
        if quantity <= 0 or quantity > offer.quantity:
            raise GameValidationError("Quantité invalide")
        
        # Trouver les villes
        buyer_city = None
        seller_city = None
        
        for city in savegame['cities']:
            if city['id'] == buyer_city_id:
                buyer_city = city
            if city['id'] == offer.seller_city_id:
                seller_city = city
        
        if not buyer_city:
            raise GameValidationError("Ville acheteuse introuvable")
        if not seller_city:
            raise GameValidationError("Ville vendeuse introuvable")
        
        # Vérifier que l'acheteur ne peut pas acheter ses propres offres
        if buyer_city['owner'] == offer.seller_player_id:
            raise GameValidationError("Vous ne pouvez pas acheter vos propres offres")
        
        # Calculer le coût total
        total_cost = quantity * offer.price_per_unit
        
        # Effectuer la transaction financière
        # L'or est stocké dans players.json, pas dans savegame.json
        players_data = self.data_manager.load_players()
        
        # Trouver les joueurs
        buyer_player = None
        seller_player = None
        for player in players_data['players']:
            if player['id'] == buyer_city['owner']:
                buyer_player = player
            if player['id'] == offer.seller_player_id:
                seller_player = player
        
        if not buyer_player:
            raise GameValidationError("Joueur acheteur introuvable")
        if not seller_player:
            raise GameValidationError("Joueur vendeur introuvable")
        
        # Vérifier les fonds de l'acheteur dans players.json
        if buyer_player.get('gold', 0) < total_cost:
            raise GameValidationError("Fonds insuffisants")
        
        # Effectuer la transaction dans players.json
        buyer_player['gold'] -= total_cost
        seller_player['gold'] = seller_player.get('gold', 0) + total_cost
        
        # === NOUVEAU : TRANSPORT VIRTUEL AU LIEU DE TRANSACTION INSTANTANÉE ===
        transport_created = False
        transport_info = {}
        
        if self.transport_manager:
            try:
                # Calculer les paramètres du transport virtuel
                transport_params = self._calculate_virtual_transport(
                    offer.seller_city_id, buyer_city_id, 
                    offer.resource_type, quantity, universe
                )
                
                # Créer le transport virtuel avec un ID spécial pour le marché
                virtual_transport = self.transport_manager.create_market_transport(
                    source_city_id=offer.seller_city_id,
                    destination_city_id=buyer_city_id,
                    player_id=buyer_city['owner'],  # Le transport appartient à l'acheteur
                    resources={offer.resource_type: quantity},
                    ships_needed=transport_params['ships_needed'],
                    loading_time=transport_params['loading_time'],
                    transport_time=transport_params['transport_time']
                )
                
                transport_created = True
                transport_info = {
                    'transport_id': virtual_transport.id,
                    'ships_needed': transport_params['ships_needed'],
                    'estimated_delivery': transport_params['loading_time'] + transport_params['transport_time'],  # Temps pour recevoir les ressources
                    'estimated_total': transport_params['total_estimated_time'],  # Temps total avec retour
                    'distance': transport_params['distance']
                }
                
                message = f"Achat réussi ! Transport créé : {quantity} {offer.resource_type} arriveront dans {transport_info['estimated_delivery']:.0f}s (transport total: {transport_info['estimated_total']:.0f}s)"
                
            except Exception as e:
                # Si le transport échoue, faire une transaction instantanée en fallback
                buyer_city['resources'][offer.resource_type] = (
                    buyer_city['resources'].get(offer.resource_type, 0) + quantity
                )
                message = f"Achat réussi : {quantity} {offer.resource_type} pour {total_cost} or (livraison instantanée - erreur transport)"
        else:
            # Pas de TransportManager, transaction instantanée
            buyer_city['resources'][offer.resource_type] = (
                buyer_city['resources'].get(offer.resource_type, 0) + quantity
            )
            message = f"Achat réussi : {quantity} {offer.resource_type} pour {total_cost} or (livraison instantanée)"
        
        # Mettre à jour l'offre
        if quantity == offer.quantity:
            # Préparer les informations de l'acheteur pour l'historique (sans recharger savegame)
            buyer_info = {
                'buyer_city_id': buyer_city_id,
                'buyer_player_id': buyer_city['owner'],
                'buyer_coordinates': self._get_city_coordinates_cached(buyer_city, savegame),
                'quantity': quantity,
                'total_cost': total_cost
            }
            
            # Supprimer l'offre complètement et l'ajouter à l'historique
            self._remove_offer_by_id(offer_id, buyer_info)
        else:
            # Réduire la quantité
            self._update_offer_quantity(offer_id, offer.quantity - quantity)
        
        # Sauvegarder les données avec transition_utils (batch saving optimisé)
        save_savegame_transition(savegame, force=False)  # Sauvegarde différée
        self.data_manager.save_players(players_data)  # Players.json reste immédiat pour l'or
        self.data_manager.save_market(market_data)  # Market.json reste immédiat pour les offres
        
        # Construire la réponse avec les informations de transport
        response = {
            'success': True,
            'transaction': {
                'offer_id': offer_id,
                'resource_type': offer.resource_type,
                'quantity': quantity,
                'total_cost': total_cost
            },
            'message': message
        }
        
        # Ajouter les informations de transport si disponibles
        if transport_created and transport_info:
            response['transport'] = transport_info
        
        return response

    def buy_offer_complete(self, buyer_city_id: str, offer_id: str) -> Dict[str, Any]:
        """Achète une offre complète"""
        # Trouver l'offre dans market.json
        offer_data = self._find_offer_by_id(offer_id)
        if not offer_data:
            raise GameValidationError("Offre introuvable")
        
        offer = MarketOffer.from_dict(offer_data)
        
        # Acheter la quantité complète
        return self.buy_offer(buyer_city_id, offer_id, offer.quantity)

    def cancel_offer(self, player_id: str, offer_id: str) -> Dict[str, Any]:
        """Annule une offre et restitue les ressources"""
        # Charger les données avec transition_utils
        savegame = load_savegame_transition()
        market_data = self.data_manager.load_market()
        
        # Trouver l'offre
        offer_data = self._find_offer_by_id(offer_id)
        if not offer_data:
            raise GameValidationError("Offre introuvable")
        
        offer = MarketOffer.from_dict(offer_data)
        
        # Vérifier que l'offre appartient au joueur
        if offer.seller_player_id != player_id:
            raise GameValidationError("Vous ne pouvez pas annuler cette offre")
        
        # Trouver la ville vendeuse
        seller_city = None
        for city in savegame['cities']:
            if city['id'] == offer.seller_city_id:
                seller_city = city
                break
        
        if not seller_city:
            raise GameValidationError("Ville vendeuse introuvable")
        
        # Restituer les ressources
        seller_city['resources'][offer.resource_type] = (
            seller_city['resources'].get(offer.resource_type, 0) + offer.quantity
        )
        
        # Supprimer l'offre
        self._remove_offer_by_id(offer_id)
        
        # Sauvegarder avec optimisation
        save_savegame_transition(savegame, force=False)  # Sauvegarde différée
        self.data_manager.save_market(market_data)
        
        return {
            'success': True,
            'message': f"Offre annulée : {offer.quantity} {offer.resource_type} restituées"
        }

    def get_player_offers(self, player_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les offres d'un joueur"""
        market_data = self.data_manager.load_market()
        
        player_offers = []
        for offer in market_data['offers']:
            if offer['seller_player_id'] == player_id:
                player_offers.append(offer)
        
        return player_offers

    def get_market_capabilities_detailed(self, city_id: str) -> Dict[str, Any]:
        """Récupère les capacités détaillées du marché d'une ville"""
        # Charger les données
        savegame = self.data_manager.load_savegame()
        buildings_data = self.data_manager.load_buildings()
        
        # Trouver la ville
        city = None
        for c in savegame['cities']:
            if c['id'] == city_id:
                city = c
                break
        
        if not city:
            raise GameValidationError("Ville introuvable")
        
        # Vérifier que la ville a un marché
        market_building = None
        for building in city['buildings']:
            if building.get('name', '').lower() == 'market':
                market_building = building
                break
        
        if not market_building:
            return {
                'has_market': False,
                'message': "Cette ville n'a pas de marché"
            }
        
        # Récupérer les capacités réelles depuis buildings.json
        market_level = market_building.get('level', 1)
        market_config = buildings_data.get('Market', {})
        levels = market_config.get('levels', [])
        
        # Trouver la configuration pour ce niveau
        level_config = None
        for level_data in levels:
            if level_data.get('level') == market_level:
                level_config = level_data
                break
        
        if not level_config:
            # Fallback si pas de config trouvée
            market_range = market_level
            total_capacity = market_level * 1000
        else:
            effect = level_config.get('effect', {})
            market_range = effect.get('market_range', market_level)
            total_capacity = effect.get('total_capacity', market_level * 1000)
        
        # Calculer les offres actuelles
        current_offers = len(self.get_player_offers(city['owner']))
        
        return {
            'has_market': True,
            'level': market_level,
            'market_range': market_range,
            'total_capacity': total_capacity,
            'used_capacity': current_offers,
            'available_capacity': total_capacity - current_offers,
            'building_info': market_building
        }

    # ===== MÉTHODES UTILITAIRES =====

    def _find_offer_by_id(self, offer_id: str) -> Optional[Dict[str, Any]]:
        """Trouve une offre par son ID dans market.json"""
        market_data = self.data_manager.load_market()
        
        for offer in market_data['offers']:
            if offer['id'] == offer_id:
                return offer
        
        return None

    def _remove_offer_by_id(self, offer_id: str, buyer_info: Dict[str, Any] = None) -> bool:
        """Supprime une offre par son ID de market.json et l'ajoute à l'historique"""
        market_data = self.data_manager.load_market()
        
        # Initialiser l'historique s'il n'existe pas
        if 'history' not in market_data:
            market_data['history'] = []
        
        for i, offer in enumerate(market_data['offers']):
            if offer['id'] == offer_id:
                # Ajouter des informations de transaction à l'offre pour l'historique
                historical_offer = offer.copy()
                historical_offer['completed_at'] = time.time()
                historical_offer['status'] = 'completed'
                
                # Ajouter les coordonnées du vendeur et de l'acheteur
                if buyer_info:
                    historical_offer['buyer_city_id'] = buyer_info.get('buyer_city_id')
                    historical_offer['buyer_player_id'] = buyer_info.get('buyer_player_id')
                    historical_offer['buyer_coordinates'] = buyer_info.get('buyer_coordinates')
                    historical_offer['transaction_quantity'] = buyer_info.get('quantity')
                    historical_offer['transaction_total_cost'] = buyer_info.get('total_cost')
                
                # Ajouter les coordonnées du vendeur
                historical_offer['seller_coordinates'] = self._get_city_coordinates(offer['seller_city_id'])
                
                # Ajouter à l'historique
                market_data['history'].append(historical_offer)
                
                # Maintenir seulement les 50 dernières transactions
                market_data['history'] = sorted(
                    market_data['history'], 
                    key=lambda x: x.get('completed_at', 0), 
                    reverse=True
                )[:50]
                
                # Supprimer l'offre active
                market_data['offers'].pop(i)
                
                # Mettre à jour les statistiques
                if 'statistics' not in market_data:
                    market_data['statistics'] = {}
                market_data['statistics']['total_transactions'] = market_data['statistics'].get('total_transactions', 0) + 1
                
                # Sauvegarder
                self.data_manager.save_market(market_data)
                return True
        
        return False

    def _update_offer_quantity(self, offer_id: str, new_quantity: int) -> bool:
        """Met à jour la quantité d'une offre dans market.json"""
        market_data = self.data_manager.load_market()
        
        for offer in market_data['offers']:
            if offer['id'] == offer_id:
                offer['quantity'] = new_quantity
                return True
        
        return False

    def _calculate_market_radius(self, market_level: int) -> int:
        """Calcule le rayon d'action selon le niveau du marché"""
        # Charger les données des bâtiments pour avoir la vraie valeur
        try:
            buildings_data = self.data_manager.load_buildings()
            market_config = buildings_data.get('Market', {})
            levels = market_config.get('levels', [])
            
            # Trouver la configuration pour ce niveau
            for level_data in levels:
                if level_data.get('level') == market_level:
                    effect = level_data.get('effect', {})
                    return effect.get('market_range', market_level)
            
            # Fallback si pas de config trouvée
            return market_level
        except:
            # Fallback en cas d'erreur
            return market_level
    
    def _get_city_coordinates(self, city_id: str) -> str:
        """Récupère les coordonnées d'une ville"""
        try:
            savegame = load_savegame_transition()  # Utiliser transition_utils
            return self._get_city_coordinates_cached(None, savegame, city_id)
        except Exception:
            return "Coordonnées inconnues"
    
    def _get_city_coordinates_cached(self, city_dict: Dict[str, Any] = None, 
                                   savegame_data: Dict[str, Any] = None, 
                                   city_id: str = None) -> str:
        """Version optimisée qui utilise les données déjà chargées"""
        try:
            # Si on a déjà le dict de la ville, utiliser ses coordonnées directement
            if city_dict and 'coordinates' in city_dict:
                coords = city_dict['coordinates']
                return f"({coords.get('x', 0)}, {coords.get('y', 0)})"
            
            # Sinon, chercher dans savegame_data si fourni
            if savegame_data and city_id:
                for city in savegame_data.get("cities", []):
                    if city["id"] == city_id and 'coordinates' in city:
                        coords = city['coordinates']
                        return f"({coords.get('x', 0)}, {coords.get('y', 0)})"
            
            # Si on a city_dict mais pas de coordonnées, utiliser son ID pour chercher
            if city_dict and 'id' in city_dict and savegame_data:
                for city in savegame_data.get("cities", []):
                    if city["id"] == city_dict['id'] and 'coordinates' in city:
                        coords = city['coordinates']
                        return f"({coords.get('x', 0)}, {coords.get('y', 0)})"
            
            return "Coordonnées inconnues"
        except Exception:
            return "Coordonnées inconnues"

    def _is_within_market_radius(self, buyer_island_id: str, seller_island_id: str, 
                                radius: int, universe: Dict[str, Any]) -> bool:
        """Vérifie si une île vendeuse est dans le rayon d'action"""
        if buyer_island_id == seller_island_id:
            return True  # Même île, toujours accessible
        
        distance = self._calculate_distance(buyer_island_id, seller_island_id, universe)
        return distance <= radius

    def _calculate_distance(self, island1_id: str, island2_id: str, universe: Dict[str, Any]) -> int:
        """Calcule la distance entre deux îles"""
        island1 = None
        island2 = None
        
        for island in universe['islands']:
            if island['id'] == island1_id:
                island1 = island
            if island['id'] == island2_id:
                island2 = island
        
        if not island1 or not island2:
            return float('inf')  # Distance infinie si île introuvable
        
        # Utiliser coords au lieu de position
        if 'coords' not in island1 or 'coords' not in island2:
            return float('inf')  # Pas de coordonnées disponibles
        
        # Calcul de distance euclidienne avec coefficient d'échelle
        from app.city_constants import TRANSPORT_CONSTANTS
        dx = island1['coords'][0] - island2['coords'][0]
        dy = island1['coords'][1] - island2['coords'][1]
        raw_distance = (dx * dx + dy * dy) ** 0.5
        distance = raw_distance * TRANSPORT_CONSTANTS['DISTANCE_SCALE_FACTOR']
        
        # Arrondir à l'entier supérieur
        return int(distance) + 1
