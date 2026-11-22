"""
WSGI config for EstateProject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EstateProject.settings')

django.setup()


def _boot_maintenance():
    """Free-tier safety net: ensure tables exist and demo data is present
    before the first request. Idempotent — no-ops in milliseconds when the
    database is already up to date. REMOVE once PostgreSQL + CI-run
    migrations land (Phase 1B)."""
    try:
        call_command("migrate", "--no-input", verbosity=0)
        call_command("seed_demo", verbosity=0)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Boot maintenance failed — continuing anyway")


_boot_maintenance()

application = get_wsgi_application()
