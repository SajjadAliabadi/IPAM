import re

with open('core/static/js/custom_ui_overrides.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Remove the hardcoded background style in JS so CSS can handle it!
js = js.replace('jazzyActions.style.background = "#f8fafc";', '')
js = js.replace('jazzyActions.style.borderTop = "1px solid #e2e8f0";', '')

with open('core/static/js/custom_ui_overrides.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('Done')
