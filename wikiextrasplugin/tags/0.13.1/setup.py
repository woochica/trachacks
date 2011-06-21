#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='TracWikiExtras',
    description='Plugin for Trac which extends the wiki with some extras',
    keywords='trac wiki plugin icons smileys entities symbols color phrases '
             'boxes',
    url='http://trac-hacks.org/wiki/WikiExtrasPlugin',
    version='0.13.1',
    license='BSD',
    author='Mikael Relbe and Christian Boos',
    author_email='mikael@relbe.se; cboos@neuf.fr',
    long_description="""
        This Trac 0.13 plugin extends the Trac Wiki by providing support for:
         * Icons and smileys.
         * HTML entities and other frequently used symbols.
         * Highlighting attentional phrases.
         * Coloring text.
         * Visually appealing and modern looking text and image boxes.
         * Transformation of UNC paths to "file://" links.

        The Fugue icon library is contained within this distribution for
        convenience (though installation time is taking a hit), which contains
        more than 3.000(!) icons in three sizes (small/medium/large).

        Use the wiki markup (|name|) or the Icon macro to show any icon in the
        library. When a glob pattern (* and ?) is part of the name, a preview
        of matching icons is displayed. This feature is very handy for finding
        and selecting an icon when a wiki page is being edited in side-by-side
        mode.

        Attentional phrases such as FIXME, TODO and DONE are highlighted to
        catch attention.
        
        Use the Color macro to decorate wiki text with colors.

        Use the box wiki processor -- and its variants rbox, newsbox and
        imagebox -- to insert appealing and eye-catching boxes on the web page.

        Following set of macros that can be used to provide a visual index of
        the markup:
         * [[ShowEntities]]
         * [[ShowIcons]]
         * [[ShowPhrases]]
         * [[ShowSmileys]]
         * [[ShowSymbols]]

        Use the About-macros for instructions and demonstrations to wiki
        authors on some of these features:
         * [[AboutWikiBoxes]]
         * [[AboutWikiIcons]]
         * [[AboutWikiPhrases]]

        The set of smileys, symbols and phrases, and the width of boxes are
        configurable.

        See http://p.yusukekamiyamane.com for an external reference on the
        Fugue icon library.

        See http://www.w3.org/TR/html401/sgml/entities.html
        for the official list of HTML 4.0 entities,
        and http://www.cookwood.com/html/extras/entities.html
        for an illustration.

        This plugin is based on the TracWikiGoodies plugin by Christian Boos,
        see http://trac-hacks.org/wiki/WikiGoodiesPlugin

        It is not advisable to enable corresponding packages in
        WikiGoodiesPlugin and *this* plugin at the same time.
    """,
    packages = find_packages(exclude=['*.tests']),
    package_data={
        'tracwikiextras': ['doc/*',
                           'htdocs/css/boxes-narrow-toc.css',
                           'htdocs/css/boxes-shadowless.css',
                           'htdocs/css/boxes.css',
                           'htdocs/css/phrases.css',
                           'htdocs/icons/fugue/*.txt',
                           'htdocs/icons/fugue/bonus/icons-24/*.png',
                           'htdocs/icons/fugue/bonus/icons-32/*.png',
                           'htdocs/icons/fugue/bonus/icons-shadowless-24/*.png',
                           'htdocs/icons/fugue/bonus/icons-shadowless-32/*.png',
                           'htdocs/icons/fugue/icons/*.png',
                           'htdocs/icons/fugue/icons-shadowless/*.png',
                          ]
    },
    zip_safe = False,
    test_suite = 'tracwikiextras.tests.suite',
    entry_points={'trac.plugins': 'tracwikiextras = tracwikiextras'},
)
