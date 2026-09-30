import re

with open('core/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import_export to INSTALLED_APPS
content = content.replace("'network',", "'network',\n    'import_export',")

# Add MEDIA configuration
media_config = '''
# Media files (Uploads like logos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
'''
if 'MEDIA_URL' not in content:
    content += media_config

# Ensure JAZZMIN_UI_TWEAKS exists so we can modify it at runtime
ui_tweaks = '''
JAZZMIN_UI_TWEAKS = {
    "theme": "default",
}
'''
if 'JAZZMIN_UI_TWEAKS' not in content:
    content = content.replace("JAZZMIN_SETTINGS = {", ui_tweaks + "\nJAZZMIN_SETTINGS = {")

with open('core/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
