import re

with open('core/templates/admin/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Change col-lg-9 to col-lg-12
content = content.replace('<div class="col-lg-9 col-12">', '<div class="col-lg-12 col-12">')

# Change col-lg-3 to col-lg-12 mt-4
content = content.replace('<div class="col-lg-3 col-12">', '<div class="col-lg-12 col-12 mt-3">')

with open('core/templates/admin/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
