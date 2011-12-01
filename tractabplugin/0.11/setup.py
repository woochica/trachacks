from setuptools import setup

setup(name='TracTab',
      version='0.1.4',
      packages=['tractab'],
      package_data={'tractab' : ['templates/*.html']},
      entry_points={'trac.plugins': 'tractab = tractab'},
)

