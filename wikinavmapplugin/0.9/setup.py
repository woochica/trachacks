from setuptools import find_packages, setup

setup(
    name='TracWikiNavMap', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        navmap = wikinavmap.web_ui
	mappopup = wikinavmap.popup
	mapdata = wikinavmap.mapdata
    """, package_data={'wikinavmap' : ['templates/*.cs', 'htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.png', 'htdocs/images/*.gif']},
	author = "Adam Ullman",
	author_email = "adam@it.usyd.edu.au",
	description = "Displays a graphical map of the Trac Wiki, Tickets and Milestones",
	
	install_requires = [ 'GraphvizPlugin' ]
)
