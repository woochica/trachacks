from setuptools import find_packages, setup

setup(
    name='WikiComments', version='1.0',
    packages=find_packages(),
    entry_points = {
        'trac.plugins': [
            'wikicomments = wikicomments.wikicomments',
        ],
    },
    eager_resources = [
        'wikicomments/htdocs/wikicomments.js',
        'wikicomments/htdocs/toolbar-comment-icon.png'
    ],
    package_data = { '': ['*.js', '*.png'] }
)
