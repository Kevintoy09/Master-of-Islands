"""
Wall Group Manager
==================

Gère le système de groupement des murs selon le niveau de la muraille.
- Analyse les cartes battlefield pour identifier les lignes de murs
- Divise les murs en sections selon nb_element du bâtiment
- Assigne les HP par section au lieu de par case individuelle
"""

import json
import os
from typing import Dict, List, Tuple, Any


class WallGroupManager:
    """Gestionnaire des groupes de murs pour le système de fortification"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.buildings_data = self._load_buildings_data()
    
    def _load_buildings_data(self) -> Dict[str, Any]:
        """Charge les données des bâtiments"""
        buildings_path = os.path.join(self.data_dir, 'buildings.json')
        try:
            with open(buildings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement buildings.json: {e}")
            return {}
    
    def get_wall_stats(self, wall_level: int) -> Dict[str, Any]:
        """Récupère les stats d'un niveau de muraille"""
        muraille_data = self.buildings_data.get('Muraille', {})
        levels = muraille_data.get('levels', [])
        
        if 1 <= wall_level <= len(levels):
            return levels[wall_level - 1]['effect']
        return {}
    
    def find_wall_lines(self, hex_map: List[str]) -> List[List[Tuple[int, int]]]:
        """
        Trouve toutes les lignes de murs connectés dans la carte
        
        Returns:
            List des lignes de murs, chaque ligne est une liste de coordonnées (row, col)
        """
        if not hex_map:
            return []
        
        height = len(hex_map)
        width = len(hex_map[0]) if height > 0 else 0
        visited = set()
        wall_lines = []
        
        def get_neighbors(row: int, col: int) -> List[Tuple[int, int]]:
            """Retourne les voisins hexagonaux d'une case"""
            neighbors = []
            # Hexagonal adjacency (simplified for string grid)
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]
            
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    neighbors.append((nr, nc))
            return neighbors
        
        def dfs_wall_line(start_row: int, start_col: int) -> List[Tuple[int, int]]:
            """DFS pour trouver une ligne de murs connectés"""
            line = []
            stack = [(start_row, start_col)]
            
            while stack:
                row, col = stack.pop()
                if (row, col) in visited:
                    continue
                    
                if row < 0 or row >= height or col < 0 or col >= width:
                    continue
                    
                if hex_map[row][col] != 'W':
                    continue
                
                visited.add((row, col))
                line.append((row, col))
                
                # Ajouter les voisins murs
                for nr, nc in get_neighbors(row, col):
                    if (nr, nc) not in visited and hex_map[nr][nc] == 'W':
                        stack.append((nr, nc))
            
            return sorted(line)  # Trier pour cohérence
        
        # Parcourir toutes les cases pour trouver les murs
        for row in range(height):
            for col in range(width):
                if hex_map[row][col] == 'W' and (row, col) not in visited:
                    wall_line = dfs_wall_line(row, col)
                    if wall_line:
                        wall_lines.append(wall_line)
        
        return wall_lines
    
    def create_wall_groups(self, wall_lines: List[List[Tuple[int, int]]], wall_level: int) -> Dict[str, Any]:
        """
        Crée les groupes de murs selon le niveau de muraille
        Divise TOUTES les positions de murs en groupes équilibrés
        
        Args:
            wall_lines: Liste des lignes de murs continues
            wall_level: Niveau du bâtiment muraille
            
        Returns:
            Dict avec les groupes de murs et leurs HP
        """
        wall_stats = self.get_wall_stats(wall_level)
        nb_element = wall_stats.get('nb_element', 1)
        wall_hp = wall_stats.get('wall_hp', 100)
        
        if not wall_lines:
            return {}
        
        # 🔥 NOUVELLE APPROCHE : Collecter TOUTES les positions et les diviser équitablement
        all_wall_positions = []
        for wall_line in wall_lines:
            if wall_line:
                all_wall_positions.extend(wall_line)
        
        if not all_wall_positions:
            return {}
        
        total_positions = len(all_wall_positions)
        wall_groups = {}
        
        # Calculer la taille de chaque groupe (répartition équilibrée)
        positions_per_group = total_positions // nb_element
        remainder = total_positions % nb_element
        
        current_index = 0
        
        for group_idx in range(nb_element):
            # Calculer la taille de ce groupe (certains groupes prennent 1 position supplémentaire du reste)
            group_size = positions_per_group
            if group_idx < remainder:
                group_size += 1
            
            # Extraire les positions pour ce groupe
            group_positions = all_wall_positions[current_index:current_index + group_size]
            current_index += group_size
            
            if group_positions:
                group_key = f"wall_group_{group_idx}"
                wall_groups[group_key] = {
                    "positions": group_positions,  # Format compact géré par battle_creation_service_v2
                    "hp": wall_hp,                 # Seule donnée dynamique
                    "wall_level": wall_level       # Niveau pour calculer stats/max_hp
                }
        
        return wall_groups
    
    def _load_template_hex_map(self, battlefield_template_id: str) -> list:
        """Charge le hexMap depuis le template de battlefield"""
        try:
            template_path = os.path.join(self.data_dir, 'battlefields', f'{battlefield_template_id}.json')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                return template_data.get('hexMap', [])
        except Exception as e:
            print(f"❌ Erreur chargement hexMap du template {battlefield_template_id}: {e}")
        return []
    
    def initialize_battlefield_walls(self, battlefield_template_id: str, wall_level: int) -> Dict[str, Any]:
        """
        Initialise les murs d'un battlefield avec le système de groupes
        
        Args:
            battlefield_template_id: ID du template de battlefield
            wall_level: Niveau du bâtiment muraille
            
        Returns:
            Dict avec les données de murs initialisées
        """
        # ✅ Charger le hexMap depuis le template (pas de copie)
        hex_map = self._load_template_hex_map(battlefield_template_id)
        if not hex_map:
            return {}
        
        # Trouver les lignes de murs
        wall_lines = self.find_wall_lines(hex_map)
        
        # Créer les groupes de murs
        wall_groups = self.create_wall_groups(wall_lines, wall_level)
        

        
        return {
            "wall_groups": wall_groups
            # wall_stats supprimées - calculables dynamiquement depuis wall_level
        }
    
    def get_max_hp(self, wall_level: int) -> int:
        """Calcule les HP max d'un groupe de murs selon son niveau"""
        wall_stats = self.get_wall_stats(wall_level)
        return wall_stats.get('wall_hp', 100)
    
    def is_wall_group_destroyed(self, wall_group: Dict[str, Any]) -> bool:
        """Vérifie si un groupe de murs est détruit (HP <= 0)"""
        return wall_group.get('hp', 0) <= 0
    
    def get_wall_defense(self, wall_level: int) -> int:
        """Récupère la défense d'un mur selon son niveau"""
        wall_stats = self.get_wall_stats(wall_level)
        return wall_stats.get('defense', 50)
    
    def get_wall_attack_ranged(self, wall_level: int) -> int:
        """Récupère l'attaque à distance d'un mur selon son niveau"""
        wall_stats = self.get_wall_stats(wall_level)
        return wall_stats.get('attack_ranged', 25)
    
    def get_wall_range(self, wall_level: int) -> int:
        """Récupère la portée d'un mur selon son niveau"""
        wall_stats = self.get_wall_stats(wall_level)
        return wall_stats.get('range', 2)

    def can_pass_through_wall(self, wall_groups: Dict[str, Any], position: Tuple[int, int]) -> bool:
        """
        Vérifie si on peut passer par une position de mur
        
        Args:
            wall_groups: Données des groupes de murs
            position: Position (row, col) à vérifier
            
        Returns:
            True si on peut passer (groupe détruit), False sinon
        """
        for group_key, group_data in wall_groups.items():
            positions = group_data.get('positions', [])
            if position in positions:
                # Si cette position fait partie d'un groupe encore vivant
                return group_data.get('hp', 0) <= 0
        
        # Si la position n'est pas dans un groupe de murs, on peut passer
        return True
    
    def damage_wall_at_position(self, wall_groups: Dict[str, Any], position: Tuple[int, int], damage: int) -> Dict[str, Any]:
        """
        Applique des dégâts à un groupe de murs à une position donnée
        
        Args:
            wall_groups: Données des groupes de murs
            position: Position attaquée
            damage: Dégâts à appliquer
            
        Returns:
            Dict avec le résultat de l'attaque
        """
        for group_key, group_data in wall_groups.items():
            positions = group_data.get('positions', [])
            if position in positions:
                current_hp = group_data.get('hp', 0)
                new_hp = max(0, current_hp - damage)
                group_data['hp'] = new_hp
                
                return {
                    "success": True,
                    "group_key": group_key,
                    "damage_dealt": damage,
                    "remaining_hp": new_hp,
                    "destroyed": new_hp <= 0,
                    "affected_positions": positions
                }
        
        return {
            "success": False,
            "message": "Aucun groupe de murs trouvé à cette position"
        }


def get_wall_group_manager(data_dir: str = None) -> WallGroupManager:
    """Factory function pour obtenir une instance du gestionnaire"""
    if data_dir is None:
        # Default path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, '..', '..', 'data')
    
    return WallGroupManager(data_dir)