import os
import json
import logging

# Import des constantes centralisées
try:
    from app.city_constants import POPULATION_CONSTANTS
    CEREAL_CONSUMPTION_PER_HOUR = POPULATION_CONSTANTS["CEREAL_CONSUMPTION_PER_PERSON_PER_HOUR"]
    BASE_SATISFACTION = POPULATION_CONSTANTS["BASE_SATISFACTION"]
    FAMINE_SATISFACTION_MALUS = POPULATION_CONSTANTS["FAMINE_SATISFACTION_MALUS"]
    BLOCK_GROWTH_WHEN_NO_CEREAL = POPULATION_CONSTANTS["BLOCK_GROWTH_WHEN_NO_CEREAL"]
    BASE_SECONDS_PER_UPDATE = 10  # 1 tick = 10 secondes
    TICKS_PER_HOUR = 360  # 1 tick = 10 secondes, donc 360 ticks par heure
except ImportError:
    # Fallback si l'import échoue (compatibilité)
    CEREAL_CONSUMPTION_PER_HOUR = 0.1
    BASE_SATISFACTION = 50
    FAMINE_SATISFACTION_MALUS = 40
    BLOCK_GROWTH_WHEN_NO_CEREAL = True
    BASE_SECONDS_PER_UPDATE = 10  # 1 tick = 10 secondes
    TICKS_PER_HOUR = 360

