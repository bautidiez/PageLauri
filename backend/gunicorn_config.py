# Gunicorn Configuration for Production
# Uso: gunicorn -c gunicorn_config.py "app:app"

import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2  # Fixed to 2 for Render Free Tier to avoid resource exhaustion
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'  # stdout
errorlog = '-'   # stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'elvestuario_app'

# Server Mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (descomentar si usas HTTPS)
# keyfile = '/path/to/keyfile.pem'
# certfile = '/path/to/certfile.pem'
