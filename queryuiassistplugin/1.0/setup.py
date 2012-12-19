from setuptools import setup, find_packages

version = '0.1'

setup(
    name='QueryUiAssistPlugin',
    version=version,
    classifiers=[
                  "Programming Language :: Python",
                  "Programming Language :: Python :: 2.6",
                  "Framework :: Trac",
                  "Operating System :: OS Independent",
                  "Development Status :: 3 - Alpha",
                  "Intended Audience :: Developers",
                  "Intended Audience :: Information Technology",
                  "License :: OSI Approved :: BSD License",
                  "Natural Language :: Japanese",
                  "Topic :: Software Development :: Bug Tracking",
                  ],
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='On Query page, flip checkbox status on double click it\'s label',
    install_requires=['Trac >= 0.12'],
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'uiassist': ['htdocs/*/*'],
    },
    entry_points={
        'trac.plugins': [
            'queryuiassist = uiassist.query',
        ],
    },
)
