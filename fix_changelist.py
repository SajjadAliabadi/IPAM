import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_list = "if 'subnet__id__exact' not in request.GET and 'q' not in request.GET:"
new_list = "if 'subnet__id__exact' not in request.GET and 'q' not in request.GET and 'status__exact' not in request.GET:"

content = content.replace(old_list, new_list)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
