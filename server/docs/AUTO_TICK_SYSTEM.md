# AUTO-TICK SYSTEM - Documentation

## 🚀 Fonctionnalités

Le système d'auto-tick automatise les tâches temporelles du jeu :

### ✅ Activé par défaut
- **Transports** : Traitement automatique des voyages, chargements, livraisons
- **Production** : Génération automatique des ressources (configurable)
- **Intervalle configurable** : Par défaut 30 secondes (modifiable)

### 🎛️ Configuration

**Fichier** : `data/auto_tick_settings.json`
```json
{
  "enabled": true,
  "interval_seconds": 30,
  "run_production": true
}
```

### 📊 Statut

Le système se lance automatiquement au démarrage du serveur :
```
[OK] [AUTO-TIMER] Service automatique démarré for transports and constructions WITH PRODUCTION
```

### 🔧 API de contrôle

Endpoints admin disponibles :
- `GET /admin/api/auto-tick/status` - Statut du système
- `POST /admin/api/auto-tick` - Activer/désactiver
- `POST /admin/api/auto-tick/interval` - Modifier l'intervalle

### 🎯 Résultats

Production automatique fonctionnelle :
- Les ressources augmentent automatiquement selon l'intervalle configuré
- Les transports se traitent en temps réel
- Aucune intervention manuelle nécessaire

## 📝 Maintenance

Système auto-suffisant, pas de maintenance spéciale requise.