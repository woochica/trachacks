from setuptools import setup

setup(
    name="ExtLinkRewriter",
    version="0.3",
    packages=['ExtLinkRewriter'],
    entry_points = {'trac.plugins':
                    ['ExtLinkRewriter.provider = ExtLinkRewriter.provider',],},
    license = "BSD")

