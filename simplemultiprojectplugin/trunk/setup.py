from setuptools import setup

setup(
    name='SimpleMultiProject',
    version='0.0.3',
    packages=['simplemultiproject'],
    package_data={
        'simplemultiproject' : [
            'templates/*.html',
            'htdocs/*.js',
            'htdocs/css/*.css'
        ]
    },
    author = 'Christopher Paredes',
    author_email='jesuchristopher@gmail.com',
    maintainer = "falkb",
    license='GPL',
    url='http://trac-hacks.org/wiki/SimpleMultiProject',
    description='Simple Project',
    long_description='Simple Project',
    keywords='Simple Project',
    entry_points = {'trac.plugins': ['simplemultiproject = simplemultiproject']}
)