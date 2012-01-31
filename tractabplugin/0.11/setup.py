from setuptools import setup

setup(name='TracTab',
      version='0.1.5',
      license='BSD',
      author='Bobby Smith',
      author_email='bobbysmith007@gmail.com',
      maintainer='Ryan J Ollos',
      maintainer_email='ryan.j.ollos.@gmail.com',
      packages=['tractab'],
      package_data={'tractab' : ['templates/*.html']},
      entry_points={'trac.plugins': 'tractab = tractab'},
)