class PopulationManager:
    """
    Gère la croissance, la consommation alimentaire et les limites de population dans chaque ville.
    
    Responsabilités :
    - Calculer et mettre à jour la population selon la nourriture disponible et la satisfaction
    - Gérer la consommation de céréales et la décroissance en cas de pénurie  
    - Fournir les limites de population et de nourriture
    - Centraliser la logique de croissance/décroissance démographique
    - Gérer la satisfaction (bonus/malus des bâtiments, hygiène, surpopulation, etc.)
    
    Remarque : Ce manager assure la cohérence entre ressources alimentaires, bâtiments et population.
    """
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Fallback si pas de data_dir fourni (devrait pas arriver en production)
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
        self.data_dir = data_dir
        self.buildings_db = self.load_buildings_db()
        self.last_update_time = 0

    def load_buildings_db(self):
        """Charge la base de données des bâtiments"""
        path = os.path.join(self.data_dir, 'buildings.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur chargement buildings.json: {e}")
            return {}



    def get_effective_building_level(self, building):
        """
        Calcule le niveau effectif d'un bâtiment (prend en compte les constructions en cours).
        - Si le bâtiment est en construction/développement et a un previous_level, utilise previous_level
        - Sinon utilise le level normal
        """
        # Simplification: si status != "Terminé", considérer en construction
        if building.get('status') != 'Terminé':
            # Si c'est un développement (previous_level existe), utiliser l'ancien niveau
            if 'previous_level' in building:
                return building['previous_level']
            # Si c'est une construction initiale, pas d'effets
            else:
                return 0
        
        # Bâtiment terminé, utiliser le niveau actuel
        return building.get('level', 1)

    def get_building_effect(self, building_name, level, effect_key):
        """
        Récupère la valeur d'effet d'un bâtiment donné à un niveau donné.
        """
        if level < 1:
            return 0
        try:
            building_data = self.buildings_db.get(building_name, {})
            levels = building_data.get('levels', [])
            # Trouver le niveau correspondant
            level_data = next((l for l in levels if l.get('level') == level), None)
            if level_data:
                return level_data.get('effect', {}).get(effect_key, 0)
            return 0
        except Exception:
            return 0

    def ensure_city_satisfaction_structure(self, city):
        """
        S'assure que la ville a la structure de données nécessaire pour la satisfaction.
        """
        if 'windmill_cereal_bonus' not in city:
            city['windmill_cereal_bonus'] = 0  # Nouveau : slider du moulin (céréales/h)
        if 'has_plague' not in city:
            city['has_plague'] = False
        if 'hygiene_percent' not in city:
            city['hygiene_percent'] = 100

    def calculate_satisfaction(self, city):
        """
        Calcule la satisfaction totale d'une ville.
        """
        self.ensure_city_satisfaction_structure(city)
        
        # Satisfaction recalculée depuis satisfaction_details si existe
        if 'satisfaction_details' in city:
            total_bonus = sum(city['satisfaction_details'].get('bonus', {}).values())
            total_malus = sum(city['satisfaction_details'].get('malus', {}).values())
        else:
            total_bonus = 0
            total_malus = 0
        
        # Valeur de base = 50
        satisfaction = max(0, min(100, BASE_SATISFACTION - total_malus + total_bonus))
        return satisfaction

    def get_population_malus(self, city):
        """
        Calcule le malus de surpopulation.
        Malus = 1 par tranche de 10 habitants, plafonné à 8 jusqu'à 80 habitants,
        puis 1 par tranche de 10 au-delà.
        """
        population = int(city['resources'].get('population_total', 0))
        if population <= 80:
            return min(8, population // 10)
        else:
            return population // 10

    def calculate_food_limit(self, city):
        """
        Calcule la capacité maximale de nourriture d'une ville en fonction de l'Hôtel de Ville.
        """
        food_capacity = 0
        for building in city.get('buildings', []):
            if building.get('name') == 'Hôtel de Ville':
                level = self.get_effective_building_level(building)
                
                # Ignorer si pas d'effets (construction initiale)
                if level == 0:
                    continue
                
                food_bonus = self.get_building_effect('Hôtel de Ville', level, 'food_capacity')
                food_capacity += food_bonus
        return food_capacity

    def calculate_population_limit(self, city):
        """
        Calcule la capacité maximale de population d'une ville en fonction de l'Hôtel de Ville.
        """
        population_capacity = 0
        for building in city.get('buildings', []):
            if building.get('name') == 'Hôtel de Ville':
                level = self.get_effective_building_level(building)
                
                # Ignorer si pas d'effets (construction initiale)
                if level == 0:
                    continue
                
                capacity_bonus = self.get_building_effect('Hôtel de Ville', level, 'population_capacity')
                population_capacity += capacity_bonus
        return population_capacity

    def get_population_growth_from_town_hall(self, city):
        """
        Retourne la croissance de la population définie par l'Hôtel de Ville.
        """
        for building in city.get('buildings', []):
            if building.get('name') == 'Hôtel de Ville':
                level = self.get_effective_building_level(building)
                
                # Ignorer si pas d'effets (construction initiale)
                if level == 0:
                    continue
                
                return self.get_building_effect('Hôtel de Ville', level, 'population_growth')
        return 0.0

    def calculate_windmill_food_supply(self, city):
        """
        OBSOLÈTE - Supprimé avec la nouvelle logique du moulin.
        Le moulin ne nourrit plus d'habitants, il ajoute seulement un bonus de satisfaction.
        """
        return 0

    def calculate_cleanliness_capacity(self, city):
        """
        Calcule la capacité de propreté totale des Thermes.
        """
        cleanliness_capacity = 0
        for building in city.get('buildings', []):
            if building.get('name') == 'Thermes':
                level = self.get_effective_building_level(building)
                
                # Ignorer si pas d'effets (construction initiale)
                if level == 0:
                    continue
                
                capacity = self.get_building_effect('Thermes', level, 'cleanliness_capacity')
                cleanliness_capacity += capacity
        return cleanliness_capacity

    def ajuster_affectation_ouvriers(self, city):
        """
        Réaffecte les ouvriers en cas de décroissance : retire proportionnellement de toutes les ressources.
        En aucun cas la population libre ne doit être négative.
        """
        resources = city.get('resources', {})
        pop_totale = resources.get('population_total', 0)
        workers_assigned = city.get('workers_assigned', {})
        
        ouvriers_affectes = sum(workers_assigned.values())
        pop_totale_int = int(pop_totale)
        ouvriers_a_retirer = ouvriers_affectes - pop_totale_int
        
        if ouvriers_a_retirer <= 0:
            return
        
        # Réduction proportionnelle de tous les ouvriers
        ratio = max(0, pop_totale_int / ouvriers_affectes)
        for resource in workers_assigned:
            workers_assigned[resource] = int(workers_assigned[resource] * ratio)

    def _get_island_advanced_resource(self, island_id):
        """Récupère la ressource avancée d'une île depuis universe.json"""
        try:
            import os
            universe_path = os.path.join(self.data_dir, 'universe.json')
            with open(universe_path, 'r', encoding='utf-8') as f:
                universe = json.load(f)
            
            for island in universe.get('islands', []):
                if str(island.get('id')) == str(island_id):
                    return island.get('advanced_resource')
            return None
        except Exception:
            return None

    # ===== NOUVELLES MÉTHODES SPÉCIALISÉES (PHASE 2) =====
    
    def calculate_food_capacities(self, city):
        """Calcule les capacités alimentaires de la ville (seulement Hôtel de Ville maintenant)."""
        townhall_capacity = self.calculate_food_limit(city)
        return {
            'townhall_capacity': townhall_capacity,
            'windmill_capacity': 0,  # Supprimé : le moulin ne nourrit plus
            'total_capacity': townhall_capacity
        }
    
    def calculate_population_food_status(self, city, food_capacities):
        """Calcule l'état alimentaire de la population."""
        current_population = city['resources'].get('population_total', 0)
        
        # Population nourrie par l'Hôtel de Ville (gratuit)
        nourished_by_townhall = min(current_population, food_capacities['townhall_capacity'])
        
        # Population excédentaire = population non nourrie (consomme des céréales)
        unfed = max(0, current_population - food_capacities['townhall_capacity'])
        
        return {
            'total': current_population,
            'fed_by_townhall': nourished_by_townhall,
            'fed_by_windmill': 0,  # Supprimé
            'starving': unfed
        }
    
    def calculate_cereal_consumption(self, city, population_food_status, dt=1.0):
        """
        NOUVELLE LOGIQUE : Calcule la consommation de céréales.
        
        Consommation = (pop_unfed × 0.1 céréale/h) + windmill_cereal_bonus
        
        - pop_unfed : habitants au-delà de la capacité de l'Hôtel de Ville
        - windmill_cereal_bonus : bonus du slider du moulin (0 à capacité max)
        """
        # Récupérer le bonus céréales actuel (slider)
        windmill_bonus = city.get('windmill_cereal_bonus', 0)
        
        # Récupérer la capacité max du moulin
        max_windmill_bonus = 0
        for building in city.get('buildings', []):
            if building.get('name') == 'Windmill':
                level = self.get_effective_building_level(building)
                if level > 0:
                    max_windmill_bonus = self.get_building_effect('Windmill', level, 'cereal_bonus_per_hour')
                    break
        
        # Forcer le bonus dans les limites
        windmill_bonus = max(0, min(windmill_bonus, max_windmill_bonus))
        city['windmill_cereal_bonus'] = windmill_bonus
        
        # Consommation de base : pop_unfed × 0.1 céréale/hab/heure
        pop_unfed = population_food_status['starving']
        base_consumption_per_hour = pop_unfed * CEREAL_CONSUMPTION_PER_HOUR
        
        # Consommation totale = base + bonus moulin
        total_consumption_per_hour = base_consumption_per_hour + windmill_bonus
        
        # Conversion en consommation par tick
        consumption_per_tick = total_consumption_per_hour / TICKS_PER_HOUR
        total_needed = consumption_per_tick * dt
        
        # LOG DEBUG
        city_name = city.get('name', 'Unknown')
        logging.info(f"[CEREAL] {city_name}: pop_unfed={pop_unfed:.1f}, base={base_consumption_per_hour:.2f}/h, windmill_bonus={windmill_bonus:.1f}/h, total={total_consumption_per_hour:.2f}/h, per_tick={consumption_per_tick:.4f}")
        
        return {
            'windmill_bonus': windmill_bonus,
            'population_unfed': pop_unfed,
            'base_rate_per_hour': CEREAL_CONSUMPTION_PER_HOUR,
            'total_consumption_per_hour': total_consumption_per_hour,
            'total_needed': total_needed,
            'consumption_per_tick': consumption_per_tick,
            'dt': dt
        }
    
    def _calculate_heroes_satisfaction_bonus(self, city) -> int:
        """
        Calcule le bonus de satisfaction apporté par les héros en garnison dans la ville.
        
        Le bonus est directement lu depuis player_heroes.json (satisfaction_bonus).
        Le status est vérifié dans la section military/heroes de la ville (savegame.json).
        Cette valeur est calculée et stockée lors de la création du héros et à chaque level up.
        
        Returns:
            int: Total du bonus de satisfaction (somme de tous les héros en garrison)
        """
        try:
            city_id = city.get('id')
            owner_id = city.get('owner')
            
            if not owner_id or not city_id:
                return 0
            
            # Récupérer les héros de la garnison de la ville (depuis savegame.json)
            military_data = city.get('military', {})
            heroes_garrison = military_data.get('heroes', {})
            
            if not heroes_garrison:
                return 0
            
            # Charger player_heroes.json pour les stats (satisfaction_bonus)
            gamedata_dir = os.path.join(os.path.dirname(self.data_dir), 'gamedata')
            player_heroes_path = os.path.join(gamedata_dir, 'player_heroes.json')
            
            if not os.path.exists(player_heroes_path):
                return 0
            
            with open(player_heroes_path, 'r', encoding='utf-8') as f:
                player_heroes_data = json.load(f)
            
            # Vérifier si le joueur a des héros
            if owner_id not in player_heroes_data:
                return 0
            
            player_heroes = player_heroes_data[owner_id].get('heroes', {})
            total_satisfaction_bonus = 0
            
            # Parcourir les héros de la garnison de la ville
            for hero_instance_id, hero_garrison_data in heroes_garrison.items():
                # Vérifier le status dans savegame.json (garrison uniquement)
                status = hero_garrison_data.get('status', '')
                
                if status != 'garrison':
                    continue
                
                # Récupérer les données complètes du héros depuis player_heroes.json
                hero_data = player_heroes.get(hero_instance_id)
                
                if not hero_data:
                    continue
                
                # Lire directement le bonus de satisfaction stocké
                hero_satisfaction = hero_data.get('satisfaction_bonus', 0)
                total_satisfaction_bonus += hero_satisfaction
                
                hero_id = hero_data.get('hero_id', 'unknown')
                hero_level = hero_data.get('current_level', 1)
                logging.info(f"🦸 Héros {hero_id} (lvl {hero_level}) en garnison à {city.get('name')}: +{hero_satisfaction} satisfaction")
            
            return total_satisfaction_bonus
            
        except Exception as e:
            logging.warning(f"Erreur calcul bonus satisfaction héros: {e}")
            return 0
    
    def calculate_satisfaction_factors(self, city, cereal_consumption):
        """Calcule tous les facteurs de satisfaction."""
        self.ensure_city_satisfaction_structure(city)
        
        bonus = {}
        malus = {}
        
        # NOUVEAU : Bonus du moulin = consommation de céréales bonus (windmill_cereal_bonus)
        windmill_bonus_value = cereal_consumption.get('windmill_bonus', 0)
        if windmill_bonus_value > 0:
            bonus['windmill'] = int(windmill_bonus_value)  # 1 point de satisfaction par céréale/h
        
        # Bonus des Thermes
        thermes_bonus = 0
        for building in city.get('buildings', []):
            if building.get('name') == 'Thermes':
                level = self.get_effective_building_level(building)
                if level > 0:
                    thermes_bonus += self.get_building_effect('Thermes', level, 'satisfaction_bonus')
        bonus['thermes'] = thermes_bonus
        
        # 🦸 NOUVEAU : Bonus des héros en garnison
        heroes_bonus = self._calculate_heroes_satisfaction_bonus(city)
        if heroes_bonus > 0:
            bonus['heroes'] = heroes_bonus
        
        # Bonus des recherches du joueur (Puits, Philosophie, etc.)
        research_satisfaction_bonus = 0
        owner_id = city.get('owner')
        if owner_id:
            # players.json est dans gamedata/ (fichier de sauvegarde)
            gamedata_dir = os.path.join(os.path.dirname(self.data_dir), 'gamedata')
            players_path = os.path.join(gamedata_dir, 'players.json')
            research_path = os.path.join(self.data_dir, 'research.json')
            
            try:
                with open(players_path, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
                
                player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
                if player:
                    with open(research_path, 'r', encoding='utf-8') as f:
                        research_data = json.load(f)
                    
                    unlocked_research = player.get('unlocked_research', [])
                    
                    for research_id in unlocked_research:
                        research = next((r for r in research_data.get('researches', []) if r.get('id') == research_id), None)
                        if research and 'effect' in research:
                            effect = research['effect']
                            # Cumuler les bonus de satisfaction
                            if 'satisfaction_bonus' in effect:
                                research_satisfaction_bonus += effect['satisfaction_bonus']
            except Exception as e:
                logging.warning(f"Erreur chargement recherches satisfaction: {e}")
        
        if research_satisfaction_bonus > 0:
            bonus['research'] = research_satisfaction_bonus
        
        # 🌾 Bonus de faction céréales : +10 satisfaction pour toutes les villes
        if owner_id:
            try:
                gamedata_dir = os.path.join(os.path.dirname(self.data_dir), 'gamedata')
                players_path = os.path.join(gamedata_dir, 'players.json')
                
                with open(players_path, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
                
                player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
                if player and player.get('faction') == 'cereal':
                    bonus['faction'] = 10  # +10 satisfaction pour faction céréales
            except Exception as e:
                logging.warning(f"Erreur chargement faction satisfaction: {e}")
        
        # Malus de population
        malus['population'] = self.get_population_malus(city)
        
        # Malus/bonus d'imposition
        gold_rate = city.get('gold_rate', 1)
        if gold_rate == 1:
            bonus['impot'] = 5
        elif gold_rate == 2:
            malus['impot'] = 10
        elif gold_rate == 3:
            malus['impot'] = 20
        
        # Bonus/malus d'hygiène 
        population = city['resources'].get('population_total', 0)
        cleanliness_capacity = self.calculate_cleanliness_capacity(city)
        hygiene_percent = 100 if population == 0 else int(100 * cleanliness_capacity / max(1, population))
        
        # Stocker le pourcentage d'hygiène dans la ville
        city['hygiene_percent'] = hygiene_percent
        
        # Système de paliers d'hygiène progressifs
        if hygiene_percent >= 80:
            bonus['hygiene'] = 10  # Excellente hygiène
        elif hygiene_percent >= 60:
            bonus['hygiene'] = 5   # Bonne hygiène
        elif hygiene_percent >= 40:
            malus['hygiene'] = 5   # Hygiène médiocre
        else:
            malus['hygiene'] = 15  # Hygiène catastrophique
            
            # Déclenchement de la peste si hygiène < 40% et population > 50
            if population > 50 and not city.get('has_plague', False):
                # MORTALITÉ : tuer 25% de la population libre au déclenchement
                population_free = city['resources'].get('population_free', 0)
                deaths = int(population_free * 0.25)
                if deaths > 0:
                    city['resources']['population_free'] = max(0, population_free - deaths)
                    city['resources']['population_total'] = max(0, city['resources'].get('population_total', 0) - deaths)
                
                city['has_plague'] = True  # Déclenche la peste
        
        # Malus de peste (cumulatif avec le malus d'hygiène)
        if city.get('has_plague', False):
            malus['plague'] = 20  # Peste active = -20 satisfaction supplémentaire
        
        return {'bonus': bonus, 'malus': malus}
    
    def calculate_health_status(self, city):
        """Calcule l'état de santé et d'hygiène."""
        population = city['resources'].get('population_total', 0)
        cleanliness_capacity = self.calculate_cleanliness_capacity(city)
        
        hygiene_percent = 100 if population == 0 else int(100 * cleanliness_capacity / max(1, population))
        
        # NOTE: La peste ne se désactive PAS automatiquement ici
        # Elle doit être guérie via le bouton dans le popup des thermes (cure_plague endpoint)
        
        return {
            'hygiene_percent': hygiene_percent,
            'has_plague': city.get('has_plague', False),
            'cleanliness_capacity': cleanliness_capacity,
            'population': population
        }
    
    def apply_consumption_and_famine(self, city, cereal_consumption, satisfaction_factors):
        """
        Applique la consommation de céréales et gère la famine.
        - Si bloqué : pas de consommation, pas de famine (population stable)
        - Sinon : consommation normale et famine si céréales insuffisantes
        """
        resources = city['resources']
        current_cereal = resources.get('cereal', 0)
        total_needed = cereal_consumption['total_needed']
        is_growth_blocked = resources.get('growth_blocked_no_cereal', False)
        
        # Si bloqué, population stable : pas de consommation ni de famine
        if is_growth_blocked:
            satisfaction_factors['malus'].pop('famine', None)
            return
        
        # Si pas de besoin de céréales (population <= capacité gratuite)
        if total_needed == 0:
            satisfaction_factors['malus'].pop('famine', None)
            return
        
        # Consommation et gestion de la famine
        if current_cereal >= total_needed:
            resources['cereal'] = max(0, current_cereal - total_needed)
            satisfaction_factors['malus'].pop('famine', None)
            # Logging supprimé pour réduire le bruit
        else:
            # Plus de céréales : réinitialiser le slider du moulin automatiquement
            resources['cereal'] = 0
            city['windmill_cereal_bonus'] = 0
            satisfaction_factors['malus']['famine'] = FAMINE_SATISFACTION_MALUS
            # Logging supprimé (famine visible dans l'UI via malus satisfaction)
    
    def calculate_population_growth(self, city, satisfaction: int, dt: float, population_food_status):
        """
        Calcule le taux de croissance de la population.
        Si bloqué (growth_blocked_no_cereal), retourne 0 pour stabiliser la population.
        
        Note: Les valeurs dans buildings.json sont en pop/heure (ex: 5.0 pop/heure).
        Avec 1 tick = 10 secondes, il y a 360 ticks par heure.
        On divise donc par 360 pour obtenir la croissance par tick.
        """
        resources = city['resources']
        is_blocked = resources.get('growth_blocked_no_cereal', False)
        
        if is_blocked:
            return 0
        
        # Calcul basé sur la satisfaction
        base_growth_rate_per_hour = self.get_population_growth_from_town_hall(city)
        
        # Conversion de pop/heure vers pop/tick (1 tick = 10 secondes, 360 ticks/heure)
        TICKS_PER_HOUR = 360
        base_growth_rate_per_tick = base_growth_rate_per_hour / TICKS_PER_HOUR
        
        # Modificateur basé sur satisfaction:
        # satisfaction = 50 → modificateur = 0 → croissance × 1 (normale)
        # satisfaction = 100 → modificateur = 3 → croissance × 4 (quadruplée)
        # satisfaction = 0 → modificateur = -5 → croissance × (-4) (décroissance forte)
        if satisfaction >= BASE_SATISFACTION:
            # Au-dessus de 50: bonus de 0% à +300%
            modificateur = 3 * (satisfaction - BASE_SATISFACTION) / BASE_SATISFACTION
        else:
            # En-dessous de 50: malus progressif jusqu'à -500% à satisfaction=0
            # À satisfaction=0, modificateur=-5 → growth × (1-5) = growth × -4
            modificateur = -5 * (BASE_SATISFACTION - satisfaction) / BASE_SATISFACTION
        
        modificateur = max(-5, min(3, modificateur))  # Limiter entre -500% et +300%
        return base_growth_rate_per_tick * (1 + modificateur)

    def apply_population_growth(self, city, growth_rate: float, dt: float):
        """
        Applique la croissance/décroissance de la population.
        - Utilise un accumulateur fractionnaire pour éviter les pertes de précision
        - Détecte quand la population atteint la capacité alimentaire sans céréales
        - Active le blocage automatique dans ce cas (déblocage manuel requis)
        """
        import math
        
        resources = city['resources']
        current_pop = int(resources.get('population_total', 0))
        pop_fractional = resources.get('population_fractional', 0.0)
        current_cereal = resources.get('cereal', 0)
        food_capacity = int(resources.get('pop_nourished_by_townhall', 0) + resources.get('pop_nourished_by_windmill', 0))
        
        # Calcul avec accumulateur fractionnaire
        # Note: growth_rate est déjà calculé PAR TICK, donc on ne multiplie PAS par dt
        growth_amount = growth_rate
        total_growth = pop_fractional + growth_amount
        population_gained = math.floor(total_growth)  # floor pour gérer correctement les négatifs
        pop_fractional = total_growth - population_gained
        
        new_population = current_pop + population_gained
        
        # Détection du blocage : si on atteint la capacité en descendant sans céréales
        if current_cereal < 1 and new_population == food_capacity and current_pop > food_capacity:
            resources['growth_blocked_no_cereal'] = True
        
        # Limites
        max_population = self.calculate_population_limit(city)
        if new_population > max_population:
            new_population = max_population
            pop_fractional = 0.0
        
        if new_population < 0:
            new_population = 0
            pop_fractional = 0.0
        
        # Mise à jour (population toujours entière)
        resources['population_total'] = int(new_population)
        resources['population_fractional'] = pop_fractional
        
        # Log
        city_name = city.get('name', 'Unknown')
        logging.info(f"🔄 [{city_name}] Population: {current_pop} → {new_population} (fraction: {pop_fractional:.3f}) | Growth: {growth_amount:.3f}")

    def update_city_population(self, city, elapsed_seconds=1):
        """Méthode principale de mise à jour de la population - Version refactorisée."""
        if not city.get('resources') or not city.get('owner'):
            return city
        
        try:
            # Récupérer le tick actuel pour le timestamp
            # Simplification: utiliser elapsed_seconds directement
            dt = elapsed_seconds / BASE_SECONDS_PER_UPDATE
            
            # 1. Calcul des capacités alimentaires
            food_capacities = self.calculate_food_capacities(city)
            
            # 2. Calcul de l'état alimentaire de la population
            population_food_status = self.calculate_population_food_status(city, food_capacities)
            
            # 3. Calcul de la consommation de céréales (avec temps écoulé)
            cereal_consumption = self.calculate_cereal_consumption(city, population_food_status, dt)
            
            # 4. Calcul des facteurs de satisfaction
            satisfaction_factors = self.calculate_satisfaction_factors(city, cereal_consumption)
            
            # 5. Application de la consommation et gestion de la famine
            self.apply_consumption_and_famine(city, cereal_consumption, satisfaction_factors)
            
            # 6. Calcul de la satisfaction finale
            satisfaction = BASE_SATISFACTION
            for bonus in satisfaction_factors['bonus'].values():
                satisfaction += bonus
            for malus in satisfaction_factors['malus'].values():
                satisfaction -= malus
            
            # 7. Calcul de l'état de santé
            health_status = self.calculate_health_status(city)
            
            # 8. Calcul de la croissance
            growth_rate = self.calculate_population_growth(city, satisfaction, dt, population_food_status)
            
            # 9. Application de la croissance
            self.apply_population_growth(city, growth_rate, dt)
            
            # 10. Réaffectation des ouvriers si nécessaire
            resources = city['resources']
            current_population = resources.get('population_total', 0)
            workers_assigned = city.get('workers_assigned', {})
            total_workers = sum(workers_assigned.values())
            
            if total_workers > current_population:
                self.ajuster_affectation_ouvriers(city)
            
            # 11. Mise à jour des données détaillées de satisfaction dans satisfaction_details
            # Calculer real_growth_per_hour pour l'affichage (growth_rate est en hab/tick)
            real_growth_per_hour = growth_rate * 360  # 360 ticks par heure
            
            city['satisfaction_details'] = {
                'base': BASE_SATISFACTION,
                'bonus': satisfaction_factors['bonus'],
                'malus': satisfaction_factors['malus'],
                'total': satisfaction,
                'growth_rate': growth_rate,  # En hab/tick (pour le calcul réel)
                'real_growth_per_hour': real_growth_per_hour  # En hab/h (pour l'affichage)
            }
            
            # SUPPRIMÉ: satisfaction en racine (doublon de satisfaction_details.total)
            
            # 13. Mise à jour des resources pour compatibilité frontend
            # Garder ces champs pour compatibilité avec le frontend React (WindmillPopupContent.tsx, TownHallPopupContent.tsx)
            resources['population_unfed'] = population_food_status['starving']
            resources['pop_nourished_by_townhall'] = population_food_status['fed_by_townhall']
            resources['cereal_consumption_per_tick'] = cereal_consumption['consumption_per_tick']  # Consommation par tick (pas total_needed qui est * dt)
            resources['windmill_cereal_bonus'] = cereal_consumption['windmill_bonus']  # Bonus du moulin (slider)
            
            # Mettre à jour population_free basée sur workers_assigned
            workers_assigned = city.get('workers_assigned', {})
            total_workers = sum(workers_assigned.values())
            
            resources['population_free'] = max(0, int(current_population) - total_workers)
            
        except Exception as e:
            logging.error(f"Erreur dans PopulationManager.update_city_population : {e}")
        
        # Plus besoin de timestamp - le système centralisé gère tout
        return city

    def update_all_cities_population(self, savegame_data, elapsed_seconds=None):
        """
        Met à jour la population de toutes les villes dans le savegame.
        🕒 SYSTÈME SIMPLIFIÉ : Utilise elapsed_seconds directement
        """
        # Simplification: ne plus utiliser time_manager
        
        for city in savegame_data.get('cities', []):
            # Mode direct: utiliser elapsed_seconds ou 1.0 par défaut
            if elapsed_seconds is not None:
                # Mode forcé : utiliser les secondes directement
                time_to_use = elapsed_seconds
            else:
                # Mode par défaut : 1.0 seconde pour un tick manuel
                time_to_use = 1.0
                
            if time_to_use > 0:
                self.update_city_population(city, time_to_use)
        
        return savegame_data

    # get_city_population_info() supprimée - les données sont maintenant dans satisfaction_details

    def set_windmill_cereal_bonus(self, city, bonus_value):
        """
        NOUVELLE MÉTHODE : Définit le bonus de céréales du moulin (slider).
        
        Args:
            city: La ville
            bonus_value: Valeur du slider (céréales/heure)
        
        Returns:
            La valeur réellement appliquée (limitée par la capacité max du moulin)
        """
        self.ensure_city_satisfaction_structure(city)
        
        # Récupérer la capacité max du moulin
        max_bonus = 0
        for building in city.get('buildings', []):
            if building.get('name') == 'Windmill':
                level = self.get_effective_building_level(building)
                if level > 0:
                    max_bonus = self.get_building_effect('Windmill', level, 'cereal_bonus_per_hour')
                    break
        
        # Forcer dans les bornes [0, max]
        city['windmill_cereal_bonus'] = max(0, min(bonus_value, max_bonus))
        return city['windmill_cereal_bonus']

    def cure_plague(self, city):
        """
        Soigne la peste dans une ville (action manuelle du joueur).
        """
        self.ensure_city_satisfaction_structure(city)
        
        # Détecter le changement d'état pour notification
        previous_plague_status = city.get('has_plague', False)
        city['has_plague'] = False
        # La peste sera retirée au prochain recalcul de satisfaction_details
        
        # Marquer le changement pour notification si la peste était active
        if previous_plague_status:
            city['_plague_status_changed'] = {
                'from': True,
                'to': False,
                'city_name': city.get('name', 'Ville'),
                'owner': city.get('owner')
            }
        
        return True
