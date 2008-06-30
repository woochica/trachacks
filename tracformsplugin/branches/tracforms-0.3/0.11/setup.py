
from setuptools import find_packages, setup

setup(
    name="TracForms",
    description='Provides forms on any page with a wiki',
    version="0.3",
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    license='GPL',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = '''
        [trac.plugins]
        tracforms = tracforms
    ''')

