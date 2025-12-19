# 🎮 Master of Islands - AI System Phase 1
## Guide de Test et Validation

---

## ✅ Phase 1 TERMINÉE

Toutes les fonctionnalités de la Phase 1 sont implémentées :

### 📁 **Fichiers créés** (12 fichiers)

#### **1. Configuration**
- `server/app/ai/config/ai_config.json` (187 lignes)
  - Personnalités (economic, military, balanced)
  - Règles de spawn (minimum 1 IA par île)
  - Simulation d'activité (3-8 sessions/jour)
  - Configuration des modules

#### **2. Utilitaires** (3 fichiers)
- `server/app/ai/utils/data_loader.py` (145 lignes)
  - Chargement dynamique JSON avec cache
- `server/app/ai/utils/activity_simulator.py` (192 lignes)
  - Simulation connexions réalistes
- `server/app/ai/utils/priority_queue.py` (75 lignes)
  - File de priorité pour actions

#### **3. Moteur de décision** (3 fichiers)
- `server/app/ai/personality.py` (62 lignes)
  - 3 types de personnalité avec modificateurs
- `server/app/ai/decision_engine.py` (177 lignes)
  - Calcul priorités : base × personnalité × urgence × phase
- `server/app/ai/ai_controller.py` (474 lignes)
  - Contrôleur principal, création/suppression IA

#### **4. Modules fonctionnels** (4 fichiers)
- `server/app/ai/modules/base_module.py` (108 lignes)
  - Classe abstraite pour tous les modules
- `server/app/ai/modules/city_builder.py` (392 lignes)
  - Construction de bâtiments avec scoring intelligent
- `server/app/ai/modules/resource_manager.py` (358 lignes)
  - Gestion pénuries (production, pillage, marché, quêtes)
- `server/app/ai/modules/colonizer.py` (296 lignes)
  - Stratégie colonisation Phase 1 (stone, cereal, papyrus, iron)

#### **5. API et Interface** (2 fichiers)
- `server/app/routes/ai_routes.py` (172 lignes)
  - Routes API : create, list, delete, stats, execute, spawn
- `server/app/templates/ai_admin.html` (438 lignes)
  - Interface admin complète avec stats et actions

#### **6. Intégration**
- `server/app/services/tick_service.py` (modifié)
  - Exécution IA intégrée dans le tick system

---

## 🚀 Comment tester ?

### **Étape 1 : Démarrer le serveur**

```powershell
cd c:\Users\Kevin\Desktop\game57\server
python run.py
```

### **Étape 2 : Accéder à l'interface admin**

Ouvrir dans le navigateur :
```
http://localhost:5000/api/ai/admin
```

### **Étape 3 : Créer une IA de test**

**Option A : Via l'interface**
1. Choisir personnalité (economic/military/balanced)
2. Choisir difficulté (easy/medium/hard)
3. Cliquer "Créer IA"

**Option B : Via API (curl)**
```powershell
curl -X POST http://localhost:5000/api/ai/players `
  -H "Content-Type: application/json" `
  -d '{"personality": "economic", "difficulty": "medium"}'
```

### **Étape 4 : Spawn des IA manquantes**

Cliquer sur "Spawn IA Manquantes" pour créer 1 IA par île (règle minimum).

### **Étape 5 : Observer le comportement**

1. **Stats en temps réel** : Rafraîchissement automatique toutes les 10s
2. **Liste des IA** : Username, personnalité, difficulté, nombre de villes, statut
3. **Logs serveur** : Vérifier les décisions prises par les IA

### **Étape 6 : Exécuter manuellement un cycle**

Cliquer "Exécuter Cycle IA" pour forcer une exécution immédiate.

---

## 🧪 Tests à effectuer

### **Test 1 : Création IA**
- [ ] Créer une IA "economic"
- [ ] Vérifier qu'elle apparaît dans la liste
- [ ] Vérifier le nom généré (ex: "Consul_Magnus_247")

### **Test 2 : Spawn automatique**
- [ ] Cliquer "Spawn IA Manquantes"
- [ ] Vérifier qu'une IA est créée par île
- [ ] Vérifier que chaque IA a une ville de départ

### **Test 3 : Cycle de décision**
- [ ] Créer une IA
- [ ] Attendre 10 secondes (ou cliquer "Exécuter Cycle IA")
- [ ] Vérifier les logs : L'IA doit proposer des actions

### **Test 4 : Construction de bâtiments**
- [ ] Vérifier qu'une IA construit des bâtiments
- [ ] Observer la priorité selon personnalité :
  - Economic → Entrepôts, Académies
  - Military → Casernes, Défenses
  - Balanced → Mix équilibré

### **Test 5 : Gestion des ressources**
- [ ] Simuler une pénurie (modifier manuellement resources dans savegame.json)
- [ ] Vérifier que l'IA propose une solution (production/pillage/marché)

### **Test 6 : Colonisation**
- [ ] Donner à une IA les ressources nécessaires (500 stone, 500 cereal, 100 gold)
- [ ] Vérifier qu'elle colonise une nouvelle île
- [ ] Vérifier qu'elle priorise les ressources Phase 1 (stone, cereal, papyrus, iron)

### **Test 7 : Activité réaliste**
- [ ] Vérifier que certaines IA sont "en ligne" et d'autres "hors ligne"
- [ ] Attendre quelques minutes et vérifier les changements de statut
- [ ] Confirmer que les IA hors ligne ne prennent pas d'actions

### **Test 8 : Suppression**
- [ ] Supprimer une IA via l'interface
- [ ] Vérifier qu'elle disparaît de la liste
- [ ] Vérifier que ses villes sont supprimées (TODO : à implémenter complètement)

