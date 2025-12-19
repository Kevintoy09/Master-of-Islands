# 🚀 QUICK START - Déploiement Production

## Étapes Rapides (30 minutes)

### 1️⃣ Commit et Push (2 min)

```powershell
cd c:\Users\Kevin\Desktop\game56
git add .
git commit -m "feat: Configuration production Railway"
git push origin master
```

### 2️⃣ Railway Setup (5 min)

1. Aller sur [Railway.app](https://railway.app)
2. Se connecter avec GitHub
3. Créer un projet depuis `Kevintoy09/jeu-09-03-25`
4. Ajouter PostgreSQL : **+ New → Database → PostgreSQL**

### 3️⃣ Variables d'Environnement (3 min)

Dans Railway → Settings → Variables :

```bash
ENVIRONMENT=production
SECRET_KEY=GENERER_UNE_CLE_ALEATOIRE_LONGUE
CORS_ORIGINS=https://votre-domaine.com
MAX_CITIES_PER_PLAYER=5
TICK_INTERVAL_SECONDS=3600
LOG_LEVEL=INFO
REACT_APP_API_URL=${{RAILWAY_PUBLIC_DOMAIN}}
```

### 4️⃣ Déployer (5 min)

Railway déploie automatiquement. Attendre le build.

### 5️⃣ Migration Database (5 min)

Dans Railway Shell :
```bash
cd server
python -m app.migrations.migration_manager migrate
```

### 6️⃣ Test (2 min)

```
https://votre-url.railway.app/api/health
```

### 7️⃣ Domaine Custom (10 min)

1. Acheter domaine (Namecheap/OVH/Cloudflare)
2. Railway → Settings → Custom Domain
3. Configurer DNS (A/CNAME records)
4. Attendre propagation (5-30 min)

---

## ✅ C'EST FAIT !

Votre jeu est en production sur Railway avec PostgreSQL.

**URL temporaire** : Railway vous fournit une URL `.railway.app`  
**URL finale** : Votre domaine custom une fois DNS propagé

---

## 📊 Budget Mensuel

- **Railway Starter** : ~5$/mois (500h, suffisant pour beta)
- **Domaine** : ~1€/mois (12€/an)
- **Total** : ~6€/mois pour 10-50 joueurs

---

## 🐛 Problèmes ?

1. **Build fail** → Vérifier logs Railway
2. **502 Gateway** → Vérifier Gunicorn démarre (logs)
3. **Database error** → Vérifier PostgreSQL service actif
4. **CORS error** → Vérifier CORS_ORIGINS et protocole HTTPS

---

**Pour le guide complet** : voir `DEPLOYMENT_GUIDE_RAILWAY.md`
