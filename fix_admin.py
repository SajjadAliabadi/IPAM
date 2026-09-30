import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix IPRequestAdmin
ip_req_correct = '''    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists():
            return (
                ('Request Details', {'fields': ('user', 'hostname', 'subnet', 'reason')}),
                ('Admin Action', {'fields': ('status', 'assigned_ip', 'admin_comment')}),
            )
        else:
            return (
                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
            )'''

# We need to find IPRequestAdmin's current corrupted get_fieldsets
# It starts with def get_fieldsets(self, request, obj=None): inside IPRequestAdmin
# and ends with         else:\n            return (\n                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),\n            )

regex = r"(?s)(class IPRequestAdmin.*?    def get_fieldsets\(self, request, obj=None\):.*?    else:\s*return \(\s*\('IP Request', \{'fields': \('subnet', 'hostname', 'reason'\)\}\),\s*\))"

match = re.search(regex, content)
if match:
    original_block = match.group(1)
    # We just want to replace from def get_fieldsets to the end of that match.
    # Actually, simpler: regex match the exact corrupted block
    bad_block = re.search(r"(?s)    def get_fieldsets\(self, request, obj=None\):.*?else:\s*return \(\s*\('IP Request', \{'fields': \('subnet', 'hostname', 'reason'\)\}\),\s*\)", original_block).group(0)
    
    content = content.replace(bad_block, ip_req_correct, 1) # Only replace first occurrence (IPRequestAdmin)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
