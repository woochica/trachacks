from setuptools import find_packages, setup

setup(
        name='TracMath', version='0.1',
        packages=find_packages(exclude=['*.tests*']),
        entry_points="""
                    [trac.plugins]
                    tracmath = tracmath
                    """,
    )

