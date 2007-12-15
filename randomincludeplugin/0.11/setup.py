from setuptools import setup

setup(
    name='TracRandomInclude',
    version='0.1',
    packages=['randominclude'],
    package_data={ 'randominclude': [  ]},
    description="Macros to include random items from specially formatted pages",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
                'randominclude.randomquote = randominclude.randomquote',
                'randominclude.randomitem = randominclude.randomitem',
                ],
    }
)
      
