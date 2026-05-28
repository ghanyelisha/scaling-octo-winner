"""
WSGI entry point for production servers (Gunicorn, uWSGI, etc.).

Run with:
    gunicorn wsgi:app
    gunicorn --config gunicorn.conf.py wsgi:app
"""
from app import create_app

app = create_app()
