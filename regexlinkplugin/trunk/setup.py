from setuptools import setup, find_packages
setup(
    name = "RegexLink",
    author = "Roel Harbers",
    license = "THE BEER-WARE LICENSE (Revision 42)",
    url = "http://trac-hacks.org/wiki/RegexLinkPlugin",
    description = "Trac plugin for creating external links based on regular expressions",
    version = "0.3",
    packages = find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        regex_link = RegexLink.regex_link
    """,
)
