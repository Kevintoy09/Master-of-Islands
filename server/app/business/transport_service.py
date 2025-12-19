"""
TRANSPORT_SERVICE.PY - Service principal pour la gestion des transports
======================================================================

RESPONSABILITÉS:
- Création et validation des transports
- Gestion des états et transitions
- Calculs de distance et temps  
- Déduction/crédit des ressources
- Gestion des files d'attente de chargement
- Archivage des transports terminés

ÉTATS DES TRANSPORTS:
- waiting: En attente (port occupé)
- loading: Chargement en cours
- traveling: En voyage vers destination
- returning: Retour vers origine (si cross-player)
- completed: Terminé (sera archivé)

LOGIQUE MÉTIER:
- Un seul chargement par port à la fois
- File d'attente FIFO par ville source
- Cross-player = retour obligatoire
- Same-player = pas de retour
======================================================================
"""

import time
import math
import uuid
from typing import Dict, List, Any, Optional, Tuple
from app.data_manager import DataManager
from app.city_constants import TRANSPORT_CONSTANTS

class TransportService:
    
    TRANSPORT_STATES = {
        'WAITING': 'waiting',
        'LOADING': 'loading', 
        'TRAVELING': 'traveling',
        'RETURNING': 'returning',
        'COMPLETED': 'completed'
    }
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        
    # ========================================
    # CRÉATION DE TRANSPORT
    # ========================================
    
    def create_transport(self, player_id: str, source_city_id: str, destination_city_id: str, 
                        resources: Dict[str, int], ships_needed: int, 
                        loading_time: float, travel_time: float, transport_type: str = "resources",
                        battlefield_template_id: str = None) -> Dict[str, Any]:
        """
        Crée un nouveau transport avec toutes les validations.
        
        Returns: {"success": bool, "transport_id": str, "message": str}
        """
        try:
            # 1. VALIDATIONS CRITIQUES
            validation_result = self._validate_transport_creation(
                player_id, source_city_id, destination_city_id, resources, ships_needed
            )
            if not validation_result['valid']:
                return {"success": False, "error": validation_result['error']}
            
            # 2. DÉTERMINER LE JOUEUR DE DESTINATION
            destination_player_id = self._get_city_owner(destination_city_id)
            is_cross_player = (player_id != destination_player_id)
            
            # 3. CRÉER L'OBJET TRANSPORT  
            transport_id = self._generate_transport_id()
            current_time = round(time.time(), 2)
            
            transport = {
                "id": transport_id,
                "source_player_id": player_id,
                "source_city": source_city_id,
                "destination_city": destination_city_id,
                "destination_player_id": destination_player_id,
                "resources": resources,
                "ships_needed": ships_needed,
                "status": self.TRANSPORT_STATES['WAITING'],  # Par défaut en attente
                "created_at": current_time,
                "loading_time": round(loading_time, 2),
                "travel_time": round(travel_time, 2),
                "remaining_time": round(loading_time, 2),  # Commence par le temps de chargement
                "last_update": current_time,  # Timestamp pour calcul temps écoulé
                "is_cross_player": is_cross_player,
                "transport_type": transport_type,  # Nouveau : type de transport (resources/movement/attack)
                "battlefield_template_id": battlefield_template_id,  # Pour les attaques
                "timeline": {
                    "created": current_time,
                    "loading_start": None,
                    "loading_end": None,
                    "travel_start": None,
                    "travel_end": None,
                    "return_start": None,
                    "return_end": None,
                    "completed": None
                }
            }
            
            # 4. RÉSERVATIONS (déduction ressources + bateaux occupés)
            if not self._make_transport_reservations(player_id, source_city_id, resources, ships_needed):
                return {"success": False, "error": "Erreur lors des réservations"}
            
            # 5. GESTION FILE D'ATTENTE / DÉMARRAGE IMMÉDIAT
            if self._is_port_free(source_city_id):
                # Port libre = démarrage immédiat
                transport["status"] = self.TRANSPORT_STATES['LOADING']
                transport["timeline"]["loading_start"] = current_time
                transport["last_update"] = current_time  # Synchroniser avec loading_start
            else:
                # Port occupé = en attente
                transport["status"] = self.TRANSPORT_STATES['WAITING']
            
            # 6. SAUVEGARDE
            self._save_transport(transport)
            
            return {
                "success": True,
                "transport_id": transport_id,
                "message": f"Transport créé avec succès ({'chargement immédiat' if transport['status'] == 'loading' else 'mis en attente'})"
            }
            
        except Exception as e:
            print(f"❌ Erreur création transport: {e}")
            return {"success": False, "error": f"Erreur système: {str(e)}"}
    
    # ========================================
    # VALIDATIONS
    # ========================================
    
    def _validate_transport_creation(self, player_id: str, source_city_id: str, 
                                   destination_city_id: str, resources: Dict[str, int], 
                                   ships_needed: int) -> Dict[str, Any]:
        """Valide tous les prérequis pour créer un transport."""
        
        # 1. Vérifier que les villes existent
        if not self._city_exists(source_city_id) or not self._city_exists(destination_city_id):
            return {"valid": False, "error": "Une ou plusieurs villes n'existent pas"}
        
        # 2. Vérifier propriété ville source
        if not self._player_owns_city(player_id, source_city_id):
            return {"valid": False, "error": "Vous ne possédez pas la ville source"}
        
        # 3. Vérifier ressources disponibles
        available_resources = self._get_city_resources(source_city_id)
        for resource, amount in resources.items():
            if available_resources.get(resource, 0) < amount:
                return {"valid": False, "error": f"Pas assez de {resource} dans la ville source"}
        
        # 4. Vérifier bateaux disponibles
        player_ships = self._get_player_ships_info(player_id)
        if player_ships['available'] < ships_needed:
            return {"valid": False, "error": f"Pas assez de bateaux disponibles ({ships_needed} requis, {player_ships['available']} disponibles)"}
        
        return {"valid": True}
    
    # ========================================
    # GESTION DES RESSOURCES ET BATEAUX
    # ========================================
    
    def _make_transport_reservations(self, player_id: str, source_city_id: str, 
                                   resources: Dict[str, int], ships_needed: int) -> bool:
        """Effectue les déductions de ressources et marque les bateaux comme occupés."""
        try:
            # 1. Déduire ressources de la ville source
            if not self._deduct_city_resources(source_city_id, resources):
                return False
            
            # 2. Marquer bateaux comme occupés
            if not self._increment_ships_busy(player_id, ships_needed):
                # Rollback ressources en cas d'échec
                self._add_city_resources(source_city_id, resources)
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur réservations: {e}")
            return False
    
    # ========================================
    # HELPER METHODS (à implémenter)
    # ========================================
    
    def _generate_transport_id(self) -> str:
        """Génère un ID unique pour le transport."""
        # Pour l'instant, UUID simple - à améliorer avec compteur
        return f"transport_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def _city_exists(self, city_id: str) -> bool:
        """Vérifie qu'une ville existe."""
        try:
            # Gestion spéciale pour les villages barbares
            if city_id.startswith('wild_camp_'):
                # Les villages barbares sont virtuels mais valides
                island_id = city_id.replace('wild_camp_', '')
                # Vérifier que l'île existe
                universe = self.data_manager.load_universe()
                islands = universe.get('islands', [])
                return any(island.get('id') == island_id for island in islands)
            
            # Vérification normale pour les villes
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            return any(c.get('id') == city_id for c in cities)
        except Exception as e:
            print(f"❌ Erreur vérification existence ville {city_id}: {e}")
            return False
    
    def _player_owns_city(self, player_id: str, city_id: str) -> bool:
        """Vérifie qu'un joueur possède une ville."""
        try:
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == city_id), None)
            return city is not None and city.get('owner') == player_id
        except Exception as e:
            print(f"❌ Erreur vérification propriété ville {city_id}: {e}")
            return False
    
    def _get_city_owner(self, city_id: str) -> str:
        """Récupère le propriétaire d'une ville."""
        try:
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == city_id), None)
            return city.get('owner') if city else None
        except Exception as e:
            print(f"❌ Erreur récupération propriétaire ville {city_id}: {e}")
            return None
    
    def _get_city_resources(self, city_id: str) -> Dict[str, int]:
        """Récupère les ressources ET les unités d'une ville."""
        try:
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == city_id), None)
            if city:
                resources = city.get('resources', {}).copy()  # Ressources normales
                
                # Ajouter les unités avec le préfixe "unit_" (nouvelle structure)
                garrison = city.get('military', {}).get('garrison', {})
                for player_id, player_units in garrison.items():
                    if isinstance(player_units, dict):
                        for unit_type, unit_data in player_units.items():
                            if isinstance(unit_data, dict) and 'quantity' in unit_data:
                                current_qty = resources.get(f"unit_{unit_type}", 0)
                                resources[f"unit_{unit_type}"] = current_qty + unit_data.get('quantity', 0)
                
                return resources
            return {}
        except Exception as e:
            print(f"❌ Erreur récupération ressources ville {city_id}: {e}")
            return {}
    
    def _get_player_ships_info(self, player_id: str) -> Dict[str, int]:
        """Récupère les informations sur les bateaux du joueur."""
        try:
            players_data = self.data_manager.load_players()
            players = players_data.get('players', [])
            player = next((p for p in players if p.get('id') == player_id), None)
            
            if not player:
                print(f"❌ Joueur {player_id} non trouvé pour infos vaisseaux")
                return {'total': 0, 'busy': 0, 'available': 0}
            
            # Initialiser les bateaux de transport s'ils n'existent pas
            if 'transport_ships_total' not in player:
                player['transport_ships_total'] = 5  # Valeur par défaut
                player['transport_ships_busy'] = 0
                self.data_manager.save_players(players_data)
            
            # Récupérer les données de vaisseaux
            transport_ships_total = player.get('transport_ships_total', 5)
            transport_ships_busy = player.get('transport_ships_busy', 0)
            transport_ships_available = transport_ships_total - transport_ships_busy
            
            return {
                'total': transport_ships_total,
                'busy': transport_ships_busy,
                'available': max(0, transport_ships_available)
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération infos vaisseaux joueur {player_id}: {e}")
            return {'total': 0, 'busy': 0, 'available': 0}
    
    def _deduct_city_resources(self, city_id: str, resources: Dict[str, int]) -> bool:
        """Déduit des ressources d'une ville."""
        try:
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == city_id), None)
            
            if not city:
                print(f"❌ Ville {city_id} non trouvée pour déduction ressources")
                return False
            
            city_resources = city.get('resources', {})
            
            # Vérifier suffisamment de ressources et déduire
            city_garrison = city.get('military', {}).get('garrison', {})
            
            for resource_type, amount in resources.items():
                if amount > 0:  # Ignorer les ressources à 0
                    # Gérer les unités (préfixées par "unit_") - nouvelle structure
                    if resource_type.startswith("unit_"):
                        unit_type = resource_type[5:]  # Enlever "unit_" du début
                        
                        # Calculer total disponible
                        total_available = 0
                        for player_id, player_units in city_garrison.items():
                            if isinstance(player_units, dict) and unit_type in player_units:
                                total_available += player_units[unit_type].get('quantity', 0)
                        
                        if total_available < amount:
                            print(f"❌ Pas assez de {unit_type} dans {city_id}: {total_available} < {amount}")
                            return False
                        
                        # Déduire (priorité au propriétaire de la ville)
                        remaining = amount
                        city_owner = city.get('owner')
                        
                        if city_owner in city_garrison and unit_type in city_garrison[city_owner]:
                            owner_qty = city_garrison[city_owner][unit_type].get('quantity', 0)
                            deduct_owner = min(owner_qty, remaining)
                            city_garrison[city_owner][unit_type]['quantity'] -= deduct_owner
                            if city_garrison[city_owner][unit_type]['quantity'] <= 0:
                                del city_garrison[city_owner][unit_type]
                            remaining -= deduct_owner
                        
                        # Déduire le reste chez les autres si nécessaire
                        if remaining > 0:
                            for player_id, player_units in city_garrison.items():
                                if remaining <= 0 or player_id == city_owner:
                                    continue
                                if isinstance(player_units, dict) and unit_type in player_units:
                                    player_qty = player_units[unit_type].get('quantity', 0)
                                    deduct = min(player_qty, remaining)
                                    city_garrison[player_id][unit_type]['quantity'] -= deduct
                                    if city_garrison[player_id][unit_type]['quantity'] <= 0:
                                        del city_garrison[player_id][unit_type]
                                    remaining -= deduct
                        
                        print(f"✅ Déduit {amount} {unit_type} de {city_id}")
                    else:
                        # Gérer les ressources normales
                        current_amount = city_resources.get(resource_type, 0)
                        if current_amount < amount:
                            print(f"❌ Pas assez de {resource_type} dans {city_id}: {current_amount} < {amount}")
                            return False
                        city_resources[resource_type] = current_amount - amount
            
            # Sauvegarder avec force_save=True pour éviter le throttling
            return self.data_manager.save_savegame(savegame, force_save=True)
                
        except Exception as e:
            print(f"❌ Erreur déduction ressources ville {city_id}: {e}")
            return False
    
    def _add_city_resources(self, city_id: str, resources: Dict[str, int]) -> bool:
        """Ajoute des ressources à une ville."""
        try:
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == city_id), None)
            
            if not city:
                print(f"❌ Ville {city_id} non trouvée pour crédit ressources")
                return False
            
            city_resources = city.get('resources', {})
            
            # Ajouter les ressources ET les unités
            city_garrison = city.get('military', {}).get('garrison', {})
            
            for resource_type, amount in resources.items():
                if amount > 0:  # Ignorer les ressources à 0
                    # Gérer les unités (préfixées par "unit_") - nouvelle structure
                    if resource_type.startswith("unit_"):
                        unit_type = resource_type[5:]  # Enlever "unit_" du début
                        city_owner = city.get('owner') or city.get('ownerId', 'unknown')
                        
                        # Initialiser le groupe du propriétaire si nécessaire
                        if city_owner not in city_garrison:
                            city_garrison[city_owner] = {}
                        
                        # Ajouter au propriétaire
                        if unit_type in city_garrison[city_owner]:
                            city_garrison[city_owner][unit_type]['quantity'] += amount
                        else:
                            city_garrison[city_owner][unit_type] = {
                                'quantity': amount
                            }
                        print(f"✅ Ajouté {amount} {unit_type} à {city_id}")
                    else:
                        # Gérer les ressources normales
                        current_amount = city_resources.get(resource_type, 0)
                        city_resources[resource_type] = current_amount + amount
            
            # Sauvegarder
            return self.data_manager.save_savegame(savegame)
                
        except Exception as e:
            print(f"❌ Erreur crédit ressources ville {city_id}: {e}")
            return False
    
    def _increment_ships_busy(self, player_id: str, ships_count: int) -> bool:
        """Marque des bateaux comme occupés."""
        try:
            players_data = self.data_manager.load_players()
            players = players_data.get('players', [])
            player = next((p for p in players if p.get('id') == player_id), None)
            
            if not player:
                print(f"❌ Joueur {player_id} non trouvé pour incrémenter bateaux occupés")
                return False
            
            # Initialiser si nécessaire
            if 'transport_ships_busy' not in player:
                player['transport_ships_busy'] = 0
            
            # Incrémenter le nombre de bateaux occupés
            current_busy = player.get('transport_ships_busy', 0)
            player['transport_ships_busy'] = current_busy + ships_count
            
            # Sauvegarder avec force_save pour éviter le throttling
            return self.data_manager.save_players(players_data, force_save=True)
                
        except Exception as e:
            print(f"❌ Erreur incrément bateaux occupés joueur {player_id}: {e}")
            return False
    
    def _is_port_free(self, city_id: str) -> bool:
        """Vérifie si le port d'une ville est libre (pas de chargement en cours)."""
        try:
            transports_data = self.data_manager.load_transports()
            
            # Chercher s'il y a déjà un transport en "loading" depuis cette ville
            for transport in transports_data.get('transports', []):
                if (transport.get('source_city') == city_id and 
                    transport.get('status') == self.TRANSPORT_STATES['LOADING']):
                    return False  # Port occupé
            
            return True  # Port libre
            
        except Exception as e:
            print(f"❌ Erreur vérification port libre: {e}")
            return True  # En cas d'erreur, supposer libre
    
    def _save_transport(self, transport: Dict[str, Any]) -> bool:
        """Sauvegarde un transport dans transports.json."""
        try:
            transports_data = self.data_manager.load_transports()
            transports_data["transports"].append(transport)
            return self.data_manager.save_transports(transports_data, force_save=True)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde transport: {e}")
            return False


            return 'unknown'


