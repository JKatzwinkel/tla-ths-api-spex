from setuptools import setup

setup(
        name='thsapi',
        version='0.0.1',
        packages=['thsapi'],
        include_package_data=True,
        install_requires=[
            'flask',
            'flask-sqlalchemy',
            'couchdb',
            ],
        )
