"""
Service de gestion des notifications
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.notification import Notification, NotificationType
from ..data_manager import DataManager

class NotificationService:
    """Service pour gérer les notifications des joueurs"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def create_transport_notification(
        self, 
        player_id: str, 
        from_city: str, 
        to_city: str, 
        resources
    ) -> str:
        """Créer une notification d'arrivée de transport"""
        # Gérer différents formats de ressources
        if isinstance(resources, dict):
            # Convertir le dictionnaire en string lisible
            resources_list = []
            for resource_name, quantity in resources.items():
                if quantity > 0:
                    resources_list.append(f"{quantity} {resource_name}")
            resources_text = " et ".join(resources_list) if resources_list else "aucune ressource"
        else:
            # Si c'est déjà une string, l'utiliser directement
            resources_text = str(resources)
        
        notification = Notification(
            player_id=player_id,
            type=NotificationType.TRANSPORT_ARRIVED,
            title="Transport arrivé",
            message=f"Transport de {from_city} vers {to_city} arrivé à destination",
            details={
                "from": from_city,
                "to": to_city,
                "resources": resources_text
            }
        )
        
        return self._save_notification(notification)
    
    def create_market_purchase_notification(
        self, 
        player_id: str, 
        resources: Dict[str, int], 
        total_cost: float, 
        seller_city: str
    ) -> str:
        """Créer une notification d'achat sur le marché"""
        # Convertir les ressources en texte lisible
        resources_list = []
        for resource_name, quantity in resources.items():
            if quantity > 0:
                resources_list.append(f"{quantity} {resource_name}")
        resources_text = " et ".join(resources_list) if resources_list else "aucune ressource"
        
        notification = Notification(
            player_id=player_id,
            type=NotificationType.MARKET_PURCHASE,
            title="Achat sur le marché",
            message=f"Achat réussi: {resources_text} pour {total_cost} or",
            details={
                "resources": resources_text,
                "cost": total_cost,
                "seller_city": seller_city
            }
        )
        
        return self._save_notification(notification)
    
    def create_market_sale_notification(
        self, 
        player_id: str, 
        resource: str, 
        quantity: int, 
        total_earned: float, 
        buyer_city: str
    ) -> str:
        """Créer une notification de vente sur le marché"""
        notification = Notification(
            player_id=player_id,
            type=NotificationType.MARKET_SALE,
            title="Vente sur le marché",
            message=f"Vente réussie: {quantity} {resource} pour {total_earned} or",
            details={
                "resource": resource,
                "quantity": quantity,
                "earned": total_earned,
                "buyer_city": buyer_city
            }
        )
        
        return self._save_notification(notification)
    
    def create_building_notification(
        self, 
        player_id: str, 
        building_name: str, 
        city_name: str
    ) -> str:
        """Créer une notification de fin de construction"""
        notification = Notification(
            player_id=player_id,
            type=NotificationType.BUILDING_COMPLETED,
            title="Construction terminée",
            message=f"{building_name} terminé dans {city_name}",
            details={
                "building_name": building_name,
                "city_name": city_name
            }
        )
        
        return self._save_notification(notification)
    
    def create_research_notification(
        self, 
        player_id: str, 
        research_name: str
    ) -> str:
        """Créer une notification de recherche débloquée"""
        notification = Notification(
            player_id=player_id,
            type=NotificationType.RESEARCH_COMPLETED,
            title="Recherche débloquée",
            message=f"Recherche '{research_name}' terminée",
            details={
                "research_name": research_name
            }
        )
        
        return self._save_notification(notification)
    
    def create_missing_building_notifications(self, player_id: str) -> List[str]:
        """Créer des notifications pour tous les bâtiments terminés qui n'en ont pas"""
        created_notifications = []
        
        try:
            # Récupérer toutes les notifications de bâtiment existantes
            existing_notifications = self.get_player_notifications(player_id, limit=1000)
            existing_building_notifications = set()
            
            for notif in existing_notifications:
                if (notif.get('type') == 'batiment' and 
                    'details' in notif and 
                    'building_name' in notif['details'] and 
                    'city_name' in notif['details']):
                    key = f"{notif['details']['building_name']}:{notif['details']['city_name']}"
                    existing_building_notifications.add(key)
            
            # Récupérer toutes les villes du joueur
            savegame_data = self.data_manager.load_savegame()
            cities = savegame_data.get('cities', [])
            
            for city in cities:
                if city.get('owner') != player_id:
                    continue
                    
                city_name = city.get('name', 'Ville')
                buildings = city.get('buildings', [])
                
                for building in buildings:
                    # Vérifier si le bâtiment est terminé
                    if building.get('status') == 'Terminé':
                        building_name = building.get('name', 'Bâtiment')
                        key = f"{building_name}:{city_name}"
                        
                        # Si pas de notification existante, en créer une
                        if key not in existing_building_notifications:
                            print(f"🔔 Création notification rétroactive: {building_name} dans {city_name}")
                            notification_id = self.create_building_notification(
                                player_id=player_id,
                                building_name=building_name,
                                city_name=city_name
                            )
                            created_notifications.append(notification_id)
                            
        except Exception as e:
            print(f"❌ Erreur lors de la création des notifications manquantes: {e}")
            
        return created_notifications
    
    def get_player_notifications(
        self, 
        player_id: str, 
        limit: int = 50,
        only_unread: bool = False
    ) -> List[Dict[str, Any]]:
        """Récupérer les notifications d'un joueur"""
        notifications_data = self._load_notifications()
        player_notifications = []
        
        for notif_data in notifications_data.get("notifications", []):
            if notif_data.get("player_id") == player_id:
                if only_unread and notif_data.get("is_read", False):
                    continue
                
                notification = Notification.from_dict(notif_data)
                player_notifications.append(notification.format_for_display())
        
        # Trier par date décroissante (plus récent en premier)
        player_notifications.sort(
            key=lambda x: datetime.strptime(x["date"], "%d/%m/%y à %Hh%M"), 
            reverse=True
        )
        
        return player_notifications[:limit]
    
    def get_unread_count(self, player_id: str) -> int:
        """Compter les notifications non lues"""
        notifications_data = self._load_notifications()
        count = 0
        
        for notif_data in notifications_data.get("notifications", []):
            if (notif_data.get("player_id") == player_id and 
                not notif_data.get("is_read", False)):
                count += 1
        
        return count
    
    def mark_all_as_read(self, player_id: str) -> bool:
        """Marquer toutes les notifications comme lues"""
        notifications_data = self._load_notifications()
        modified = False
        
        for notif_data in notifications_data.get("notifications", []):
            if (notif_data.get("player_id") == player_id and 
                not notif_data.get("is_read", False)):
                notif_data["is_read"] = True
                modified = True
        
        if modified:
            self._save_notifications_data(notifications_data)
        
        return modified
    
    def _save_notification(self, notification: Notification) -> str:
        """Sauvegarder une notification"""
        notifications_data = self._load_notifications()
        notifications_data["notifications"].append(notification.to_dict())
        self._save_notifications_data(notifications_data)
        return notification.id
    
    def _load_notifications(self) -> Dict[str, Any]:
        """Charger les notifications depuis le fichier"""
        return self.data_manager.load_notifications()
    
    def _save_notifications_data(self, data: Dict[str, Any]) -> None:
        """Sauvegarder les données de notifications"""
        self.data_manager.save_notifications(data)
