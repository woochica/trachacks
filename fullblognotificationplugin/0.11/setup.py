from setuptools import find_packages, setup

setup(name='TracFullBlogNotificationPlugin',
      version = '0.1',
      description = "Notification of blog changes",
      author = 'Nick Loeve',
      author_email = 'nick@hyves.nl',
      url = 'http://trac-hacks.org/wiki/FullBlogNotificationPlugin',
      keywords = 'trac plugin',
      license = "GPL",
      packages = find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data = True,
      package_data = { 'fullblognotification': ['templates/*', 'htdocs/*'] },
      zip_safe = False,
      entry_points = {'trac.plugins': [
          'fullblognotification = fullblognotification']},
      extras_require = {
        'fullblogplugin': "TracFullBlogPlugin>=0.1"
      }
)

