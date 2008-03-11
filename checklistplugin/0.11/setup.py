#
#   Setup script for the Trac checklist plugin.
#

from setuptools import find_packages, setup

setup(
    name='TracChecklist', version='1.1',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        trac_checklist = trac_checklist
    """,
)

