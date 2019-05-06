from setuptools import setup, find_packages

VERSION = '0.1.101'

setup(
        name='thsapi',
        version=VERSION,
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            'flask',
            'flask-sqlalchemy',
            'flask-cors',
            'couchdb',
            'SQLAlchemy>=1.3.0',
            'Jinja2>=2.10.1',
            ],
        )
