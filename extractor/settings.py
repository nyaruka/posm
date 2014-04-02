import yaml

settings = {}
admin_levels = {}

# source file definitions
sources_file = open('sources.yaml', 'rb')
admin_levels_file = open('admin_mapping.yaml', 'rb')

# update settings dictionary
settings.update(yaml.load(sources_file))
admin_levels.update(yaml.load(admin_levels_file))
