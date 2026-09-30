import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("from import_export.admin import ImportExportModelAdmin", "from import_export.admin import ImportExportActionModelAdmin")
content = content.replace("class SubnetAdmin(ImportExportModelAdmin):", "class SubnetAdmin(ImportExportActionModelAdmin):")
content = content.replace("class IPAddressAdmin(ImportExportModelAdmin):", "class IPAddressAdmin(ImportExportActionModelAdmin):")
content = content.replace("class VlanAdmin(ImportExportModelAdmin):", "class VlanAdmin(ImportExportActionModelAdmin):")

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
