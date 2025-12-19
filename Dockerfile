# Build stage avec Node.js pour compiler React
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY client/package*.json ./client/
RUN cd client && npm ci --prefer-offline --no-audit

COPY client/ ./client/
RUN cd client && npm run build

# Production stage avec Python
FROM python:3.11-slim

WORKDIR /app

# Copier requirements et installer les dépendances Python
COPY server/requirements.txt ./server/
RUN pip install --no-cache-dir -r server/requirements.txt

# Copier le code serveur
COPY server/ ./server/

# Copier le build React depuis le stage précédent
COPY --from=frontend-builder /app/client/build ./server/static_frontend

# Créer le dossier gamedata (sera monté comme volume)
RUN mkdir -p /app/server/gamedata

# Port exposé
EXPOSE 8000

# Démarrer avec gunicorn
CMD ["sh", "-c", "cd server && gunicorn -c gunicorn.conf.py run:app"]
