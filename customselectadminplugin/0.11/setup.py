from setuptools import setup

setup(name='CustomSelectAdmin',
      version='0.3',
      packages=['CustomSelectAdmin'],
      package_data={'CustomSelectAdmin' : ['templates/*.html']},
      author='Jimmy Theis',
      author_email='jet.he.is@gmail.com',
      description='Modify custom select fields for tickets in an admin panel within Trac.',
      long_description=open('README.txt').read(),
      url='http://www.sixfeetup.com',
      license='BSD',
      entry_points={'trac.plugins': ['CustomSelectAdmin = CustomSelectAdmin']},
)
