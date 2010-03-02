import os
import sys
import unittest


def suite():
    suite = unittest.TestSuite()
    utestdir = os.path.dirname(__file__)
    sys.path.insert(0, utestdir)
    for f in os.listdir(utestdir):
        if os.path.isfile(os.path.join(utestdir, f)) \
           and f.startswith('test_') \
           and f.endswith('.py'):
            mod = __import__(f[:-3], globals(), locals(), [''])
            if 'suite' in dir(mod):
                suite.addTest(mod.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
