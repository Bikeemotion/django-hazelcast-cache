import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name = 'django-hazelcast-cache',
    version = '0.1',
    packages = find_packages(),
    include_package_data = True,
    license = 'BSD License',
    description = 'Django hazelcast cache',
    long_description = README,
    url = '',
    author = 'Nuno Silva',
    author_email = 'nsilva@bikeemotion.com',
    install_requires=[
        'Django>=1.7',
    ],
)