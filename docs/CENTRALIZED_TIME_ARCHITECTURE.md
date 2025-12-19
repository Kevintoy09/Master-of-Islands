# Architecture Centralisée pour MMO - Contrôle Global du Temps

## 🎯 OBJECTIFS
1. **Une seule valeur** contrôle TOUTE la vitesse du jeu
2. **Séparation** calculs backend / affichage frontend  
3. **Scalabilité** dev → production avec milliers de joueurs

## 🏗️ ARCHITECTURE PROPOSÉE

### 1. GameTimeManager (Centralisé)
```python
class GameTimeManager:
    def __init__(self):
        # VITESSES PRÉDÉFINIES
        self.DEVELOPMENT_SPEED = 3600    # 1h/sec (dev)
        self.TESTING_SPEED = 60          # 1h/min (test)
        self.PRODUCTION_SPEED = 1        # Temps réel (prod)
        self.SLOW_PRODUCTION = 0.016667  # 1 unité/minute
        
        self.current_multiplier = self.DEVELOPMENT_SPEED
        
        # INTERVALLES DE CALCUL (en secondes réelles)
        self.BACKEND_TICK_INTERVAL = 1    # Calculs toutes les 1s
        self.FRONTEND_UPDATE_INTERVAL = 5  # Affichage toutes les 5s
        
    def get_production_per_tick(self, base_production_per_second):
        """Calcule la production réelle par tick selon la vitesse"""
        game_seconds_per_tick = self.BACKEND_TICK_INTERVAL * self.current_multiplier
        return base_production_per_second * game_seconds_per_tick
        
    def switch_to_development(self):
        self.current_multiplier = self.DEVELOPMENT_SPEED
        
    def switch_to_production(self):
        self.current_multiplier = self.SLOW_PRODUCTION  # 1 unité/minute
```

### 2. Système Unifié de Production
```python
class UnifiedProductionSystem:
    def __init__(self, time_manager):
        self.time_manager = time_manager
        
    def calculate_research_production(self, workers, building_level):
        base_per_second = workers * self.get_points_per_worker(building_level)
        return self.time_manager.get_production_per_tick(base_per_second)
        
    def calculate_gold_production(self, buildings, population):
        base_per_second = self.calculate_base_gold_rate(buildings, population)
        return self.time_manager.get_production_per_tick(base_per_second)
        
    def calculate_resource_production(self, workers, site_level):
        base_per_second = workers * self.get_resource_yield(site_level)
        return self.time_manager.get_production_per_tick(base_per_second)
```

### 3. GameLoopManager Optimisé
```python
class OptimizedGameLoopManager:
    def __init__(self, time_manager):
        self.time_manager = time_manager
        self.production_system = UnifiedProductionSystem(time_manager)
        
        # Fréquences différenciées
        self.backend_ticker = PreciseTicker(1.0)  # 1s pour calculs
        self.frontend_ticker = PreciseTicker(5.0) # 5s pour clients
        
    def backend_tick(self):
        """Calculs fréquents (1s) - Haute précision"""
        self.update_all_productions()
        self.update_constructions()
        self.update_transports()
        
    def frontend_tick(self):
        """Mise à jour clients (5s) - Optimisé réseau"""
        self.send_updates_to_clients()
        self.cleanup_old_data()
```

## 📊 EXEMPLES CONCRETS

### Développement (3600x)
```python
# Base: 3 points recherche/seconde
# Tick (1s réel) = 3600s jeu = 10800 points
time_manager.switch_to_development()
production_per_tick = time_manager.get_production_per_tick(3)
# Result: 10800 points/tick
```

### Production (1 unité/minute)
```python  
# Base: 3 points recherche/seconde
# Tick (1s réel) = 0.016667s jeu = 0.05 points
time_manager.switch_to_production() 
production_per_tick = time_manager.get_production_per_tick(3)
# Result: 0.05 points/tick (3 points/minute)
```

## 🎮 INTERFACE DE CONTRÔLE

### API Routes
```python
@app.route('/admin/game-speed/<speed_preset>')
def set_game_speed(speed_preset):
    if speed_preset == 'dev':
        time_manager.switch_to_development()
    elif speed_preset == 'prod':
        time_manager.switch_to_production()
    
    # Recalculer TOUTES les productions
    production_system.recalculate_all_productions()
```

### Interface Admin
```javascript
// Boutons de contrôle
<button onClick={() => setGameSpeed('dev')}>
  Vitesse DEV (3600x)
</button>
<button onClick={() => setGameSpeed('prod')}>
  Vitesse PROD (1 unité/min)
</button>
```

## ✅ AVANTAGES

✅ **Contrôle total** : Une valeur change tout  
✅ **Performance** : Calculs optimisés selon l'usage  
✅ **Scalabilité** : Séparation backend/frontend  
✅ **Flexibilité** : Vitesses prédéfinies  
✅ **Maintenance** : Code centralisé  

## 🔧 MIGRATION

1. Étendre le TimeManager existant
2. Créer UnifiedProductionSystem  
3. Modifier GameLoopManager pour utiliser le temps centralisé
4. Adapter tous les calculs de production
5. Ajouter interface de contrôle admin