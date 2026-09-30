import re

with open('core/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = ['*']")

with open('core/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
