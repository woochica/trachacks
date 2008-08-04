from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='ReportToDetailedRSS', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        ReportToDetailedRSS = ReportToDetailedRSS
    """,
    package_data={'ReportToDetailedRSS': ['templates/*.rss']},
)