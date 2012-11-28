from setuptools import find_packages, setup

setup(
    name = 'TracImageSvg',
    version = '0.1',
    packages = ['imagesvg'],
    package_data = { 'imagesvg': [ '*.txt',] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Image svg plugin for Trac.",
    license = "BSD",
    keywords = "trac svg",
    url = "http://trac-hacks.org/wiki/ImageSvg",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {'trac.plugins': ['imagesvg = imagesvg.web_ui']},
)
