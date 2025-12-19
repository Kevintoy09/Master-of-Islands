# 🚀 GUIDE DE DÉPLOIEMENT PRODUCTION - IMPERIUM
## Railway + PostgreSQL + Domaine Custom

---

## 📋 TABLE DES MATIÈRES

1. [Préparation du Code](#1-preparation-du-code)
2. [Configuration Railway](#2-configuration-railway)
3. [Base de Données PostgreSQL](#3-base-de-donnees-postgresql)
4. [Configuration Domaine](#4-configuration-domaine)
5. [Migration des Données](#5-migration-des-donnees)
6. [Monitoring & Maintenance](#6-monitoring--maintenance)
7. [Plan de Lancement Beta](#7-plan-de-lancement-beta)

---

## ✅ 1. PRÉPARATION DU CODE

### 1.1 Vérifier les fichiers créés

Tous les fichiers suivants ont été créés automatiquement :

```
📦 Root
├── Procfile                    # Configuration Gunicorn
├── railway.json               # Configuration Railway
├── runtime.txt                # Version Python
├── .env.production            # Variables production
├── .env.development           # Variables dev
└── .gitignore                 # Fichiers à ignorer

📦 Server
├── requirements.txt           # Dépendances Python (mises à jour)
├── app/
│   ├── config/
│   │   └── database.py       # Connexion PostgreSQL
│   ├── models/
│   │   └── db_models.py      # Modèles SQLAlchemy
│   ├── migrations/
│   │   └── migration_manager.py  # Script de migration
│   ├── routes/
│   │   └── health_routes.py  # Health check
│   └── dual_data_manager.py  # Gestionnaire hybride

📦 Client
├── .env.production            # Config API production
├── .env.development           # Config API dev
└── src/config/
    └── api.config.ts          # Configuration API dynamique
```

### 1.2 Commit sur GitHub

```powershell
# Se placer dans le dossier du projet
cd c:\Users\Kevin\Desktop\game56

# Initialiser git si nécessaire
git init
git add .
git commit -m "feat: Configuration déploiement production Railway"

# Lier au repository (si pas déjà fait)
git remote add origin https://github.com/Kevintoy09/jeu-09-03-25.git
git branch -M master
git push -u origin master
```

---

## 🚂 2. CONFIGURATION RAILWAY

### 2.1 Créer le Projet Railway

1. **Aller sur [Railway.app](https://railway.app)**
2. **Se connecter avec GitHub**
3. **Cliquer sur "New Project"**
4. **Choisir "Deploy from GitHub repo"**
5. **Sélectionner `Kevintoy09/jeu-09-03-25`**

### 2.2 Ajouter PostgreSQL

1. Dans votre projet Railway, cliquer sur **"+ New"**
2. Sélectionner **"Database" → "PostgreSQL"**
3. Railway va automatiquement :
   - Créer la base de données
   - Générer `DATABASE_URL`
   - Lier la database au service

### 2.3 Configurer les Variables d'Environnement

Dans Railway, aller dans **Settings → Variables** et ajouter :

```bash
# Environment
ENVIRONMENT=production

# Secret Key (générer une clé aléatoire forte)
SECRET_KEY=VOTRE_CLE_SECRETE_SUPER_LONGUE_ET_ALEATOIRE

# CORS (votre futur domaine)
CORS_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# Game Config
MAX_CITIES_PER_PLAYER=5
TICK_INTERVAL_SECONDS=3600

# Performance
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
GUNICORN_TIMEOUT=120

# Logs
LOG_LEVEL=INFO

# React App (URL publique Railway)
REACT_APP_API_URL=${{RAILWAY_PUBLIC_DOMAIN}}
```

> **💡 Astuce** : Railway génère automatiquement `DATABASE_URL`, vous n'avez pas besoin de l'ajouter.

### 2.4 Générer une SECRET_KEY forte

```powershell
# Dans PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
```

Copier la clé générée et la mettre dans `SECRET_KEY`.

### 2.5 Configuration du Build

Railway devrait détecter automatiquement :
- **Builder**: Nixpacks
- **Build Command**: `cd client && npm install && npm run build`
- **Start Command**: `gunicorn --chdir server run:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

Si ce n'est pas le cas, vérifier que `railway.json` et `Procfile` sont bien présents.

### 2.6 Déployer

1. Railway va automatiquement déployer à chaque push sur `master`
2. Vous pouvez aussi déclencher manuellement : **Settings → Deployments → Deploy**
3. Attendre que le build se termine (~3-5 minutes)

### 2.7 Vérifier le Déploiement

Une fois déployé, Railway vous donnera une URL du type :
```
https://jeu-09-03-25-production.up.railway.app
```

Tester le health check :
```
https://votre-url.railway.app/api/health
```

Résultat attendu :
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "postgresql",
  "version": "1.0.0"
}
```

---

## 🐘 3. BASE DE DONNÉES POSTGRESQL

### 3.1 Migration Initiale JSON → PostgreSQL

Une fois le déploiement réussi, connectez-vous en SSH à Railway :

```bash
# Dans Railway CLI (à installer si nécessaire)
railway link
railway run python -m app.migrations.migration_manager migrate
```

Ou utilisez le **Railway Shell** dans l'interface web :
1. Aller dans votre service
2. Cliquer sur **"Shell"**
3. Exécuter :
```bash
cd server
python -m app.migrations.migration_manager migrate
```

### 3.2 Que fait la Migration ?

Le script migre automatiquement :
- ✅ Joueurs (`players.json` → `players`)
- ✅ Villes (`savegame.json` → `cities`)
- ✅ Bâtiments (`savegame.json` → `buildings`)
- ✅ Recherches (`research.json` → `research`)
- ✅ Unités (`savegame.json` → `units`)
- ✅ Héros (`player_heroes.json` → `heroes`)
- ✅ Batailles (`battlesv2.json` → `battles`)
- ✅ Transports (`transports.json` → `transports`)

### 3.3 Backup PostgreSQL → JSON (optionnel)

Pour exporter les données en JSON (backup ou développement local) :

```bash
python -m app.migrations.migration_manager export
```

### 3.4 Accéder à PostgreSQL

Railway fournit un accès direct à la base :
1. Aller dans **PostgreSQL service → Data**
2. Ou utiliser un client SQL avec les credentials fournis

---

## 🌐 4. CONFIGURATION DOMAINE

### 4.1 Acheter un Domaine

**Recommandations** (prix annuel ~10-15€) :
- [Namecheap](https://www.namecheap.com)
- [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/)
- [OVH](https://www.ovh.com)
- [Gandi](https://www.gandi.net)

Exemples de noms :
- `imperium-game.com`
- `play-imperium.com`
- `imperium-strategy.com`

### 4.2 Configurer le Domaine dans Railway

1. Dans Railway, aller dans **Settings → Networking**
2. Cliquer sur **"Custom Domain"**
3. Ajouter votre domaine : `imperium-game.com`
4. Railway vous donnera un **CNAME** à configurer

### 4.3 Configurer les DNS

Dans votre registrar (Namecheap, OVH, etc.) :

**Type A (racine)** :
```
Type: A
Host: @
Value: [IP fournie par Railway]
TTL: Automatic
```

**Type CNAME (www)** :
```
Type: CNAME
Host: www
Value: [domaine Railway fourni]
TTL: Automatic
```

### 4.4 Activer SSL/TLS

Railway active automatiquement HTTPS avec Let's Encrypt.
Après propagation DNS (5-30 minutes), votre site sera accessible en HTTPS.

### 4.5 Redirection www → non-www (optionnel)

Ajouter dans Railway ou via Cloudflare une redirection :
```
www.imperium-game.com → imperium-game.com
```

### 4.6 Mettre à jour CORS

Une fois le domaine actif, mettre à jour dans Railway :
```bash
CORS_ORIGINS=https://imperium-game.com,https://www.imperium-game.com
```

---

## 📊 5. MONITORING & MAINTENANCE

### 5.1 Surveillance Railway

Railway fournit automatiquement :
- **Metrics** : CPU, RAM, Réseau
- **Logs** : Accès en temps réel
- **Alerts** : Notifications si le service crash

### 5.2 Logs Applicatifs

Pour voir les logs en temps réel :
```bash
railway logs --follow
```

Ou dans l'interface Railway : **Deployments → Logs**

### 5.3 Coûts Estimés (Railway)

**Forfait Starter (~5$/mois)** :
- 500 heures d'exécution
- 100 GB de bande passante
- Suffisant pour 10-50 joueurs

**Forfait Developer (~20$/mois)** :
- Ressources illimitées
- Priorité support
- Pour 50-500 joueurs

**PostgreSQL** : Inclus dans le forfait

### 5.4 Scaling

Pour augmenter les performances :
1. Railway → Settings → Resources
2. Augmenter les **Workers** Gunicorn :
```bash
GUNICORN_WORKERS=4  # Au lieu de 2
```
3. Upgrader le plan Railway si nécessaire

### 5.5 Backups Automatiques

Railway sauvegarde PostgreSQL automatiquement.
Pour des backups personnalisés :

```bash
# Script backup (à exécuter régulièrement)
railway run python -m app.migrations.migration_manager export
```

---

## 🎯 6. PLAN DE LANCEMENT BETA

### SEMAINE 1-2 : Déploiement Technique

- [x] ✅ Configuration Railway (FAIT)
- [x] ✅ Migration PostgreSQL (À TESTER)
- [x] ✅ Configuration domaine (À FAIRE)
- [ ] 🔄 Tests de charge (10-20 joueurs simultanés)
- [ ] 🔄 Monitoring actif

### SEMAINE 3-4 : Tests & Optimisations

- [ ] 🎮 Tests gameplay complets
- [ ] 🐛 Correction bugs critiques
- [ ] ⚡ Optimisation performances
- [ ] 📱 Tests mobile
- [ ] 📝 Rédaction tutoriel joueur

### MOIS 2 : Lancement Beta

#### Phase 1 : Alpha Fermée (5-10 joueurs)
- Inviter 5-10 joueurs de confiance
- Feedback intensif
- Correction rapide des bugs

#### Phase 2 : Beta Ouverte (20-50 joueurs)
- Publication sur :
  - Reddit (`/r/WebGames`, `/r/incremental_games`)
  - Discord (serveurs de jeux de stratégie)
  - Twitter/X
  - IndieDB
- Monitoring actif
- Support joueurs

#### Communication

**Message Beta** :
```
🏛️ IMPERIUM - Jeu de Stratégie Antique BETA

Construisez votre empire romain, gérez vos ressources,
formez des armées et dominez le monde antique !

✨ Features:
- Gestion de villes et ressources
- Combats tactiques hexagonaux
- Système de héros et recherches
- 100% gratuit et multijoueur

🎮 Jouez maintenant : https://imperium-game.com
📊 Beta ouverte - Vos retours comptent !
```

---

## 🚨 TROUBLESHOOTING

### Problème : Build échoue

**Solution** :
1. Vérifier les logs Railway
2. Tester en local : `npm run build` dans `client/`
3. Vérifier `requirements.txt` et `package.json`

### Problème : 502 Bad Gateway

**Solution** :
1. Vérifier que Gunicorn démarre : Railway Logs
2. Vérifier `PORT` est bien utilisé : `--bind 0.0.0.0:$PORT`
3. Augmenter timeout si nécessaire

### Problème : Database connection failed

**Solution** :
1. Vérifier `DATABASE_URL` dans Railway Variables
2. Vérifier PostgreSQL service est actif
3. Tester connexion : `railway run python -c "import os; print(os.getenv('DATABASE_URL'))"`

### Problème : CORS errors

**Solution** :
1. Vérifier `CORS_ORIGINS` inclut votre domaine
2. Vérifier protocole HTTPS
3. Clear cache navigateur

---

## 📞 SUPPORT & RESSOURCES

- **Railway Docs** : https://docs.railway.app
- **PostgreSQL Docs** : https://www.postgresql.org/docs/
- **Flask Docs** : https://flask.palletsprojects.com/
- **React Docs** : https://react.dev

---

## ✅ CHECKLIST FINALE

Avant le lancement beta :

- [ ] ✅ Code déployé sur Railway
- [ ] ✅ PostgreSQL configuré et migré
- [ ] ✅ Domaine custom configuré et actif
- [ ] ✅ SSL/HTTPS actif
- [ ] ✅ Health check répond
- [ ] ✅ Test de connexion joueur
- [ ] ✅ Test création ville
- [ ] ✅ Test combat
- [ ] ✅ Test recherche
- [ ] ✅ Test transport ressources
- [ ] ✅ Monitoring actif
- [ ] ✅ Backup configuré

---

## 🎉 PROCHAINES ÉTAPES

1. **Immédiat** :
   - Commit et push le code sur GitHub
   - Déployer sur Railway
   - Tester le health check

2. **Cette semaine** :
   - Acheter le domaine
   - Migrer les données vers PostgreSQL
   - Tests intensifs

3. **Semaine prochaine** :
   - Lancement alpha fermée (5-10 joueurs)
   - Collecte feedback
   - Optimisations

4. **Mois prochain** :
   - Beta ouverte (20-50 joueurs)
   - Communication communauté
   - Scaling si nécessaire

---

**Bon courage pour le lancement ! 🚀**

Si vous avez des questions ou rencontrez des problèmes, n'hésitez pas à demander.
