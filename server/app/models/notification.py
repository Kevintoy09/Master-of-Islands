"""
Modèle pour les notifications du joueur
"""
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional
import uuid

# Timezone France (UTC+1 en hiver, UTC+2 en été)
FRANCE_TZ = timezone(timedelta(hours=2))  # Actuellement UTC+2 (heure d'été)

class NotificationType(Enum):
    TRANSPORT_ARRIVED = "transport"
    BUILDING_COMPLETED = "batiment"
    RESEARCH_COMPLETED = "recherche"
    MARKET_PURCHASE = "achat_marche"
    MARKET_SALE = "vente_marche"

class Notification:
    """Modèle pour une notification du joueur"""
    
    def __init__(
        self,
        id: str = None,
        player_id: str = "",
        type: NotificationType = NotificationType.TRANSPORT_ARRIVED,
        title: str = "",
        message: str = "",
        details: Dict[str, Any] = None,
        is_read: bool = False,
        created_at: datetime = None
    ):
        self.id = id or str(uuid.uuid4())
        self.player_id = player_id
        self.type = type
        self.title = title
        self.message = message
        self.details = details or {}
        self.is_read = is_read
        self.created_at = created_at or datetime.now(FRANCE_TZ)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour JSON"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Créer depuis un dictionnaire"""
        return cls(
            id=data.get("id"),
            player_id=data.get("player_id", ""),
            type=NotificationType(data.get("type", "transport")),
            title=data.get("title", ""),
            message=data.get("message", ""),
            details=data.get("details", {}),
            is_read=data.get("is_read", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(FRANCE_TZ).isoformat()))
        )
    
    def format_for_display(self) -> Dict[str, str]:
        """Formatter pour l'affichage dans l'interface"""
        date_str = self.created_at.strftime("%d/%m/%y à %Hh%M")
        
        # Format spécifique selon le type
        if self.type == NotificationType.TRANSPORT_ARRIVED:
            detail = f"Transport {self.details.get('from', 'Ville A')} → {self.details.get('to', 'Ville B')}"
            resources = self.details.get('resources', {})
            if resources:
                if isinstance(resources, dict):
                    # Format dictionnaire : {"wood": 200, "iron": 150}
                    resource_list = []
                    for resource, amount in resources.items():
                        resource_names = {
                            'wood': 'bois', 'stone': 'pierre', 'iron': 'fer', 
                            'cereal': 'céréales', 'papyrus': 'papyrus',
                            'gold': 'or', 'diamond': 'diamant'
                        }
                        resource_name = resource_names.get(resource, resource)
                        resource_list.append(f"{amount} {resource_name}")
                    detail += f" : {', '.join(resource_list)}"
                else:
                    # Format string : "200 bois et 150 fer"
                    detail += f" : {resources}"
        
        elif self.type == NotificationType.BUILDING_COMPLETED:
            building_name = self.details.get('building_name', 'Bâtiment')
            city_name = self.details.get('city_name', 'Ville')
            detail = f"{building_name} terminé dans {city_name}"
        
        elif self.type == NotificationType.RESEARCH_COMPLETED:
            research_name = self.details.get('research_name', 'Recherche')
            detail = f"Recherche '{research_name}' terminée"
        
        else:
            detail = self.message
        
        return {
            "date": date_str,
            "type": self.type.value,
            "detail": detail
        }
