# Configuration Gunicorn pour Railway
import multiprocessing

workers = 2
threads = 4
worker_class = 'gthread'
timeout = 120

# Logging vers stdout/stderr
accesslog = '-'
errorlog = '-'
loglevel = 'info'
