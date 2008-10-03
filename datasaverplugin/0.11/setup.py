
from setuptools import find_packages, setup

setup(
    name='DataSaverPlugin',
    version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points="""
        [trac.plugins]
        datasaver = datasaver
    """,
    package_data={'datasaver': ['js/*.js', 'css/*.css']},
)

