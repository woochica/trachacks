from setuptools import find_packages, setup

setup(
    name='EasyPoll',
    version='0.1.1',
    author='Pankaj Meena',
    author_email='hi.amigo@gmail.com',
    keywords='poll, easypoll, 0.11, mysql db, google charts',
    description='Fully featured Database driven poll plugin with permission controlls for voting and poll creation. Google charts for showing poll results.',
    url='',
    license='BSD',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        EasyPoll = EasyPoll
    """,
    package_data={'EasyPoll': [ 'templates/*.html', 
                                'htdocs/css/*.css'
                              ]},
)