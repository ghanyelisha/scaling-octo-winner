"""
Gunicorn configuration for Afah.

Usage:
    gunicorn --config gunicorn.conf.py wsgi:app
"""
import os

# ── Binding ───────────────────────────────────────────────────────────────────
# Override with env var for different environments, e.g.:
#   GUNICORN_BIND=0.0.0.0:5000 gunicorn --config gunicorn.conf.py wsgi:app
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# ── Workers ───────────────────────────────────────────────────────────────────
# Intentionally set to 1 for two reasons:
#   1. SQLite does not support concurrent writes — multiple workers would cause
#      database locking errors under load.
#   2. APScheduler runs as a background thread inside the worker process.
#      Multiple workers would each start their own scheduler, resulting in
#      duplicate reminder emails being sent.
# Switch to PostgreSQL + increase workers if you need to scale later.
workers = 1
worker_class = 'sync'

# Allow light I/O concurrency within the single worker (e.g. slow email sends
# don't block incoming HTTP requests).
threads = 2

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout = 30           # Kill worker if it doesn't respond within 30 s
graceful_timeout = 30  # Give in-flight requests 30 s to finish on restart
keepalive = 5          # Keep idle connections open for 5 s (reverse proxy)

# ── Logging ───────────────────────────────────────────────────────────────────
# '-' means stdout/stderr — captured by systemd, Docker, or your process manager
accesslog = '-'
errorlog  = '-'
loglevel  = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sus'

# ── Process ───────────────────────────────────────────────────────────────────
proc_name = 'afah'

# Don't advertise the Gunicorn version in response headers
server_version = 'Server'
