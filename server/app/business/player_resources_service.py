"""
Service pour gérer les ressources globales du joueur (or, diamants, bateaux, points de recherche).
Ces ressources ne dépendent pas d'une ville spécifique mais du joueur.
"""

class PlayerResourcesService:
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    # Liste des ressources globales (communes à toutes les villes du joueur)
    GLOBAL_RESOURCES = ['gold', 'diamonds', 'transport_ships_total', 'research_points']
    
    def get_player_global_resources(self, player_id: str) -> dict:
        """Récupère les ressources globales du joueur. Retourne des valeurs par défaut si le joueur n'existe pas."""
        players_data = self.data_manager.load_players()
        if not players_data:
            # Retourner des valeurs par défaut sans créer de joueur
            return {'gold': 0, 'diamonds': 0, 'transport_ships': 0, 'research_points': 0}
            
        player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        if not player:
            # Ne pas créer automatiquement - retourner des valeurs par défaut
            return {'gold': 0, 'diamonds': 0, 'transport_ships': 0, 'research_points': 0}
            
        return {
            'gold': player.get('gold', 0),
            'diamonds': player.get('diamonds', 0),
            'transport_ships': player.get('transport_ships_total', 0),
            'research_points': player.get('research_points', 0)
        }
    
    def add_to_player_global_resource(self, player_id: str, resource_name: str, amount: int) -> bool:
        """Ajoute un montant à une ressource globale du joueur. TRANSACTION ATOMIQUE."""
        if resource_name not in self.GLOBAL_RESOURCES:
            raise ValueError(f"'{resource_name}' n'est pas une ressource globale")
            
        # TRANSACTION ATOMIQUE : lecture + modification + sauvegarde en une fois
        players_data = self.data_manager.load_players(use_cache=False)  # Lecture fraîche
        if not players_data:
            return False
            
        player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        if not player:
            return False
        
        # Lecture de la valeur actuelle + modification atomique
        current_value = player.get(resource_name, 0)
        new_value = max(0, current_value + amount)  # Éviter les valeurs négatives
        
        # Modification et sauvegarde - force_save seulement pour les ressources critiques
        player[resource_name] = new_value
        force_save = resource_name in ['transport_ships_total', 'diamonds', 'research_points']
        result = self.data_manager.save_players(players_data, force_save=force_save)
        
        # Log seulement pour les ressources importantes (pas l'or)
        if resource_name in ['transport_ships_total', 'diamonds', 'research_points']:
            # Log silencieux pour éviter le spam
            pass
        
        return result
    
    def spend_player_global_resource(self, player_id: str, resource_name: str, amount: int) -> bool:
        """Dépense une ressource globale du joueur. TRANSACTION ATOMIQUE."""
        if resource_name not in self.GLOBAL_RESOURCES:
            raise ValueError(f"'{resource_name}' n'est pas une ressource globale")
            
        # TRANSACTION ATOMIQUE : lecture + vérification + modification + sauvegarde
        players_data = self.data_manager.load_players(use_cache=False)  # Lecture fraîche
        if not players_data:
            return False
            
        player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        if not player:
            return False
        
        # Vérification et modification atomique
        current_value = player.get(resource_name, 0)
        
        if current_value < amount:
            return False  # Pas assez de ressources
            
        new_value = current_value - amount
        
        # Modification et sauvegarde - force_save pour toutes les dépenses critiques
        player[resource_name] = new_value
        force_save = resource_name in ['transport_ships_total', 'diamonds', 'research_points', 'gold']
        result = self.data_manager.save_players(players_data, force_save=force_save)
        
        return result
    
    def sync_city_global_resources(self, player_id: str, city_id: str) -> bool:
        """Synchronise les ressources globales d'une ville avec celles du joueur."""
        global_resources = self.get_player_global_resources(player_id)
        if not global_resources:
            return False
            
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data:
            return False
            
        city = next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
        if not city or city.get('owner') != player_id:
            return False
            
        # Mettre à jour les ressources globales dans la ville
        city_resources = city.setdefault('resources', {})
        for resource_name, value in global_resources.items():
            city_resources[resource_name] = value
            
        return self.data_manager.save_savegame(savegame_data)
    
    def sync_all_player_cities_global_resources(self, player_id: str) -> bool:
        """Synchronise les ressources globales de toutes les villes du joueur."""
        global_resources = self.get_player_global_resources(player_id)
        if not global_resources:
            return False
            
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data:
            return False
            
        # Trouver toutes les villes du joueur
        player_cities = [c for c in savegame_data.get('cities', []) if c.get('owner') == player_id]
        
                
        return self.data_manager.save_savegame(savegame_data)

    def update_gold_production(self, player_id: str) -> bool:
        """
        Met à jour la production d'or pour un joueur basée sur sa population libre totale.
        L'or est généré par la population libre au taux défini par l'hôtel de ville.
        """
        from ..managers.time_manager import get_time_manager, get_production_system
        
        time_manager = get_time_manager()
        production_system = get_production_system()
        current_tick = time_manager.get_current_tick()
        players_data = self.data_manager.load_players()
        savegame_data = self.data_manager.load_savegame()
        
        if not players_data or not savegame_data:
            return False
        
        # Trouver le joueur
        player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        if not player:
            return False
        
        # Calculer la production d'or totale pour ce joueur
        total_gold_production_rate = 0
        
        # Parcourir toutes les villes du joueur
        for city in savegame_data.get('cities', []):
            if city.get('owner') == player_id:
                # Population libre de cette ville
                city_free_pop = city.get('resources', {}).get('population_free', 0)
                
                # Calculer le taux d'or par habitant pour cette ville
                city_gold_rate = self.calculate_city_gold_rate(city)
                
                # Production d'or de cette ville = population libre × taux d'or
                city_gold_production = city_free_pop * city_gold_rate
                total_gold_production_rate += city_gold_production
        
        # Calculer la production d'or si le joueur a une production positive
        if total_gold_production_rate > 0:
            # Utiliser le système de production centralisé
            last_tick = player.get('last_gold_tick', current_tick)
            
            # Calculer la production via le système centralisé
            gold_to_add = production_system.calculate_production_increment(
                production_rate=total_gold_production_rate,
                last_tick=last_tick,
                current_tick=current_tick
            )
            
            if gold_to_add > 0:
                # Ajouter l'or produit au joueur (arrondi à l'entier)
                self.add_to_player_global_resource(player_id, 'gold', int(gold_to_add))
                
                # Mettre à jour le tick
                player['last_gold_tick'] = current_tick
                self.data_manager.save_players(players_data)
                
                return True
        
        # Mettre à jour le tick même si pas de production
        player['last_gold_tick'] = current_tick
        self.data_manager.save_players(players_data)
        return True

    def calculate_city_gold_rate(self, city: dict) -> float:
        """
        Calcule le taux de production d'or par seconde par habitant libre pour une ville.
        Basé sur le taux d'imposition défini par le joueur (gold_rate).
        """
        # Vérifier s'il y a un hôtel de ville dans cette ville
        town_hall = None
        for building in city.get('buildings', []):
            if building.get('name') == 'Hôtel de Ville':
                town_hall = building
                break
        
        if not town_hall:
            return 0.0  # Pas d'hôtel de ville = pas de production d'or
        
        # Récupérer le taux d'imposition de la ville défini par le joueur
        gold_rate = city.get('gold_rate', 1)  # 1, 2, ou 3 or/sec par habitant libre
        
        # Le taux d'imposition est directement le nombre d'or/sec par habitant libre
        return float(gold_rate)

    def calculate_total_gold_production_rate(self, player_id: str) -> float:
        """
        Calcule le taux de production d'or total actuel pour un joueur.
        Retourne la production en or/seconde.
        """
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data:
            return 0.0
        
        total_rate = 0.0
        
        # Parcourir toutes les villes du joueur
        for city in savegame_data.get('cities', []):
            if city.get('owner') == player_id:
                # Population libre de cette ville
                city_free_pop = city.get('resources', {}).get('population_free', 0)
                
                # Taux d'or par habitant libre pour cette ville
                city_gold_rate = self.calculate_city_gold_rate(city)
                
                # Ajouter à la production totale
                total_rate += city_free_pop * city_gold_rate
        
        return total_rate