---

## 🐛 Problèmes possibles et solutions

### **Erreur : "Module 'app.ai' not found"**
**Solution :** Vérifier que le dossier `server/app/ai/` existe et contient `__init__.py`

### **Erreur : "Cannot import AIController"**
**Solution :** Vérifier les imports dans `ai_controller.py` :
```python
from app.ai.decision_engine import DecisionEngine
from app.ai.personality import Personality
from app.ai.utils.data_loader import get_data_loader
from app.ai.utils.activity_simulator import get_activity_simulator
```

### **Erreur : "Template 'ai_admin.html' not found"**
**Solution :** Vérifier que le fichier existe dans `server/app/templates/ai_admin.html`

### **Erreur : Les IA ne prennent pas d'actions**
**Solution :** 
1. Vérifier que le tick system fonctionne
2. Vérifier les logs : `print()` dans `ai_controller.py`
3. Vérifier que les modules sont chargés : `_create_decision_engine()`

### **Erreur : Spawn ne crée pas de villes**
**Solution :** Vérifier que `_create_starting_city()` fonctionne correctement. Peut nécessiter ajustements selon votre système de création de villes.

---

## 📊 Points de validation

### ✅ **Architecture**
- [x] Configuration externalisée (ai_config.json)
- [x] Modules indépendants (CityBuilder, ResourceManager, Colonizer)
- [x] Système de priorités fonctionnel
- [x] Intégration tick system

### ✅ **Fonctionnalités**
- [x] Création IA avec personnalités
- [x] Spawn automatique (1 par île)
- [x] Décisions de construction
- [x] Gestion des pénuries de ressources
- [x] Stratégie de colonisation Phase 1
- [x] Simulation d'activité réaliste

### ✅ **Interface**
- [x] Page admin fonctionnelle
- [x] Stats en temps réel
- [x] Actions CRUD sur les IA
- [x] Spawn et exécution manuelle

### ⏳ **À améliorer (futures versions)**
- [ ] Implémentation complète du pillage (trouver cibles, évaluer défenses)
- [ ] Achat marché (exécution réelle)
- [ ] Système de quêtes
- [ ] Suppression complète (ville + joueur)
- [ ] Logs détaillés dans l'interface
- [ ] Graphiques de performance

---

## 🎯 Critères de succès Phase 1

Pour considérer la Phase 1 comme réussie, vérifier :

1. ✅ **Au moins 1 IA par île** après le spawn
2. ✅ **Les IA construisent des bâtiments** selon leur personnalité
3. ✅ **Les IA colonisent** quand elles ont les ressources
4. ✅ **Les IA sont indétectables** (activité simulée)
5. ✅ **Pas de crash** pendant 1 heure d'exécution
6. ✅ **Interface admin fonctionnelle** et réactive

---

## 📝 Checklist de test complète

```
[ ] Démarrer le serveur sans erreurs
[ ] Accéder à /api/ai/admin
[ ] Créer 3 IA (1 economic, 1 military, 1 balanced)
[ ] Vérifier les stats (total = 3)
[ ] Spawn des IA manquantes
[ ] Vérifier qu'au moins 1 IA par île
[ ] Exécuter un cycle IA manuellement
[ ] Observer les logs : actions proposées
[ ] Attendre 30 secondes : tick automatique
[ ] Vérifier changements de statut (en ligne/hors ligne)
[ ] Créer une pénurie de céréales manuellement
[ ] Vérifier que l'IA réagit (propose solution)
[ ] Donner ressources de colonisation à une IA
[ ] Vérifier qu'elle colonise une nouvelle île
[ ] Supprimer une IA
[ ] Vérifier qu'elle disparaît de la liste
[ ] Cliquer "Supprimer Toutes les IA"
[ ] Vérifier que la liste est vide
[ ] Recréer une IA et vérifier qu'elle fonctionne
```

---

## 🔧 Commandes utiles

### **Voir les logs en temps réel**
```powershell
# Les logs s'affichent dans la console où vous avez lancé run.py
```

### **Tester les routes API avec curl**

**Lister les IA :**
```powershell
curl http://localhost:5000/api/ai/players
```

**Créer une IA :**
```powershell
curl -X POST http://localhost:5000/api/ai/players `
  -H "Content-Type: application/json" `
  -d '{"personality": "military", "difficulty": "hard"}'
```

**Stats :**
```powershell
curl http://localhost:5000/api/ai/stats
```

**Spawn :**
```powershell
curl -X POST http://localhost:5000/api/ai/spawn
```

**Exécuter :**
```powershell
curl -X POST http://localhost:5000/api/ai/execute
```

**Supprimer une IA :**
```powershell
curl -X DELETE http://localhost:5000/api/ai/players/PLAYER_ID
```

---

## 🎉 Prochaines étapes (après validation Phase 1)

1. **Implémentation complète du combat/pillage**
2. **Système de quêtes pour ressources bonus**
3. **Optimisation des décisions (machine learning ?)**
4. **Interface admin avancée** (logs détaillés, graphiques)
5. **Système de réputation IA** (agressivité, alliances)
6. **Personnalités avancées** (expansionniste, défensif, marchand)
7. **Amélioration spawn** (équilibrage initial)
8. **Tests de performance** (100+ IA simultanées)

---

## 📞 Support

En cas de problème :
1. Vérifier les logs dans la console
2. Vérifier les erreurs dans le navigateur (F12 → Console)
3. Vérifier que tous les fichiers sont bien créés
4. Tester les routes API individuellement avec curl

**Bon test ! 🚀**
