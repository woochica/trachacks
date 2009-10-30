from setuptools import find_packages, setup

version='0.0'

setup(name='TracView',
      version=version,
      description="a view with Trac",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={'': 
                    [ 'template/+package+/*/*', 'template/+package+/*.py_tmpl', 'template/*.py_tmpl' ]},
      install_requires = [ 'PasteScript' ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      tracview = tracview:TracView
      """,
      )

