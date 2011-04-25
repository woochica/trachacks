from setuptools import find_packages, setup

extra = {}

setup(
    name = 'TracCrowdAuthPlugin',
    version = "0.1",
    description = "Trac Crowd Auth",
    author = "Richard Liao",
    author_email = "richard.liao.i@gmail.com",
    url = "http://trac-hacks.org/wiki/TracCrowdAuthPlugin",
    license = "BSD",
    packages = find_packages(exclude=['ez_setup', 'examples', 'tests*']),
    include_package_data = True,
    package_data = { 'crowdauth': [ '*.txt', ] },
    zip_safe = False,
    keywords = "trac  crowd auth plugin",
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = ['TracAccountManager'],
    dependency_links = [
        "http://trac-hacks.org/svn/accountmanagerplugin/trunk/#egg=TracAccountManager",
    ],
    entry_points = """
    [trac.plugins]
    crowdauth = crowdauth.crowd_auth
    """,
    **extra
    )

