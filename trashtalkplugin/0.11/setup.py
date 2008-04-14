from setuptools import find_packages, setup

setup(
    name='TrashTalk',
    version='0.1',
    packages=['trashtalk'],
    package_data={ 'trashtalk' : ['htdocs/*.css'] },
    
    author='Tim Coulter',
    author_email='tim@timothyjcoulter.com',
    description='Logs URLs linking to tickets in order to show community impact.',
    url='http://trac-hacks.org/wiki/TrashTalkPlugin',
    
    classifiers=[
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac', 'Genshi >= 0.5.dev-r698,==dev'],
    
    entry_points = {
        'trac.plugins': ['trashtalk = trashtalk']
    }
    
)

