import os
import django
import cherrypy

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.wsgi import application
from network.models import SystemSettings

settings = SystemSettings.load()
port = settings.server_port or 8000

cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': port,
    'engine.autoreload.on': False,
})

if settings.enable_ssl and settings.ssl_cert_path and settings.ssl_key_path:
    if os.path.exists(settings.ssl_cert_path) and os.path.exists(settings.ssl_key_path):
        cherrypy.config.update({
            'server.ssl_module': 'builtin',
            'server.ssl_certificate': settings.ssl_cert_path,
            'server.ssl_private_key': settings.ssl_key_path,
        })
        print(f"Starting Server on HTTPS port {port}...")
    else:
        print("SSL requested but files not found. Falling back to HTTP.")
        print(f"Starting Server on HTTP port {port}...")
else:
    print(f"Starting Server on HTTP port {port}...")

cherrypy.tree.graft(application, '/')

# Serve media files via cherrypy
from django.conf import settings as django_settings
if hasattr(django_settings, 'MEDIA_ROOT'):
    cherrypy.tree.mount(None, '/media', {'/': {'tools.staticdir.on': True, 'tools.staticdir.dir': str(django_settings.MEDIA_ROOT)}})
if hasattr(django_settings, 'STATIC_ROOT') and django_settings.STATIC_ROOT:
    cherrypy.tree.mount(None, '/static', {'/': {'tools.staticdir.on': True, 'tools.staticdir.dir': str(django_settings.STATIC_ROOT)}})


cherrypy.engine.start()
cherrypy.engine.block()
