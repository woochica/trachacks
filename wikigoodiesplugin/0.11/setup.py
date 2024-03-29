#!/usr/bin/env python

from setuptools import setup

setup(name='TracWikiGoodies',
      description='Plugin for Trac which extends the Wiki with some goodies',
      keywords='trac wiki plugin smileys entities symbols',
      url='http://trac-hacks.org/wiki/WikiGoodiesPlugin',
      version='0.11.0.3dev',
      license='BSD',
      author='Christian Boos',
      author_email='cboos@neuf.fr',
      long_description="""
      This Trac 0.11 plugin extends the Trac Wiki by providing support
      for smileys, HTML entities and other frequently used symbols.

      Single words surrounded by "*", "/" or "_" characters are tranformed
      to bold, italic and underline text, respectively.

      E-mail are transformed to "mailto:" links and UNC paths are transformed
      to "file:" links.

      It also comes with a set of 3 macros that can be used
      to provide a visual index of the markup:
       * [[ShowSmileys]]
       * [[ShowEntities]]
       * [[ShowSymbols]]

      See http://moinmoin.wikiwikiweb.de/HelpOnSmileys
      for an external reference on the smileys.

      See http://www.w3.org/TR/html401/sgml/entities.html
      for the official list of HTML 4.0 entities,
      and http://www.cookwood.com/html/extras/entities.html
      for an illustration.
      """,
      packages=['goodies'],
      package_data={'goodies': ['htdocs/modern/img/*.png']},
      entry_points={'trac.plugins': 'goodies = goodies'})
