from setuptools import find_packages, setup

setup(
    name='SVN URLs',
    version='0.4',
    author='Jeff Hammel',
    description='Provide links to the actual URLs of svn versioned resources',
    license='GPL',
    packages=find_packages(exclude=['*.tests*']),
    package_data={'svnurls': ['templates/*.html']},
    install_requires=["Genshi>=0.5dev"],
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-0.5dev'],
    entry_points = """
    [trac.plugins]
    svnurls = svnurls
    """,
    )

