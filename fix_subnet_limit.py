import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("if len(hosts) > 4096:", "if len(hosts) > 65536:")
content = content.replace("hosts = hosts[:4096]", "hosts = hosts[:65536]")
content = content.replace("Cap at 4096", "Cap at 65536")

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
