"""
SERVICE DE GESTION DES RECHERCHES

RÔLE:
    Service métier central pour gérer l'arbre technologique du jeu.
    Gère le déverrouillage des recherches, la validation des prérequis,
    et l'application des effets au niveau JOUEUR (pas ville).

RESPONSABILITÉS:
    1. Vérification des prérequis (recherches préalables, coûts)
    2. Déverrouillage de nouvelles recherches
    3. Application des effets de recherche (bonus ressources, bâtiments, etc.)
    4. Gestion des points de recherche
    5. Notifications de recherches débloquées

ARCHITECTURE:
    - Les recherches sont définies dans data/research.json
    - Les recherches débloquées sont stockées dans players.json (player.unlocked_research)
    - Les effets sont stockés dans players.json (player.research_effects)
    - Les bonus s'appliquent à TOUTES les villes du joueur automatiquement

EFFETS SUPPORTÉS:
    - unlock_building: Débloque un nouveau bâtiment
    - unlock_resources: Débloque de nouvelles ressources
    - resource_bonus: Bonus de production (ex: wood +25%)

POINTS CLÉS:
    - Les bonus sont au niveau JOUEUR, pas au niveau ville
    - Une recherche débloquée affecte toutes les villes actuelles et futures
    - Les coûts sont déduits directement du joueur (research_points, gold)

HISTORIQUE:
    - Refonte majeure : passage des bonus ville → joueur
    - Bug fix : "research_bonus" → "resource_bonus" dans _apply_research_effects()
"""
from typing import Dict, List, Optional, Any
from ..data_manager import DataManager
from .notification_service import NotificationService
from ..models.notification import NotificationType

