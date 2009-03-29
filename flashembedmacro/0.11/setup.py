from setuptools import setup

PACKAGE = 'TracFlashEmbedMacro'
VERSION = '0.9beta'
URL = 'http://trac-hacks.org/wiki/FlashEmbedMacro'

setup(  name=PACKAGE,
        install_requires='Trac >=0.11',
        description='Embedding flash content macro',
        keywords='trac wiki macro flash',
        version=VERSION,
        url = URL,
        license='BSD',
        author='Alexey Kinyov',
        author_email='rudy@05bit.com',
        packages=['tracflashembed'],
        long_description="""
        Plugin provides macro [[Embed(...)]] for embedding flash content into
        wiki pages.
        """,
        entry_points={'trac.plugins': '%s = tracflashembed' % PACKAGE},
)
