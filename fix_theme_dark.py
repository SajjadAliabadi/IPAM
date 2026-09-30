import re

with open('network/middleware.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_theme_logic = '''                    settings.JAZZMIN_UI_TWEAKS['dark_mode_theme'] = sys_settings.theme
                    settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-dark'
                    settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
                    settings.JAZZMIN_UI_TWEAKS['accent'] = 'accent-primary'
                    settings.JAZZMIN_UI_TWEAKS['navbar_class'] = 'navbar-dark'
                else:
                    settings.JAZZMIN_UI_TWEAKS['dark_mode_theme'] = None
                    settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-white navbar-light'
                    settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
                    settings.JAZZMIN_UI_TWEAKS['accent'] = 'accent-primary'
                    settings.JAZZMIN_UI_TWEAKS['navbar_class'] = 'navbar-light'
            else:
                settings.JAZZMIN_UI_TWEAKS.pop('theme', None)
                settings.JAZZMIN_UI_TWEAKS.pop('dark_mode_theme', None)
                settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-white navbar-light'
                settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
'''

new_theme_logic = '''                    settings.JAZZMIN_UI_TWEAKS['dark_mode_theme'] = sys_settings.theme
                    settings.JAZZMIN_UI_TWEAKS['body_classes'] = 'dark-mode'
                    settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-dark'
                    settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
                    settings.JAZZMIN_UI_TWEAKS['accent'] = 'accent-primary'
                else:
                    settings.JAZZMIN_UI_TWEAKS['dark_mode_theme'] = None
                    settings.JAZZMIN_UI_TWEAKS['body_classes'] = ''
                    settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-white navbar-light'
                    settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
                    settings.JAZZMIN_UI_TWEAKS['accent'] = 'accent-primary'
            else:
                settings.JAZZMIN_UI_TWEAKS.pop('theme', None)
                settings.JAZZMIN_UI_TWEAKS.pop('dark_mode_theme', None)
                settings.JAZZMIN_UI_TWEAKS['body_classes'] = ''
                settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-white navbar-light'
                settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
'''

content = content.replace(old_theme_logic, new_theme_logic)

with open('network/middleware.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
