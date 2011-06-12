# -*- coding: utf-8 -*-

import fnmatch
import os
import unittest

from tracwikiextras.icons import FUGUE_ICONS
from tracwikiextras.util import group_over, reduce_names


class GroupOverTestCase(unittest.TestCase):

    def test_00(self):
        t = [] # test vector
        e = [] # expected result vector
        r = [] # result vector
        for i in group_over(t, 0):
            r.append(i)
        self.assertEqual(r, e)

    def test_01(self):
        t = [1]
        e = [(1,)]
        r = []
        for i in group_over(t, 0):
            r.append(i)
        self.assertEqual(r, e)

    def test_02(self):
        t = [1]
        e = [(1,)]
        r = []
        for i in group_over(t, 1):
            r.append(i)
        self.assertEqual(r, e)

    def test_03(self):
        t = [1]
        e = [(1, None)]
        r = []
        for i in group_over(t, 2):
            r.append(i)
        self.assertEqual(r, e)

    def test_10(self):
        t = [1, 2, 3, 4]
        e = [(1, 3),
             (2, 4)]
        r = []
        for i in group_over(t, 2):
            r.append(i)
        self.assertEqual(r, e)

    def test_20(self):
        t = [1, 2, 3, 4, 5]
        e = [(1, 4),
             (2, 5),
             (3, None)]
        r = []
        for i in group_over(t, 2):
            r.append(i)
        self.assertEqual(r, e)

    def test_30(self):
        t = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        e = [(1, 3),
             (2, None),
             (4,),
             (5, 8),
             (6, 9),
             (7, None),]
        b = [4] # break
        r = []
        for i in group_over(t, 2, lambda x: x not in b):
            r.append(i)
        self.assertEqual(r, e)

    def test_40(self):
        t = range(1, 16)
        e = [(1, 4, 7),
             (2, 5, None),
             (3, 6, None),
             (8,),
             (9,  None, None),
             (10,),
             (11, 12, 13),
             (14,),
             (15, None, None),]
        b = [8, 10, 14] # break
        r = []
        for i in group_over(t, 3, lambda x: x not in b):
            r.append(i)
        self.assertEqual(r, e)

class ReduceNamesTestCase(unittest.TestCase):

    def test_00(self):
        names = []
        expect = names
        result = reduce_names(names, 0)
        self.assertEqual(result, expect)

    def test_01(self):
        names = []
        expect = names
        result = reduce_names(names, 1)
        self.assertEqual(result, expect)

    def test_02(self):
        names = ['']
        expect = []
        result = reduce_names(names, 0)
        self.assertEqual(result, expect)

    def test_03(self):
        names = ['']
        expect = names
        result = reduce_names(names, 1)
        self.assertEqual(result, expect)

    def test_10(self):
        names = ['a']
        result = reduce_names(names, len(names))
        expect = names
        self.assertEqual(result, expect)

    def test_11(self):
        names = ['a']
        result = reduce_names(names, 0)
        expect = []
        self.assertEqual(result, expect)

    def test_20(self):
        names = ['a', 'aa']
        result = reduce_names(names, len(names))
        result.sort()
        expect = names
        self.assertEqual(result, expect)

    def test_21(self):
        names = ['a', 'aa']
        result = reduce_names(names, 1)
        result.sort()
        expect = ['a']
        self.assertEqual(result, expect)

    def test_30(self):
        names = ['a', 'aa', 'ab']
        result = reduce_names(names, len(names))
        result.sort()
        expect = names
        self.assertEqual(result, expect)

    def test_31(self):
        names = ['a', 'aa', 'ab']
        result = reduce_names(names, 1)
        result.sort()
        expect = ['a']
        self.assertEqual(result, expect)

    def test_32(self):
        names = ['a', 'aa', 'ab']
        result = reduce_names(names, 2)
        result.sort()
        expect = ['a', 'aa']
        self.assertEqual(result, expect)

    def test_40(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, len(names))
        result.sort()
        expect = names
        self.assertEqual(result, expect)

    def test_41(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 6)
        result.sort()
        expect = ['a', 'aa', 'ab', 'b', 'bb', 'bc']
        self.assertEqual(result, expect)

    def test_42(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 5)
        result.sort()
        expect = ['a', 'aa', 'ab', 'b', 'bb']
        self.assertEqual(result, expect)

    def test_43(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 4)
        result.sort()
        expect = ['a', 'aa', 'b', 'bb']
        self.assertEqual(result, expect)

    def test_44(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 3)
        result.sort()
        expect = ['a', 'aa', 'b']
        self.assertEqual(result, expect)

    def test_45(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 2)
        result.sort()
        expect = ['a', 'b']
        self.assertEqual(result, expect)

    def test_46(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 1)
        result.sort()
        expect = ['a']
        self.assertEqual(result, expect)

    def test_47(self):
        names = ['a', 'aa', 'ab', 'b', 'bb', 'bc', 'bca']
        result = reduce_names(names, 0)
        result.sort()
        expect = []
        self.assertEqual(result, expect)

    def test_50(self):
        icon_dir = FUGUE_ICONS[False]['S']
        files = fnmatch.filter(os.listdir(icon_dir), '*.png')
        names = [os.path.splitext(p)[0] for p in files]
        names.sort()
        expect = names
        result = reduce_names(names, len(names))
        result.sort()
        self.assertEqual(result, expect)

    def test_51(self):
        icon_dir = FUGUE_ICONS[False]['S']
        files = fnmatch.filter(os.listdir(icon_dir), '*.png')
        names = [os.path.splitext(p)[0] for p in files]
        names.sort()
        keep = 40
        kept = 0
        result = reduce_names(names, keep)
        for name in names:
            if name not in result:
                # print '%s%s' % (' '*8, name)
                pass
            else:
                # print name
                kept += 1
        # print '\nKept %d names' % kept
        self.assertEqual(kept, keep)

    def test_90(self):
        # Same as docstring
        names = ['a', 'aa', 'aaa', 'b', 'bb']
        result = reduce_names(names, 5)
        result.sort()
        expect = ['a', 'aa', 'aaa', 'b', 'bb']
        self.assertEqual(result, expect)

    def test_91(self):
        # Same as docstring
        names = ['a', 'aa', 'aaa', 'b', 'bb']
        result = reduce_names(names, 4)
        result.sort()
        expect = ['a', 'aa', 'b', 'bb']
        self.assertEqual(result, expect)

    def test_92(self):
        # Same as docstring
        names = ['a', 'aa', 'aaa', 'b', 'bb']
        result = reduce_names(names, 3)
        result.sort()
        expect = ['a', 'aa', 'b']
        self.assertEqual(result, expect)

    def test_93(self):
        # Same as docstring
        names = ['a', 'aa', 'aaa', 'b', 'bb']
        result = reduce_names(names, 2)
        result.sort()
        expect = ['a', 'b']
        self.assertEqual(result, expect)

    def test_94(self):
        # Same as docstring
        names = ['a', 'aa', 'aaa', 'b', 'bb']
        result = reduce_names(names, 1)
        result.sort()
        expect = ['a']
        self.assertEqual(result, expect)

    def test_95(self):
        # Same as docstring
        names = ['a', 'aa', 'aaa', 'b', 'bb']
        result = reduce_names(names, 0)
        result.sort()
        expect = []
        self.assertEqual(result, expect)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GroupOverTestCase, 'test'))
    suite.addTest(unittest.makeSuite(ReduceNamesTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
