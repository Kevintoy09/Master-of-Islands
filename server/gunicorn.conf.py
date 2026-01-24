"""
Configuration Gunicorn pour Railway
"""
import os
import multiprocessing

# Nombre de workers (1 seul pour éviter les race conditions sur auto-tick)
# TODO: Passer à plusieurs workers avec Redis pour production à grande échelle
workers = 1
threads = 8  # Augmenté pour compenser (1 worker × 8 threads = 8 connexions concurrentes)

# Timeout
timeout = 120

# Bind - Utilise PORT de Railway ou 8000 par défaut
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
