"""
WSGI config for backend project.

- Exposes the WSGI callable as a module-level variable named `application`.
- Used for traditional HTTP deployments (not ASGI/Channels).
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Standard WSGI application for HTTP servers (e.g., Gunicorn, uWSGI)
application = get_wsgi_application()
