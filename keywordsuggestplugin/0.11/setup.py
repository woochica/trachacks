from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TracKeywordSuggest',
    version = '0.5.0',
    author = 'Dmitry Dianov',
    author_email = 'scratcha at google mail',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = "Add suggestions to ticket 'keywords' field",
    license = "BSD",
    url = 'http://trac-hacks.org/wiki/KeywordSuggestPlugin',
    packages=find_packages(exclude=['*.tests*']),
    package_data = { 'keywordsuggest': ['htdocs/js/*.js','htdocs/css/ui-darkness/*.css','htdocs/css/ui-darkness/images/*.gif'] },
    entry_points = {
        'trac.plugins': [
            'keywordsuggest = keywordsuggest.keywordsuggest'
        ]
    }
)
