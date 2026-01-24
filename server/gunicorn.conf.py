"""
Configuration Gunicorn pour Railway
"""
import os
import multiprocessing

# Nombre de workers
workers = 2
threads = 4

# Timeout
timeout = 120

# Bind - Utilise PORT de Railway ou 8000 par défaut
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
