import re

with open('core/static/css/custom_admin.css', 'r', encoding='utf-8') as f:
    css = f.read()

def replace_with_not_dark(match):
    selector = match.group(1).strip()
    # Split by comma if there are multiple selectors
    selectors = [s.strip() for s in selector.split(',')]
    new_selectors = []
    for s in selectors:
        if s.startswith('body'):
            new_selectors.append(s.replace('body', 'body:not(.dark-mode)'))
        else:
            new_selectors.append(f"body:not(.dark-mode) {s}")
    return ", ".join(new_selectors) + " {"

# Regex to find selectors before {
css = re.sub(r'^([^\{\}\n]+)\s*\{', replace_with_not_dark, css, flags=re.MULTILINE)

# Some selectors might be indented, but let's fix the specific hardcoded ones manually
css = css.replace("body:not(.dark-mode) body:not(.dark-mode)", "body:not(.dark-mode)")

# To be absolutely sure, we can also add dark-mode overrides at the bottom
dark_overrides = '''
/* Dark Mode Specific Overrides */
body.dark-mode #jazzy-actions {
    background-color: #1e293b !important;
    border-top: 1px solid #334155 !important;
}
body.dark-mode .card, body.dark-mode #changelist, body.dark-mode #change-list-filters {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
}
body.dark-mode .card-header {
    background-color: #0f172a !important;
    border-bottom: 1px solid #334155 !important;
}
body.dark-mode .content-wrapper {
    background-color: #0f172a !important;
}
body.dark-mode .form-control, body.dark-mode .select2-selection {
    background-color: #334155 !important;
    border-color: #475569 !important;
    color: #f8fafc !important;
}
body.dark-mode input.form-control:focus, body.dark-mode select.form-control:focus, body.dark-mode textarea.form-control:focus {
    background-color: #1e293b !important;
}
body.dark-mode #result_list tbody tr td, body.dark-mode #result_list tbody tr th {
    background-color: #1e293b !important;
    color: #f8fafc !important;
}
body.dark-mode #result_list thead th {
    background-color: #0f172a !important;
    color: #cbd5e1 !important;
}
body.dark-mode #result_list tbody tr:hover td, body.dark-mode #result_list tbody tr:hover th {
    background-color: #334155 !important;
}
body.dark-mode ul.checkbox-select-multiple li, body.dark-mode .field-check_methods ul li {
    background-color: #334155 !important;
    border-color: #475569 !important;
}
body.dark-mode .nav-tabs .nav-link:hover:not(.active) {
    background: #334155 !important;
    color: #f8fafc !important;
}
'''
css += dark_overrides

with open('core/static/css/custom_admin.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('Done')
