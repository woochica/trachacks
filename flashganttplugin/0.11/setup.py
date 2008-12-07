# Copyright 2008 Andrew De Ponte, Patrick Murphy
#
# This file is part of FlashGanttPlugin
#
# FlashGanttPlugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# FlashGanttPlugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FlashGanttPlugin. If not, see <http://www.gnu.org/licenses/>.

from setuptools import find_packages, setup

setup(
    name='TracFlashGantt', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        flashgantt = flashgantt.flashgantt
    """,
    package_data={'flashgantt': ['templates/*.html',
                                 'templates/*.xml',
                                 'htdocs/css/*.css',
                                 'htdocs/images/*',
                                 'htdocs/flash/*.swf',
                                 'htdocs/js/*.js',
                                 'htdocs/data/*']},
)
