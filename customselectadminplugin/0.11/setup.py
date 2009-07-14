from setuptools import setup

setup(name='CustomSelectAdmin',
      version='0.1',
      packages=['CustomSelectAdmin'],
      zip_safe=False,
      author='Jimmy Theis',
      description='Modify custom select fields for tickets in an admin panel',
      url='http://www.sixfeetup.com',
      entry_points={'trac.plugins': ['customselectadmin = CustomSelectAdmin']},
      package_data={'CustomSelectAdmin' : ['templates/*.html']})
