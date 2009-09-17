from setuptools import find_packages, setup

version='0.4.1'

setup(name='CaptchaAuth',
      version=version,
      description="protect registration with a skimpyGimpy CAPTCHA",
      author='Nicholas Bergson-Shilcock',
      author_email='nicholasbs@openplans.org',
      url='http://openplans.org',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'skimpygimpy',
        'TracSQLHelper'
        ],
      dependency_links=[
        "http://trac-hacks.org/svn/tracsqlhelperscript/anyrelease#egg=TracSQLHelper",
        ],
      entry_points = """
      [trac.plugins]
      registration_captcha = captchaauth.register
      auth_captcha = captchaauth.auth
      """,
      )

