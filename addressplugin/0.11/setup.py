from setuptools import setup

setup(
    author = 'RottenChester',
    author_email = 'rottenchester@gmail.com',
    url = 'http://trac-hacks.org/wiki/AddressPlugin',
    license = 'bsd',
    name='TracAddressMacro',
    version='0.1',
    packages=['address'],
    package_data={ 'address': [  ]},
    description="Macro to render maps of addresses embedded in pages",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
                'address.macro = address.macro',
                ],
    }
)
      
