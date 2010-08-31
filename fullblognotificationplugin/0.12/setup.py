from setuptools import find_packages, setup

setup(name='TracFullBlogNotificationPlugin',
      version = '0.2.1',
      description = "Notification of changes from FullBlogPlugin",
      author = 'Nick Loeve',
      author_email = 'nick@hyves.nl',
      maintainer = 'Ryan J Ollos',
      maintainer_email = 'ryano@physiosonics.com',
      url = 'http://trac-hacks.org/wiki/FullBlogNotificationPlugin',
      keywords = 'trac plugin',
      license = "GPL",
      packages = find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data = True,
      package_data = { 'fullblognotification': ['templates/*', 'htdocs/*'] },
      zip_safe = False,
      install_requires = ['Trac >= 0.12', 'Genshi >= 0.6'],
      entry_points = {'trac.plugins': [
          'fullblognotification = fullblognotification']},
      extras_require = {
        'fullblogplugin': "TracFullBlogPlugin>=0.1"
      }
)

