from setuptools import find_packages, setup

version='0.1'

setup(name='SimpleCaptcha',
      version=version,
      description="A simple captcha for Trac's AccountManager plugin that uses Skimpy Gimpy",
      author='Nicholas Bergson-Shilcock',
      author_email='nicholasbs@openplans.org',
      url='http://topp.openplans.org',
      keywords='trac plugin',
      license="GPLv3",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      simplecaptcha = simplecaptcha
      """,
      )

