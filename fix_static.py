import re

with open('core/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

static_root = "STATIC_ROOT = BASE_DIR / 'staticfiles'"
if "STATIC_ROOT" not in content:
    content = content.replace("STATIC_URL = 'static/'", "STATIC_URL = 'static/'\n" + static_root)

with open('core/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
