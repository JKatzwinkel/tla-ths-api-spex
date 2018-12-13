from setuptools import setup, find_packages

VERSION = '0.1.1'

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
            ],
        )
