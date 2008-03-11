#
#   Setup script for the Trac checklist plugin.
#

from setuptools import find_packages, setup

setup(
    name='TracChecklist', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        trac_checklist = trac_checklist
    """,
    package_data = {
        'trac_checklist': ['templates/*.html',
                           'htdocs/css/*.css',
                           'htdocs/images/*'],
    }
    url='http://trac-hacks.org/wiki/ChecklistPlugin',
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    maintainer='Rich Harkins',
    maintainer_email='rich@worldsinfinite.com',
    license='GPL',
    description="Makes checklists available anywhere there's a wiki",
)