class ResearchService:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.notification_service = NotificationService(data_manager)
    
    def get_research_by_id(self, research_id: str) -> Optional[Dict]:
        """Récupère les données complètes d'une recherche depuis research.json"""
        research_data = self.data_manager.load_research()
        for research in research_data.get("researches", []):
            if research.get("id") == research_id:
                return research
        return None
        
    def get_player_research(self, player_id: str) -> Dict[str, Any]:
        """Récupère les recherches débloquées par un joueur"""
        players_data = self.data_manager.load_players()
        player = None
        
        for p in players_data.get("players", []):
            if p.get("id") == player_id:
                player = p
                break
        
        if not player:
            return {"unlocked_research": [], "research_points": 0, "research_effects": {}}
            
        return {
            "unlocked_research": player.get("unlocked_research", []),
            "research_points": player.get("research_points", 0),
            "research_effects": player.get("research_effects", {})
        }
    
    def can_unlock_research(self, player_id: str, research_id: str, research_data: Dict) -> Dict[str, Any]:
        """Vérifie si un joueur peut débloquer une recherche"""
        players_data = self.data_manager.load_players()
        player = None
        
        for p in players_data.get("players", []):
            if p.get("id") == player_id:
                player = p
                break
        
        if not player:
            return {"can_unlock": False, "reason": "Joueur introuvable"}
            
        unlocked_research = player.get("unlocked_research", [])
        player_resources = self._get_player_resources(player_id)
        
        # Vérifier si déjà débloquée
        if research_id in unlocked_research:
            return {"can_unlock": False, "reason": "Recherche déjà débloquée"}
            
        # Vérifier les groupes exclusifs
        exclusive_group = research_data.get("exclusive_group")
        if exclusive_group:
            # Charger toutes les recherches pour trouver celles du même groupe
            all_research_data = self.data_manager.load_research()
            all_research_list = all_research_data.get("researches", [])
            
            for other_research in all_research_list:
                other_research_id = other_research.get("id")
                if (other_research.get("exclusive_group") == exclusive_group and 
                    other_research_id in unlocked_research and 
                    other_research_id != research_id):
                    other_name = other_research.get("name", other_research_id)
                    return {
                        "can_unlock": False,
                        "reason": f"Vous avez déjà choisi '{other_name}'. Les spécialisations sont exclusives : vous ne pouvez en choisir qu'une seule."
                    }
            
        # Vérifier les prérequis
        prerequisites = research_data.get("prerequisites", [])
        missing_prerequisites = [req for req in prerequisites if req not in unlocked_research]
        if missing_prerequisites:
            return {
                "can_unlock": False, 
                "reason": f"Prérequis manquants: {', '.join(missing_prerequisites)}"
            }
            
        # Vérifier les coûts
        cost = research_data.get("cost", {})
        missing_resources = []
        
        for resource, required_amount in cost.items():
            available = player_resources.get(resource, 0)
            if available < required_amount:
                missing_resources.append(f"{resource}: {required_amount} (disponible: {available})")
                
        if missing_resources:
            return {
                "can_unlock": False,
                "reason": f"Ressources insuffisantes: {', '.join(missing_resources)}"
            }
            
        return {"can_unlock": True, "reason": "Tous les prérequis sont satisfaits"}
    
    def unlock_research(self, player_id: str, research_id: str, research_data: Dict) -> Dict[str, Any]:
        """Débloque une recherche pour un joueur"""
        # Vérifier si possible
        can_unlock = self.can_unlock_research(player_id, research_id, research_data)
        if not can_unlock["can_unlock"]:
            return {"success": False, "message": can_unlock["reason"]}
        
        players_data = self.data_manager.load_players()
        player = None
        player_index = None
        
        for i, p in enumerate(players_data.get("players", [])):
            if p.get("id") == player_id:
                player = p
                player_index = i
                break
        
        if not player:
            return {"success": False, "message": "Joueur introuvable"}
            
        # Déduire les coûts directement sur l'objet player
        cost = research_data.get("cost", {})
        for resource, amount in cost.items():
            if resource == "research_points":
                current_value = player.get("research_points", 0)
                if current_value < amount:
                    return {"success": False, "message": f"Points de recherche insuffisants ({amount} requis, {current_value} disponibles)"}
                player["research_points"] = current_value - amount
            elif resource == "gold":
                current_value = player.get("gold", 0)
                if current_value < amount:
                    return {"success": False, "message": f"Or insuffisant ({amount} requis, {current_value} disponible)"}
                player["gold"] = current_value - amount
            else:
                # Autres ressources non supportées pour l'instant
                pass
                
        # Ajouter la recherche aux recherches débloquées
        unlocked_research = player.get("unlocked_research", [])
        if research_id not in unlocked_research:
            unlocked_research.append(research_id)
            player["unlocked_research"] = unlocked_research
        
        # Appliquer les effets
        self._apply_research_effects(player, research_data.get("effect", {}))
        
        # Sauvegarder avec force_save pour garantir l'écriture
        players_data["players"][player_index] = player
        save_success = self.data_manager.save_players(players_data, force_save=True)
        
        if not save_success:
            return {
                "success": False,
                "message": f"Erreur lors de la sauvegarde de la recherche '{research_data.get('name', research_id)}'"
            }
        
        # Créer une notification de recherche débloquée
        self._create_research_notification(player_id, research_data.get("name", research_id))
        
        # Utiliser les valeurs modifiées directement depuis l'objet player
        updated_research_points = player.get("research_points", 0)
        
        return {
            "success": True, 
            "message": f"Recherche '{research_data.get('name', research_id)}' débloquée avec succès!",
            "new_research_points": updated_research_points
        }
    
    def _apply_research_effects(self, player: Dict, effects: Dict) -> None:
        """Applique les effets d'une recherche au joueur"""
        if not player:
            print("❌ [RESEARCH] Pas de joueur fourni")
            return
            
        research_effects = player.get("research_effects", {})
        
        # Effet de déverrouillage de bâtiments - Ne plus auto-construire, juste notifier
        # Le joueur devra construire le bâtiment lui-même
        
        # Effet de déverrouillage de ressources
        if "unlock_resources" in effects:
            unlocked_resources = research_effects.get("unlocked_resources", [])
            new_resources = effects["unlock_resources"]
            for resource in new_resources:
                if resource not in unlocked_resources:
                    unlocked_resources.append(resource)
            research_effects["unlocked_resources"] = unlocked_resources
            
        # Bonus de recherche (pourcentages d'amélioration)
        if "resource_bonus" in effects:
            current_bonuses = research_effects.get("resource_bonuses", {})
            new_bonuses = effects["resource_bonus"]
            
            for resource, bonus in new_bonuses.items():
                current_bonuses[resource] = current_bonuses.get(resource, 0) + bonus
                
            research_effects["resource_bonuses"] = current_bonuses
            
        # Autres effets peuvent être ajoutés ici...
        
        player["research_effects"] = research_effects
    
    def is_resource_unlocked(self, player_id: str, resource: str) -> bool:
        """Vérifie si une ressource est débloquée pour un joueur"""
        # Ressources de base toujours disponibles
        basic_resources = [
            "wood", "stone", "iron", "cereal", "papyrus", "gold", 
            "population_total", "population_free", "research_points", 
            "transport_ships", "diamonds"
        ]
        if resource in basic_resources:
            return True
            
        # Mapping des recherches vers les ressources qu'elles débloquent
        research_to_resources = {
            "ressources_avancees": ["marble", "wine", "horse", "glass"],
            "ressources_industrielles": ["coal", "gunpowder", "spices", "cotton"]
        }
        
        # Récupérer les recherches débloquées
        player_research = self.get_player_research(player_id)
        unlocked_research = player_research.get("unlocked_research", [])
        
        # Vérifier si une recherche débloque cette ressource
        for research_name, resources in research_to_resources.items():
            if research_name in unlocked_research and resource in resources:
                return True
        
        # Fallback : vérifier les research_effects (pour compatibilité)
        unlocked_resources = player_research.get("research_effects", {}).get("unlocked_resources", [])
        return resource in unlocked_resources
    
    def can_assign_workers_to_resource_sites(self, player_id: str) -> bool:
        """Vérifie si le joueur peut assigner des ouvriers aux sites de ressources"""
        # Récupérer les recherches débloquées
        player_research = self.get_player_research(player_id)
        unlocked_research = player_research.get("unlocked_research", [])
        
        # Vérifier si "acces_ressources" est débloqué
        return "acces_ressources" in unlocked_research
    
    def _get_player_resources(self, player_id: str) -> Dict[str, int]:
        """Récupère les vraies ressources d'un joueur depuis ses villes"""
        players_data = self.data_manager.load_players()
        savegame_data = self.data_manager.load_savegame()
        
        player = None
        for p in players_data.get("players", []):
            if p.get("id") == player_id:
                player = p
                break
        
        if not player or not savegame_data:
            return {}
        
        # Récupérer les ressources réelles depuis les villes du joueur
        total_resources = {
            "research_points": player.get("research_points", 0),
            "gold": player.get("gold", 0),  # L'or est stocké au niveau joueur
            "wood": 0,
            "stone": 0,
            "iron": 0,
            "cereal": 0,
            "papyrus": 0,
            "horse": 0,
            "marble": 0,
            "glass": 0,
            "wine": 0,
            "coal": 0,
            "gunpowder": 0,
            "spices": 0,
            "cotton": 0
        }
        
        # Additionner les ressources de toutes les villes du joueur
        player_cities = [city for city in savegame_data.get('cities', []) if city.get('owner') == player_id]
        
        for city in player_cities:
            city_resources = city.get('resources', {})
            for resource in total_resources:
                if resource not in ["research_points", "gold"]:  # Points de recherche et or viennent du player, pas des villes
                    total_resources[resource] += city_resources.get(resource, 0)
        
        return total_resources
    
    def get_player_research_points(self, player_id: str) -> int:
        """Récupère les points de recherche d'un joueur avec mise à jour contrôlée"""
        import time
        
        # Mettre à jour la production, mais avec protection contre appels trop fréquents
        try:
            from ..game_logic import GameLogic
            game_logic = GameLogic(self.data_manager)
            
            # Vérifier le timestamp de dernière mise à jour pour éviter les mises à jour trop fréquentes
            players_data = self.data_manager.load_players()
            if players_data:
                player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
                if player:
                    # game_logic.update_research_points_production()  # DÉSACTIVÉ - Utilisation du système de tick manuel
                    pass
                        
        except Exception as e:
            print(f"Erreur lors de la mise à jour des points de recherche: {e}")
        
        # Charger les données des joueurs
        players_data = self.data_manager.load_players()
        if not players_data:
            return 0
        
        # Trouver le joueur
        player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        if not player:
            return 0
        
        # Retourner les points de recherche (0 par défaut)
        return player.get('research_points', 0)
    
    def _create_research_notification(self, player_id: str, research_name: str):
        """Crée une notification pour le déverrouillage d'une recherche"""
        try:
            self.notification_service.create_research_notification(
                player_id=player_id,
                research_name=research_name
            )
        except Exception as e:
            print(f"Erreur lors de la création de la notification de recherche: {e}")
            import traceback
            traceback.print_exc()

