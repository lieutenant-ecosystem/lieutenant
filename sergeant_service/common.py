import os


def is_production_environment():
    return os.environ.get('ENVIRONMENT') == 'production'


def is_test_environment():
    return not is_production_environment()
