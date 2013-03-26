from setuptools import setup

PACKAGE = 'BittenLintAnnotator'
VERSION = '0.1.1'

_package = 'bitten_lint_annotator'
_modules = [_package + '.lintannotator']

setup(name=PACKAGE, version=VERSION, packages=[_package],
        entry_points={'trac.plugins': ['%s=%s' % (m, m) for m in _modules]},
        package_data={_package: ['htdocs/*']},
        install_requires = 'Bitten',
        zip_safe = True,

        url = 'http://trac-hacks.org/wiki/BittenLintAnnotatePlugin',
        author = 'simohe',
        author_email = 'simohe@besonet.ch',
        license = 'BSD 2-Clause',
        description = 'Show an annotation for Lint reports from bitten.'
)
