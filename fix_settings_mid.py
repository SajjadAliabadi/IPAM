import re

with open('core/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("'network.middleware.TimezoneMiddleware',", "'network.middleware.TimezoneMiddleware',\n    'network.middleware.DynamicThemeMiddleware',")

with open('core/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
