from setuptools import setup

setup(name='TracCanviz',
      version='0.1',
      license = "BSD",
      author = "Shane Caraveo",
      packages=['canviz'],
      entry_points={'trac.plugins':
        ['canviz = canviz']
        },
      package_data={'canviz': ['htdocs/*.js', 'htdocs/*.css']},
)

