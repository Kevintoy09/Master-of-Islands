"""
=================================================================
DB_MODELS.PY - Modèles PostgreSQL
=================================================================

SCHÉMA OPTIMISÉ POUR IMPERIUM:
- Tables normalisées avec relations
- Index sur les clés fréquentes
- JSONB pour données flexibles (ressources, stats)

TABLES PRINCIPALES:
- players: Joueurs et métadonnées
- cities: Villes avec position et ressources
- buildings: Bâtiments dans les villes
- research: Recherches complétées
- units: Unités militaires
- heroes: Héros disponibles
- battles: Historique de combats
- transports: Mouvements de ressources
=================================================================
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Index, Text, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base


class Player(Base):
    __tablename__ = 'players'
    
    id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Métadonnées
    alliance_id = Column(String(50), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relations
    cities = relationship('City', back_populates='player', cascade='all, delete-orphan')
    research = relationship('Research', back_populates='player', cascade='all, delete-orphan')
    

class City(Base):
    __tablename__ = 'cities'
    
    id = Column(String(50), primary_key=True)
    player_id = Column(String(50), ForeignKey('players.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    # Position géographique
    island_id = Column(String(50), nullable=False, index=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    
    # État de la ville
    population = Column(Integer, default=0)
    satisfaction = Column(Float, default=100.0)
    
    # Ressources (JSONB pour flexibilité)
    resources = Column(JSONB, default={})  # {wood: 1000, stone: 500, ...}
    production = Column(JSONB, default={})  # Production par heure
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    last_tick = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    player = relationship('Player', back_populates='cities')
    buildings = relationship('Building', back_populates='city', cascade='all, delete-orphan')
    units = relationship('Unit', back_populates='city', cascade='all, delete-orphan')
    
    # Index composite pour recherche géographique
    __table_args__ = (
        Index('idx_city_location', 'island_id', 'x', 'y'),
    )


class Building(Base):
    __tablename__ = 'buildings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey('cities.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Type et niveau
    building_type = Column(String(50), nullable=False, index=True)
    level = Column(Integer, default=1)
    
    # Construction en cours
    is_upgrading = Column(Boolean, default=False)
    upgrade_start_time = Column(BigInteger, nullable=True)  # Timestamp
    upgrade_duration = Column(Integer, nullable=True)  # Secondes
    
    # Relations
    city = relationship('City', back_populates='buildings')
    
    __table_args__ = (
        Index('idx_building_city_type', 'city_id', 'building_type'),
    )


class Research(Base):
    __tablename__ = 'research'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String(50), ForeignKey('players.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Recherche
    research_id = Column(String(100), nullable=False, index=True)
    level = Column(Integer, default=1)
    
    # Progression
    is_researching = Column(Boolean, default=False)
    research_start_time = Column(BigInteger, nullable=True)
    research_duration = Column(Integer, nullable=True)
    
    completed_at = Column(DateTime, nullable=True)
    
    # Relations
    player = relationship('Player', back_populates='research')
    
    __table_args__ = (
        Index('idx_research_player', 'player_id', 'research_id'),
    )


class Unit(Base):
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey('cities.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Type d'unité
    unit_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, default=0)
    
    # Amélioration
    upgrade_level = Column(Integer, default=0)
    
    # Relations
    city = relationship('City', back_populates='units')


class Hero(Base):
    __tablename__ = 'heroes'
    
    id = Column(String(50), primary_key=True)
    player_id = Column(String(50), ForeignKey('players.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Héros
    hero_id = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Stats (JSONB)
    stats = Column(JSONB, default={})  # {attack: 10, defense: 8, ...}
    skills = Column(JSONB, default=[])  # [skill_id1, skill_id2]
    
    # État
    city_id = Column(String(50), nullable=True)  # Ville actuelle
    is_available = Column(Boolean, default=True)


class Battle(Base):
    __tablename__ = 'battles'
    
    id = Column(String(50), primary_key=True)
    
    # Participants
    attacker_id = Column(String(50), ForeignKey('players.id'), nullable=False, index=True)
    defender_id = Column(String(50), ForeignKey('players.id'), nullable=False, index=True)
    
    # Lieu
    target_city_id = Column(String(50), nullable=False)
    
    # État
    status = Column(String(20), nullable=False, index=True)  # pending, ongoing, finished
    winner = Column(String(50), nullable=True)
    
    # Données de combat (JSONB)
    battlefield_data = Column(JSONB, default={})
    combat_log = Column(JSONB, default=[])
    rewards = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_battle_status', 'status', 'created_at'),
    )


class Transport(Base):
    __tablename__ = 'transports'
    
    id = Column(String(50), primary_key=True)
    player_id = Column(String(50), ForeignKey('players.id'), nullable=False, index=True)
    
    # Origine et destination
    from_city_id = Column(String(50), nullable=False)
    to_city_id = Column(String(50), nullable=False)
    
    # Ressources transportées
    resources = Column(JSONB, default={})
    
    # État
    status = Column(String(20), default='in_transit')  # in_transit, arrived, cancelled
    
    # Timestamps
    departure_time = Column(BigInteger, nullable=False)
    arrival_time = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_transport_arrival', 'player_id', 'arrival_time', 'status'),
    )


class GameConfig(Base):
    """Table pour stocker les configurations globales du jeu"""
    __tablename__ = 'game_config'
    
    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def create_all_tables(engine):
    """Crée toutes les tables dans PostgreSQL"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tables PostgreSQL créées avec succès")


def drop_all_tables(engine):
    """⚠️ ATTENTION: Supprime toutes les tables"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ Tables PostgreSQL supprimées")
