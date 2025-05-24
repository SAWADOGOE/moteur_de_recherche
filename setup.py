from setuptools import setup, find_packages

setup(
    name="moteur-de-recherche",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'beautifulsoup4',
        'requests',
        'nltk',
        'scikit-learn',
        'python-dotenv',
        'google-api-python-client',
        'gunicorn'
    ],
) 