from setuptools import find_packages, setup

setup(
    name='LuntTrac', version='1.1',
    author="David Roussel",
    description="A trac plugin to add Luntbuild builds to the trac timeline",
    packages=find_packages(exclude=['*.tests*']),
    package_data={'LuntTrac' : ['htdocs/*.css', 'htdocs/*.gif']},
    entry_points = """
[trac.plugins]
LuntTrac = LuntTrac.LuntTracPlugin
    """
)
