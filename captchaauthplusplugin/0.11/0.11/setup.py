from setuptools import find_packages, setup

version='0.7'

setup(name='CaptchaAuthPlus',
      version=version,
      description="protect registration and login with a skimpyGimpy CAPTCHA",
      author='Guillermo Steren. Based on CaptchaAuth by Nicholas Bergson-Shilcock',
      author_email='gstkein@hotmail.com',
      url='http://trac-hacks.org/',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'captchaauthplus': ['templates/*', ] },
      zip_safe=False,
      install_requires=[
        'skimpygimpy',
        'TracAccountManager',
        'ComponentDependencyPlugin',
        ],
      dependency_links=[
        "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
        ],
      entry_points = """
      [trac.plugins]
      registration_captcha = captchaauthplus.register
      login_captcha = captchaauthplus.login
      auth_captcha = captchaauthplus.auth
      image_captcha = captchaauthplus.web_ui
      """,
      )

