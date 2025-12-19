"""
=================================================================
DATABASE.PY - Configuration PostgreSQL pour production
=================================================================

RESPONSABILITÉS:
- Connexion PostgreSQL via SQLAlchemy
- Fallback automatique vers JSON en local
- Configuration adaptative selon environnement

ENVIRONNEMENTS:
- Production: PostgreSQL (Railway)
- Développement: JSON files (système actuel)
=================================================================
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Détection de l'environnement
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DATABASE_URL = os.getenv('DATABASE_URL', None)

# Base pour les modèles ORM
Base = declarative_base()

# Session database
db_session = None
engine = None


def init_db():
    """Initialise la connexion à la base de données"""
    global db_session, engine
    
    if ENVIRONMENT == 'production' and DATABASE_URL:
        # PostgreSQL pour production
        print(f"🐘 Connexion PostgreSQL: {DATABASE_URL[:30]}...")
        
        # Railway fournit postgres:// mais SQLAlchemy veut postgresql://
        db_url = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Vérifier la connexion avant utilisation
            pool_recycle=3600,   # Recycler les connexions après 1h
            echo=False  # Désactiver les logs SQL en prod
        )
        
        # Créer les tables si nécessaire
        Base.metadata.create_all(bind=engine)
        
        # Session factory
        session_factory = sessionmaker(bind=engine)
        db_session = scoped_session(session_factory)
        
        print("[OK] PostgreSQL connecté avec succès")
        return True
    else:
        # Mode développement - JSON files
        print("[DEV] Mode developpement: utilisation des fichiers JSON")
        return False


def get_db_session():
    """Retourne la session database (ou None si JSON mode)"""
    return db_session


def close_db():
    """Ferme proprement la connexion database"""
    if db_session:
        db_session.remove()
    if engine:
        engine.dispose()
