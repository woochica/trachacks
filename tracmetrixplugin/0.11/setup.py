from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TracMetrixPlugin', version='0.11',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        tracmetrixplugin.mdashboard = tracmetrixplugin.mdashboard
        tracmetrixplugin.web_ui = tracmetrixplugin.web_ui
        tracmetrixplugin.api = tracmetrixplugin.api
        tracmetrixplugin.model = tracmetrixplugin.model
    """,
    package_data={'tracmetrixplugin': ['templates/*.html', 
                                       'htdocs/css/*.css', 
                                       'htdocs/images/*']},
)
