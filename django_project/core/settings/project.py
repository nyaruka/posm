from .contrib import *

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.',
        # Or path to database file if using sqlite3.
        'NAME': '',
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        # Empty for localhost through domain sockets or '127.0.0.1' for
        # localhost through TCP.
        'HOST': '',
        # Set to empty string for default.
        'PORT': '',
    }
}

# Project apps
INSTALLED_APPS += (
)

# Set debug to false for production
DEBUG = TEMPLATE_DEBUG = False


PIPELINE_JS = {
    'contrib': {
        'source_filenames': (
            'js/jquery-1.11.0.min.js',
            'js/csrf-ajax.js',
            'js/underscore-min.js'
        ),
        'output_filename': 'js/contrib.js',
    }
}

PIPELINE_CSS = {
    'contrib': {
        'source_filenames': (
            #
        ),
        'output_filename': 'css/contrib.css',
        'extra_context': {
            'media': 'screen, projection',
        },
    }
}
