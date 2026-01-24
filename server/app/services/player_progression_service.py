"""
player_progression_service.py

SERVICE DE CALCUL DE LA PROGRESSION DU JOUEUR

RÔLE:
    Calcule les scores de progression du joueur sur 4 axes:
    - Construction (points basés sur niveaux de bâtiments)
    - Recherche (somme des coûts des recherches débloquées)
    - Militaire (XP, victoires, unités tuées - déjà existant)
    - Puissance Militaire (somme(quantité × xp_value) / 100)

FORMULES:
    Construction: Pour un bâtiment niveau N -> 1+2+3+...+N = N*(N+1)/2
    Recherche: Somme(coût recherches débloquées) + points_recherche_actuels
    Puissance Militaire: sum(quantity × xp_value) / 100 pour toutes les unités

UTILISATION:
    - Appelé après chaque construction/amélioration de bâtiment
    - Appelé après chaque déverrouillage de recherche
    - Appelé sur demande via API pour recalculer tous les scores
"""
import json
import os
from typing import Dict, Any


class PlayerProgressionService:
    """Service de calcul de la progression du joueur"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.base_dir = data_manager.base_dir
    
    def calculate_construction_points(self, player_id: str) -> int:
        """
        Calcule les points de construction d'un joueur.
        Formule: Pour chaque bâtiment niveau N -> somme de 1 à N = N*(N+1)/2
        
        Exemple:
            Bâtiment niveau 1 = 1 point
            Bâtiment niveau 2 = 1+2 = 3 points
            Bâtiment niveau 3 = 1+2+3 = 6 points
        """
        try:
            savegame_data = self.data_manager.load_savegame()
            cities = savegame_data.get('cities', [])
            
            total_points = 0
            
            # Parcourir toutes les villes du joueur
            for city in cities:
                if city.get('owner') != player_id:
                    continue
                
                # Compter les points de chaque bâtiment
                buildings = city.get('buildings', [])
                for building in buildings:
                    level = building.get('level', 0)
                    if level > 0:
                        # Formule triangulaire: n*(n+1)/2
                        points = (level * (level + 1)) // 2
                        total_points += points
            
            return total_points
            
        except Exception as e:
            print(f"Erreur calcul points construction: {e}")
            return 0
    
    def calculate_research_points_invested(self, player_id: str) -> int:
        """
        Calcule le total des points de recherche investis par un joueur.
        = Somme des coûts de toutes les recherches débloquées + points recherche actuels
        """
        try:
            # Charger les données du joueur
            players_data = self.data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
            
            if not player:
                return 0
            
            # Points de recherche actuels
            current_research_points = player.get('research_points', 0)
            
            # Recherches débloquées
            unlocked_research = player.get('unlocked_research', [])
            
            if not unlocked_research:
                return int(current_research_points)
            
            # Charger les données de recherche
            research_file = os.path.join(self.base_dir, 'data', 'research.json')
            with open(research_file, 'r', encoding='utf-8') as f:
                research_data = json.load(f)
            
            researches = research_data.get('researches', [])
            
            # Calculer la somme des coûts des recherches débloquées
            invested_points = 0
            for research_id in unlocked_research:
                research = next((r for r in researches if r.get('id') == research_id), None)
                if research:
                    cost = research.get('cost', {})
                    research_cost = cost.get('research_points', 0)
                    invested_points += research_cost
            
            # Total = investi + points actuels
            total = invested_points + int(current_research_points)
            
            return total
            
        except Exception as e:
            print(f"Erreur calcul points recherche: {e}")
            return 0
    
    def calculate_military_power(self, player_id: str) -> int:
        """
        Calcule la puissance militaire d'un joueur.
        Formule: sum(quantity × xp_value) / 100 pour toutes les unités dans toutes les villes
        
        Returns:
            int: Puissance militaire arrondie
        """
        try:
            # Charger les données nécessaires
            savegame_data = self.data_manager.load_savegame()
            cities = savegame_data.get('cities', [])
            
            # Charger unit_stats.json
            unit_stats_path = os.path.join(self.base_dir, 'data', 'unit_stats.json')
            with open(unit_stats_path, 'r', encoding='utf-8') as f:
                unit_stats_data = json.load(f)
            
            # Créer un dictionnaire de xp_value par type d'unité
            xp_values = {}
            for category in ['classical_age', 'enemy_units']:
                for unit_type, unit_data in unit_stats_data.get(category, {}).items():
                    xp_values[unit_type] = unit_data.get('xp_value', 0)
            
            total_power = 0
            
            # Parcourir toutes les villes
            for city in cities:
                military_data = city.get('military', {})
                garrison = military_data.get('garrison', {})
                
                # Récupérer les unités du joueur dans cette ville
                player_garrison = garrison.get(player_id, {})
                
                # Calculer la puissance pour chaque type d'unité
                for unit_type, unit_data in player_garrison.items():
                    quantity = unit_data.get('quantity', 0)
                    xp_value = xp_values.get(unit_type, 0)
                    total_power += quantity * xp_value
            
            # Diviser par 100 selon la formule
            military_power = int(total_power / 100)
            
            return military_power
            
        except Exception as e:
            print(f"Erreur calcul puissance militaire pour {player_id}: {e}")
            return 0
    
    def get_player_level(self, player_id: str) -> Dict[str, Any]:
        """
        Calcule le niveau global du joueur basé sur ses scores.
        Retourne un dictionnaire avec les scores détaillés.
        """
        try:
            players_data = self.data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
            
            if not player:
                return {
                    'construction_points': 0,
                    'research_points_invested': 0,
                    'military_xp': 0,
                    'military_power': 0,
                    'total_score': 0,
                    'estimated_level': 1
                }
            
            # Calculer les scores
            construction_points = self.calculate_construction_points(player_id)
            research_points_invested = self.calculate_research_points_invested(player_id)
            military_xp = player.get('total_xp_gained', 0)
            military_power = self.calculate_military_power(player_id)
            
            # Score total (pondéré)
            total_score = construction_points + research_points_invested + (military_xp // 10)
            
            # Niveau estimé (grossièrement: 1 niveau par tranche de 100 points)
            estimated_level = max(1, total_score // 100)
            
            return {
                'construction_points': construction_points,
                'research_points_invested': research_points_invested,
                'military_xp': military_xp,
                'military_power': military_power,
                'total_score': total_score,
                'estimated_level': estimated_level,
                'victories': player.get('victories', 0),
                'defeats': player.get('defeats', 0),
                'total_units_killed': player.get('total_units_killed', 0),
                'total_units_lost': player.get('total_units_lost', 0)
            }
            
        except Exception as e:
            print(f"Erreur calcul niveau joueur: {e}")
            return {
                'construction_points': 0,
                'research_points_invested': 0,
                'military_xp': 0,
                'military_power': 0,
                'total_score': 0,
                'estimated_level': 1
            }
    
    def update_player_scores(self, player_id: str) -> Dict[str, Any]:
        """
        Met à jour les scores du joueur dans players.json.
        Retourne les scores calculés.
        """
        try:
            # Calculer les scores
            construction_points = self.calculate_construction_points(player_id)
            research_points_invested = self.calculate_research_points_invested(player_id)
            
            # Mettre à jour dans players.json
            players_data = self.data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
            
            if player:
                player['construction_points'] = construction_points
                player['research_points_invested'] = research_points_invested
                
                # Sauvegarder
                self.data_manager.save_players(players_data, force_save=True)
                
                return {
                    'success': True,
                    'construction_points': construction_points,
                    'research_points_invested': research_points_invested
                }
            else:
                return {
                    'success': False,
                    'message': 'Joueur introuvable'
                }
                
        except Exception as e:
            print(f"Erreur mise à jour scores: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def update_all_players_scores(self):
        """Met à jour les scores de tous les joueurs"""
        try:
            players_data = self.data_manager.load_players()
            players = players_data.get('players', [])
            
            updated_count = 0
            for player in players:
                player_id = player.get('id')
                if player_id:
                    result = self.update_player_scores(player_id)
                    if result.get('success'):
                        updated_count += 1
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_players': len(players)
            }
            
        except Exception as e:
            print(f"Erreur mise à jour globale: {e}")
            return {
                'success': False,
                'message': str(e)
            }
