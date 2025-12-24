"""
CITY_CONSTANTS.PY - Constantes centralisées du jeu

RÔLE:
    Définit toutes les constantes et valeurs par défaut pour les villes et les mécaniques de jeu.

RESPONSABILITÉS:
    1. Constantes de transport (vitesse, capacité)
    2. Constantes de population et consommation
    3. Ressources par défaut des nouvelles villes (DEFAULT_CITY_RESOURCES)
    4. Bonus par défaut (building_bonus, production_bonus)

POINTS CLÉS:
    - DEFAULT_CITY_RESOURCES : Ressources de départ pour toute nouvelle ville
    - Plus de "research_bonus" ici : les bonus recherche sont au niveau JOUEUR (players.json)
    - building_bonus : Bonus de production des bâtiments (ex: Scierie +10% bois)
    - production_bonus : Système hérité (peut être fusionné avec building_bonus)

ARCHITECTURE:
    Ville créée → Reçoit DEFAULT_CITY_RESOURCES
    Bonus recherche → Chargés depuis player.research_effects.resource_bonuses
    Bonus bâtiments → Calculés dynamiquement depuis city.buildings

HISTORIQUE:
    - Nettoyage : Suppression de "research_bonus" (déplacé au niveau joueur)
"""

# ===================================
# CONSTANTES DE TRANSPORT
# ===================================
TRANSPORT_CONSTANTS = {
    "STANDARD_SPEED": 40,  # unités par seconde (vitesse de base uniforme 15.6)
    "SHIP_CAPACITY": 500,     # ressources par bateau
    "DISTANCE_SCALE_FACTOR": 15.0,  # Coefficient multiplicateur pour les distances (ajuste l'échelle du monde)
    # Note: loading_speed est déterminée par le niveau du port (voir buildings.json)
}

# ===================================
# CONSTANTES DE VILLE
# ===================================

# ===================================
# CONSTANTES DE POPULATION ET CONSOMMATION
# ===================================
POPULATION_CONSTANTS = {
    "CEREAL_CONSUMPTION_PER_PERSON_PER_HOUR": 0.1,  # Céréales/heure par habitant non nourri (standard Ikariam)
    "FAMINE_SATISFACTION_MALUS": 40,                # Malus de satisfaction en cas de famine
    "BASE_SATISFACTION": 50,                        # Satisfaction de base
    "BLOCK_GROWTH_WHEN_NO_CEREAL": True,            # Bloquer croissance si céréales = 0
}

DEFAULT_CITY_RESOURCES = {
    "wood": 1000,
    "stone": 200,
    "iron": 200,
    "cereal": 500,
    "papyrus": 200,
    "horse": 0,
    "marble": 0,
    "glass": 0,
    "wine": 0,
    "coal": 0,
    "gunpowder": 0,
    "spices": 0,
    "cotton": 0,
    "gold": 1000,
    "population_total": 40,
    "population_free": 40,
    "production_bonus": {},
    "building_bonus": {
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
        "cotton": 0,
        "gold": 0
    },
}
