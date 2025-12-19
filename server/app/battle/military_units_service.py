"""
military_units_service.py

Version de compatibilité pour barracks_api.py
Fournit les méthodes essentielles pour la gestion des garnisons
"""

class MilitaryUnitsService:
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def add_units_to_garrison(self, city_id, unit_type, quantity, savegame_data=None):
        """Ajoute des unités à la garnison d'une ville (compatible avec savegame.json racine cities)"""
        try:
            if savegame_data is None:
                savegame_data = self.data_manager.load_savegame()
            # Rechercher la ville directement dans savegame_data['cities']
            city = None
            for city_obj in savegame_data.get('cities', []):
                if city_obj.get('id') == city_id:
                    city = city_obj
                    break
            if not city:
                return False
            # Initialiser la garnison si elle n'existe pas
            if 'military' not in city:
                city['military'] = {}
            if 'garrison' not in city['military']:
                city['military']['garrison'] = {}
            # Ajouter les unités (nouvelle structure: garrison[player_id][unit_type])
            owner_id = city.get("owner")
            if owner_id not in city['military']['garrison']:
                city['military']['garrison'][owner_id] = {}
            
            current_units = city['military']['garrison'][owner_id].get(unit_type, {"quantity": 0}).get("quantity", 0)
            city['military']['garrison'][owner_id][unit_type] = {"quantity": current_units + quantity}
            # Sauvegarder les modifications
            self.data_manager.save_savegame(savegame_data)
            return True
        except Exception as e:
            print(f"Erreur lors de l'ajout d'unités à la garnison: {e}")
            return False
    
    def get_city_garrison(self, city_id):
        """Récupère la garnison d'une ville (compatible avec savegame.json racine cities)"""
        try:
            savegame_data = self.data_manager.load_savegame()
            for city_obj in savegame_data.get('cities', []):
                if city_obj.get('id') == city_id:
                    garrison = city_obj.get('military', {}).get('garrison', {})
                    # Nouvelle structure: garrison[player_id][unit_type][quantity]
                    simplified_garrison = {}
                    for player_id, player_units in garrison.items():
                        if isinstance(player_units, dict):
                            for unit_type, unit_data in player_units.items():
                                if isinstance(unit_data, dict) and 'quantity' in unit_data:
                                    simplified_garrison[unit_type] = simplified_garrison.get(unit_type, 0) + unit_data['quantity']
                    return simplified_garrison
            return {}
        except Exception as e:
            print(f"Erreur lors de la récupération de la garnison: {e}")
            return {}
    
    def remove_units_from_garrison(self, city_id, units_to_remove):
        """Retire des unités de la garnison d'une ville (compatible avec savegame.json racine cities)"""
        try:
            savegame_data = self.data_manager.load_savegame()
            city = None
            for city_obj in savegame_data.get('cities', []):
                if city_obj.get('id') == city_id:
                    city = city_obj
                    break
            if not city:
                return False
            if 'military' not in city:
                return False
            if 'garrison' not in city['military']:
                return False
                
            # Vérifier et retirer les unités (nouvelle structure)
            for unit_type, quantity in units_to_remove.items():
                # Calculer total disponible
                total_available = 0
                for player_id, player_units in city['military']['garrison'].items():
                    if isinstance(player_units, dict) and unit_type in player_units:
                        total_available += player_units[unit_type].get("quantity", 0)
                
                if total_available < quantity:
                    return False  # Pas assez d'unités
                
                # Retirer prioritairement du propriétaire de la ville
                remaining = quantity
                city_owner = city.get("owner")
                
                if city_owner in city['military']['garrison'] and unit_type in city['military']['garrison'][city_owner]:
                    owner_qty = city['military']['garrison'][city_owner][unit_type].get("quantity", 0)
                    remove_from_owner = min(owner_qty, remaining)
                    
                    new_qty = owner_qty - remove_from_owner
                    if new_qty > 0:
                        city['military']['garrison'][city_owner][unit_type]["quantity"] = new_qty
                    else:
                        del city['military']['garrison'][city_owner][unit_type]
                    
                    remaining -= remove_from_owner
                
                # Retirer le reste chez les autres joueurs si nécessaire
                if remaining > 0:
                    for player_id, player_units in city['military']['garrison'].items():
                        if remaining <= 0 or player_id == city_owner:
                            continue
                        if isinstance(player_units, dict) and unit_type in player_units:
                            player_qty = player_units[unit_type].get("quantity", 0)
                            remove_from_player = min(player_qty, remaining)
                            
                            new_qty = player_qty - remove_from_player
                            if new_qty > 0:
                                city['military']['garrison'][player_id][unit_type]["quantity"] = new_qty
                            else:
                                del city['military']['garrison'][player_id][unit_type]
                            
                            remaining -= remove_from_player
            
            # Sauvegarder
            self.data_manager.save_savegame(savegame_data)
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression d'unités: {e}")
            return False
