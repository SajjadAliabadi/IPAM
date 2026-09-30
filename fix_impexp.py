import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("from import_export.admin import ImportExportModelAdmin\nclass", "class")
content = "from import_export.admin import ImportExportModelAdmin\n" + content

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
