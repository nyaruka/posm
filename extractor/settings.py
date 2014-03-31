import yaml

settings = {}

# source file definitions
sources_file = open('sources.yaml', 'rb')

# update settings dictionary
settings.update(yaml.load(sources_file))
