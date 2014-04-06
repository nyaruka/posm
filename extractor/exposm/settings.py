import yaml

settings = {}
admin_levels = {}

# source file definitions
settings_file = open('settings.yaml', 'rb')
admin_levels_file = open('admin_mapping.yaml', 'rb')

# update settings dictionary
settings.update(yaml.load(settings_file))
admin_levels.update(yaml.load(admin_levels_file))
