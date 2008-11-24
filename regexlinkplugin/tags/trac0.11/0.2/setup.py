from setuptools import setup, find_packages
setup(
    name = "RegexLink",
    version = "0.2",
    packages = find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        regex_link = RegexLink.regex_link
    """,
)
