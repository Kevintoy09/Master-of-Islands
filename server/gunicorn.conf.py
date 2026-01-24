"""
Configuration Gunicorn pour Railway
"""
import multiprocessing

# Nombre de workers
workers = 2
threads = 4

# Timeout
timeout = 120

# Bind
bind = "0.0.0.0:8000"

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
