from setuptools import setup

install_requires = [
    'pytz>=2019.1', 'mailjet-rest==1.3.3', 'Django>=2.2.0', 'django-nested-admin==3.3.0',
    'djangorestframework>=3.9.0', 'celery>=4.0.0', 'requests>=2.0.0', 'Faker>=2.0.0',
    'factory-boy>=2.0.0'
]

setup(install_requires=install_requires, long_description_content_type='text/x-rst')
