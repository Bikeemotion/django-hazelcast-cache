DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

INSTALLED_APPS = [
    'django_nose',
    'tests.testapp',
]

ROOT_URLCONF = 'tests.urls'

SECRET_KEY = "shh...it's a seakret"

CACHES = {
    'default': {
        'BACKEND': 'hazelcast_cache.HazelcastCache',
        'LOCATION': ['172.17.0.6:5701'],
        'OPTIONS': {
            'GROUP_NAME': 'dev',
            'GROUP_PASSWORD': 'dev-pass',
            'MAP_KEY': 'test'
        },
    },
}
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
MIDDLEWARE_CLASSES = tuple()
