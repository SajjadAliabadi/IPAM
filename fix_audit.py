import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_audit = '''    list_display = ('timestamp', 'action', 'model_name', 'user', 'message')'''

new_audit = '''    list_display = ('timestamp', 'action_badge', 'model_name', 'user_display', 'message')

    def action_badge(self, obj):
        from django.utils.safestring import mark_safe
        color = '#64748b'
        icon = 'fa-info-circle'
        if obj.action == 'CREATE': color, icon = '#10b981', 'fa-plus-circle'
        elif obj.action == 'UPDATE': color, icon = '#3b82f6', 'fa-edit'
        elif obj.action == 'DELETE': color, icon = '#ef4444', 'fa-trash'
        elif obj.action == 'SCAN': color, icon = '#8b5cf6', 'fa-satellite-dish'
        elif obj.action == 'ASSIGN': color, icon = '#f59e0b', 'fa-user-tag'
        elif obj.action == 'SYSTEM': color, icon = '#475569', 'fa-cogs'
        
        return mark_safe(f'<span style="background: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"><i class="fas {icon}" style="margin-right: 4px;"></i> {obj.get_action_display()}</span>')
    action_badge.short_description = "Event Type"
    
    def user_display(self, obj):
        from django.utils.safestring import mark_safe
        if obj.user:
            return mark_safe(f'<div style="display:flex; align-items:center; gap:8px;"><div style="width:24px; height:24px; border-radius:50%; background:#e2e8f0; display:flex; align-items:center; justify-content:center; color:#475569;"><i class="fas fa-user" style="font-size:10px;"></i></div><span style="font-weight:600; color:#334155;">{obj.user.username}</span></div>')
        return mark_safe('<div style="display:flex; align-items:center; gap:8px;"><div style="width:24px; height:24px; border-radius:50%; background:#f1f5f9; display:flex; align-items:center; justify-content:center; color:#94a3b8;"><i class="fas fa-robot" style="font-size:10px;"></i></div><span style="font-style:italic; color:#64748b;">System Process</span></div>')
    user_display.short_description = "Initiator"'''

content = content.replace(old_audit, new_audit)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
