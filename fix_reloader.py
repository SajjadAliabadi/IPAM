import re

with open('run_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Turn off autoreloader
cherrypy_config = '''cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': port,
    'engine.autoreload.on': False,
})'''

content = content.replace("cherrypy.config.update({\n    'server.socket_host': '0.0.0.0',\n    'server.socket_port': port,\n})", cherrypy_config)

with open('run_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
