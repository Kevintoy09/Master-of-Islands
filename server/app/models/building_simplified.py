"""
Classe Building simplifiée pour la gestion des bâtiments
Utilisée uniquement par building_manager et city_service
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time

@dataclass
class Building:
    """Classe helper pour manipuler les bâtiments"""
    
    slot_id: str
    name: str
    level: int = 1
    status: str = "En construction"
    construction_end: Optional[int] = None
    started_at: Optional[int] = None
    duration: Optional[int] = None
    effect: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def remaining_time(self) -> int:
        """Temps restant en secondes"""
        if not self.construction_end or self.status == "Terminé":
            return 0
        return max(0, self.construction_end - int(time.time()))
    
    @property
    def is_completed(self) -> bool:
        """Le bâtiment est-il terminé ?"""
        return self.status == "Terminé" or self.remaining_time == 0
    
    def complete(self):
        """Marque le bâtiment comme terminé"""
        self.status = "Terminé"
        self.construction_end = None
        
    def start_construction(self, duration: int):
        """Démarre la construction"""
        self.status = "En construction"
        self.started_at = int(time.time())
        self.construction_end = self.started_at + duration
        self.duration = duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialisation pour JSON - N'inclut PAS le champ effect"""
        result = {
            'slot_id': self.slot_id,
            'name': self.name,
            'level': self.level
        }
        
        # Ajouter les champs de construction dans le même ordre que les joueurs
        if self.construction_end:
            result['construction_end'] = self.construction_end
        if self.started_at:
            result['started_at'] = self.started_at
        if self.duration:
            result['duration'] = self.duration
        
        # status en dernier pour correspondre au format joueur
        result['status'] = self.status
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Building':
        """Désérialisation depuis JSON"""
        return cls(
            slot_id=data['slot_id'],
            name=data['name'],
            level=data.get('level', 1),
            status=data.get('status', 'En construction'),
            construction_end=data.get('construction_end'),
            started_at=data.get('started_at'),
            duration=data.get('duration'),
            effect=data.get('effect', {})
        )
    
    def update_from_config(self, buildings_data: Dict[str, Any]):
        """Met à jour les effets depuis la configuration"""
        if self.name in buildings_data:
            levels = buildings_data[self.name].get('levels', [])
            if 0 < self.level <= len(levels):
                self.effect = levels[self.level - 1].get('effect', {})
    
    def can_upgrade(self, buildings_data: Dict[str, Any]) -> bool:
        """Vérifie si le bâtiment peut être amélioré"""
        if self.name not in buildings_data:
            return False
        levels = buildings_data[self.name].get('levels', [])
        return self.level < len(levels) and self.status == "Terminé"
