import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the 256 limit
old_code = '''        hosts = list(net.hosts())
        if len(hosts) > 256:
            hosts = hosts[:256]
            
        ip_strs = [str(host) for host in hosts]'''

new_code = '''        hosts = list(net.hosts())
        # Cap at 4096 to prevent memory exhaustion on accidentally large subnets (e.g. /8),
        # but fully support /23 (512), /22 (1024), /21 (2048)
        if len(hosts) > 4096:
            hosts = hosts[:4096]
            
        ip_strs = [str(host) for host in hosts]'''

content = content.replace(old_code, new_code)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
