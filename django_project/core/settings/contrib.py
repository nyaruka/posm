from .base import *

# Extra installed apps
INSTALLED_APPS += (
    # 'raven.contrib.django',  # enable Raven plugin
    'south',
    'pipeline',
    'rest_framework'
)

# use underscore template function
PIPELINE_TEMPLATE_FUNC = '_.template'

# enable cached storage - requires uglify.js (node.js)
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# django rest framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    )
}
