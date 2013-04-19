from setuptools import find_packages, setup

version='0.6'

setup(name='CaptchaAuth',
      version=version,
      description="protect registration with a skimpyGimpy CAPTCHA",
      author='Nicholas Bergson-Shilcock',
      author_email='nicholasbs@openplans.org',
      url='http://openplans.org',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'captchaauth': ['templates/*', ] },
      zip_safe=False,
      install_requires=[
        'skimpygimpy',
        'TracAccountManager',
        'TracSQLHelper',
        'ComponentDependencyPlugin',
        ],
      dependency_links=[
        "http://trac-hacks.org/svn/tracsqlhelperscript/0.11#egg=TracSQLHelper",
        "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
        ],
      entry_points = """
      [trac.plugins]
      registration_captcha = captchaauth.register
      auth_captcha = captchaauth.auth
      image_captcha = captchaauth.web_ui
      """,
      )

