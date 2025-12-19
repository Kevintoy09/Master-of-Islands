# Instructions pour déployer sur Railway en 2 services séparés

## Problème actuel
Railway a du mal à gérer Node.js + Python dans le même service.

## Solution : 2 services séparés

### Service 1 : Backend (Python/Flask)
1. Railway → New Service → Deploy from GitHub
2. Sélectionne Master-of-Islands
3. Root Directory : `server`
4. Variables :
   ```
   ENVIRONMENT=production
   SECRET_KEY=1az7ed0uhMKsVOcCkygLJ69I4rtlpSNUWqbFEPRHToB5AG28wfviYX3nmQjZDx
   CORS_ORIGINS=https://ton-frontend.railway.app
   ```

### Service 2 : Frontend (React - Static)
1. Railway → New Service → Deploy from GitHub  
2. Sélectionne Master-of-Islands
3. Root Directory : `client`
4. Variables :
   ```
   REACT_APP_API_URL=https://ton-backend.railway.app
   ```

### Alternative plus simple : Build React localement
1. Build React en local : `cd client && npm run build`
2. Flask servira le build React (comme actuellement en dev)
3. Un seul service Railway (Python seulement)
