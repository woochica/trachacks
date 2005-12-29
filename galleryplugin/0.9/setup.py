from setuptools import setup

PACKAGE = 'GalleryPlugin'
VERSION = '0.1'

setup(
    name='GalleryPlugin',
    version='0.1',
    author='Bruce Christensen',
    author_email='trac@brucec.net',
    url='http://trac-hacks.swapoff.org/wiki/GalleryPlugin',
    description='Image gallery plugin for Trac',
    license='This software is distributed under the same terms as Trac itself',
    zip_safe=True,
    packages=['gallery', 'gallery.source'],
    package_data={'gallery': ['templates/*.cs']},
    )
