from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='ValuePropagation', version='0.2', 
    author="Chris Nelson (Chris.Nelson@SIXNET.com)",
    packages=find_packages(exclude=['*.tests*']),
    url="http://trac-hacks.org/wiki/ValuePropagationPlugin",
    entry_points = """
        [trac.plugins]
        valuepropagation = valuepropagation
    """,
)

