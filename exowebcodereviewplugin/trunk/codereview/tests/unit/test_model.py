#!/usr/bin/python
# -*- coding: utf-8 -*-

# system imports
import unittest

# trac imports
from trac import db
from trac import test

# local imports
from codereview import init
from codereview import model

# Test data, borrowed from trac.db_default
# (table, (column1, column2), ((row1col1, row1col2), (row2col1, row2col2)))

def get_data(db):
    return (('codereview',
              ('id','author','status', 'text', 'version', 'time', 'priority'),
                ((1, 'tony', 1, 'hello',  1, 1162364264, 'normal'),
                 (1, 'tony', 1, 'hello2', 2, 1163364264, 'normal'),
                 (2, 'tc',   1, 'test1',  1, 1161234235, 'critical'),
                 (2, 'tony', 0, 'test2',  2, 1162523423, 'critical'),
                 (2, 'cindy',0, 'test3',  3, 1164000023, 'critical'),
                 (3, 'tc',   1, 'mytest', 1, 1163094124, 'normal'),
                 (3, 'clark',  -1, 'no',     2, 1163243123, 'normal'))),
            ('rev_path',
              ('rev', 'path'),
                (('1','/trunk'),
                 ('2','/branches'))),
            ('revision',
              ('rev', 'time', 'author', 'message'),
                (('1', 1160234353, 'robert', '#234'),
                 ('2', 1161098309, 'cindy',  'It is ok'),
                 ('3', 1161149802, 'ada',    'No'),
                 ('4', 1161214323, 'ada',    'No, too'))),
            ('node_change',
              ('rev', 'path'),
                (('1', '/trunk'),
                 ('2', '/branches'),
                 ('3', '/code/tracplugins/trunk'),
                 ('3', '/code/tracplugins/branches'),
                 ('4', '/ringier/branches/cityweekend'),
                 ('4', '/ringier/branches/pro'),
                 ('4', '/ringier/trunk/'))))

class CodeReviewPoolTestCase(unittest.TestCase):

    def setUp(self):
        self.env = test.EnvironmentStub()
        self.db = self.env.get_db_cnx()
        init.CodeReviewInit(self.env).upgrade_environment(self.db)
        cursor = self.db.cursor()
        for table, cols, vals in get_data(db):
            cursor.executemany("INSERT INTO %s (%s) VALUES (%s)" % (table,
                               ','.join(cols), ','.join(['%s' for c in cols])),
                               vals)

        self.db.commit()

    def test_get_rev_count(self):
        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp.get_rev_count(), 4)

    def test_get_codereviews_by_time(self):
        crp = model.CodeReviewPool(self.env)
        correct_result = [
                  (1163094124, 'tc',   'mytest', 3, 1, 1, 'No'),
                  (1163243123, 'clark','no',     3,-1, 2, 'No'),
                  (1163364264, 'tony', 'hello2', 1, 1, 2, '#234')
                         ]
        self.failUnlessEqual([i for i in crp.get_codereviews_by_time(1163000000, 1164000000)],
                             correct_result)

    def test_get_codereviews_by_status(self):
        crp = model.CodeReviewPool(self.env)
        correct_result1 = [3, 2]
        correct_result2 = {2:'critical', 3:'normal'}
        correct_result = (correct_result1, correct_result2)
        self.failUnlessEqual(crp.get_revisions_by_status("Completed"), correct_result)

        crp = model.CodeReviewPool(self.env)
        correct_result1 = [1]
        correct_result2 = {1:'normal'}
        correct_result = (correct_result1, correct_result2)
        self.failUnlessEqual(crp.get_revisions_by_status("Undergoing"), correct_result)

        crp = model.CodeReviewPool(self.env)
        correct_result = ([4])
        self.failUnlessEqual(crp.get_revisions_by_status("Awaiting"), correct_result)

    def test_get_codereviews_by_revisions(self):
        crp = model.CodeReviewPool(self.env)
        revisions = [3, 2]
        correct_result = ([
                     {'rev': '3', 'prefix': '', 'author': 'ada', 'msg': 'No', 'ctime': 1161149802},
                     {'rev': '2', 'prefix': '/branches', 'author': 'cindy', 'msg': 'It is ok', 'ctime': 1161098309}
                         ])
        self.failUnlessEqual([item for item in crp.get_codereviews_by_revisions(revisions)], correct_result)

    def test_get_codereviews_by_key(self):
        crp = model.CodeReviewPool(self.env)
        correct_result = ([
                     {'rev': '3', 'prefix': '', 'author': 'ada', 'msg': 'No', 'ctime': 1161149802, 'priority': 'normal', 'reviewers': ['tc', 'clark']},
                     {'rev': '2', 'prefix': '/branches', 'author': 'cindy', 'msg': 'It is ok', 'ctime': 1161098309, 'priority': 'critical', 'reviewers': ['tc', 'tony', 'cindy']}
                         ])
        self.failUnlessEqual([item for item in crp.get_codereviews_by_key("Completed")], correct_result)

        correct_result = ([
                     {'rev': '1', 'prefix': '/trunk', 'author': 'robert', 'msg': '#234', 'ctime': 1160234353, 'priority': 'normal', 'reviewers': ['tony']}
                         ])
        self.failUnlessEqual([item for item in crp.get_codereviews_by_key("Undergoing")], correct_result)

        correct_result = ([
                     {'rev': '4', 'prefix': '/ringier/', 'author': 'ada', 'msg': 'No, too', 'ctime': 1161214323}
                         ])
        self.failUnlessEqual([item for item in crp.get_codereviews_by_key("Awaiting")], correct_result)

    def test_is_match(self):
        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match({'author':['abc','def']},
                                      'abcd',
                                      'msg',
                                      1161000000))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_match({'author':['abc','def']},
                                            'ab',
                                            'msg',
                                           1161000000),
                             False)

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match({'start_date':1160000000,
                                       'end_date':1162000000},
                                       'abcd',
                                       'msg',
                                      1161000000))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_match({'start_date':1162000000,
                                            'end_date':1163000000},
                                            'abcd',
                                            'msg',
                                           1161000000),
                             False)

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match({'start_date':1162000000},
                                            'abcd',
                                            'msg',
                                           1161000000))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_match({'comment':'#123'},
                                            'abcd',
                                            '#12',
                                           1161000000),
                             False)

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match({'comment':'#123'},
                                            'abcd',
                                            '#1234, #342',
                                           1161000000))

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match({'author':['abc',],
                                       'start_date':1161000000,
                                       'end_date':1163000000,
                                       'comment':'#123'},
                                      'abcd',
                                      '#1234',
                                      1162000000))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_match({'author':['abc',],
                                       'start_date':1161000000,
                                       'end_date':1163000000,
                                       'comment':'#12345'},
                                      'abcd',
                                      '#1234',
                                      1162000000),
                             False)

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match(None,
                                      'abcd',
                                      '#1234',
                                      1162000000))

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_match({'abc':'abcd'},
                                      'abcd',
                                      '#1234',
                                      1162000000))

    def test_is_show(self):
        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_show(None, '/test', '#234'))

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_show({'prefix':['/test1', '/abc']},
                                     '/test', '#234'))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_show({'prefix':['/tes', '/abc']},
                                     '/test', '#234'),
                             False)
        
        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_show({'msg':['#2345', '#34']},
                                     '/test', '#234'))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_show({'msg':['#23', '#34']},
                                          '/test', '#234'),
                             False)

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_show({'prefix':['/test1', '/abc'],
                                      'msg':['#2345',]},
                                     '/test', '#234'))

        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp._is_show({'prefix':['/tes', '/abc'],
                                           'msg':['#23',]},
                                          '/test', '#234'),
                             False)

        crp = model.CodeReviewPool(self.env)
        self.failUnless(crp._is_show({'abc':'def'},
                                     '/test', '#234'))

    def test_get_reviewers(self):
        crp = model.CodeReviewPool(self.env)
        self.failUnlessEqual(crp.get_reviewers(2), ['tc', 'tony', 'cindy'])
        self.failUnlessEqual(crp.get_reviewers(5), [])

    def test_changeset_info(self):
        crp = model.CodeReviewPool(self.env)
        correct_result = [
                (u'4', u'ada', u'No, too', u'/ringier/', 1161214323),
                (u'2', u'cindy', u'It is ok', u'/branches', 1161098309),
                (u'1', u'robert', u'#234', u'/trunk', 1160234353)
                         ]
        self.failUnlessEqual([i for i in crp.changeset_info([1, 2, 4])],
                             correct_result)

class CodeReviewTestCase(unittest.TestCase):

    def setUp(self):
        self.env = test.EnvironmentStub()
        self.db = self.env.get_db_cnx()
        init.CodeReviewInit(self.env).upgrade_environment(self.db)
        cursor = self.db.cursor()
        for table, cols, vals in get_data(db):
            cursor.executemany("INSERT INTO %s (%s) VALUES (%s)" % (table,
                               ','.join(cols), ','.join(['%s' for c in cols])),
                               vals)

        self.db.commit()

    def test_is_existent(self):
        cr = model.CodeReview(self.env, 1)
        self.failUnless(cr.is_existent())
        cr = model.CodeReview(self.env, 4)
        self.failUnlessEqual(cr.is_existent(), False)

    def test_get_current_ver(self):
        cr = model.CodeReview(self.env, 1)
        self.failUnlessEqual(cr.get_current_ver(), 2)
        cr = model.CodeReview(self.env, 2)
        self.failUnlessEqual(cr.get_current_ver(), 3)

    def test_is_existent_ver(self):
        cr = model.CodeReview(self.env, 1)
        self.failUnless(cr.is_existent_ver(2))
        cr = model.CodeReview(self.env, 2)
        self.failUnlessEqual(cr.is_existent_ver(5), False)


    def test_get_item(self):
        cr = model.CodeReview(self.env, 2)
        correct_result = {
                    'status'    : 0,
                    'time'      : 1164000023,
                    'text'      : u'test3',
                    'priority'  : u'critical',
                    'author'    : u'cindy',
                    'id'        : 2,
                    'version'   : 3,
                    'reviewers' : [u'tc', u'tony', u'cindy']
                         }
        self.failUnlessEqual(cr.get_item(), correct_result)

        cr = model.CodeReview(self.env, 4)
        correct_result = {
                    'status'    : 2,
                    'time'      : None,
                    'text'      : None,
                    'priority'  : None,
                    'author'    : None,
                    'id'        : 4,
                    'version'   : 0,
                    'reviewers' : []
                         }
        self.failUnlessEqual(cr.get_item(), correct_result)

    def test_get_reviewers(self):
        cr = model.CodeReview(self.env, 3)
        self.failUnlessEqual(cr.get_reviewers(), [u'tc', u'clark'])
        cr = model.CodeReview(self.env, 5)
        self.failUnlessEqual(cr.get_reviewers(), [])

    def test_save(self):
        cr = model.CodeReview(self.env, 3)
        cr.save()
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT version FROM codereview WHERE id=3 AND version=3")
        result = cursor.fetchone()
        self.failUnlessEqual(result, (3,))

        cr = model.CodeReview(self.env, 1)
        item = {'text' : 'test for test', 'author' : 'clark'}
        cr.save(item)
        cursor.execute("SELECT text, author FROM codereview WHERE id=1 AND version=3")
        result = cursor.fetchone()
        self.failUnlessEqual(result, ('test for test', 'clark'))

        cr = model.CodeReview(self.env, 5)
        cr.save()
        cursor.execute("SELECT version FROM codereview WHERE id=5")
        result = cursor.fetchone()
        self.failUnlessEqual(result, (1, ))

    def test_delete(self):
        cr = model.CodeReview(self.env, 2)
        cr.delete()
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT count(version) FROM codereview WHERE id=2")
        result = cursor.fetchone()
        self.failUnlessEqual(result, (2, ))

    def test_set_to_critical(self):
        cr = model.CodeReview(self.env, 1)
        cr.set_to_critical()
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT priority FROM codereview WHERE id=1 AND version=3")
        result = cursor.fetchone()
        self.failUnlessEqual(result, ('critical', ))

    def test_set_no_need_to_review(self):
        cr = model.CodeReview(self.env, 2)
        cr.set_no_need_to_review()
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT status FROM codereview WHERE id=2 AND version=4")
        result = cursor.fetchone()
        self.failUnlessEqual(result, (-1, ))

    def test_get_all_items(self):
        cr = model.CodeReview(self.env, 2)
        result = [record for record in cr.get_all_items()]
        correct_result = [
                 {'id':2, 'author':'tc', 'status':1, 'time':1161234235, 'text':'test1', 'version':1, 'priority':'critical'},
                 {'id':2, 'author':'tony', 'status':0, 'time':1162523423, 'text':'test2', 'version':2, 'priority':'critical'},
                 {'id':2, 'author':'cindy', 'status':0, 'time':1164000023, 'text':'test3', 'version':3, 'priority':'critical'}
                 ]
        self.failUnlessEqual(result, correct_result)

    def test_get_commit_path(self):
        cr = model.CodeReview(self.env, 1)
        self.failUnlessEqual(cr.get_commit_path(), '/trunk') 

        cr = model.CodeReview(self.env, 3)
        self.failUnlessEqual(cr.get_commit_path(), '')

        cr = model.CodeReview(self.env, 4)
        self.failUnlessEqual(cr.get_commit_path(), '/ringier/')

    def test_get_all_pathes(self):
        cr = model.CodeReview(self.env, 4)
        correct_result = ['/ringier/branches/cityweekend',
                   '/ringier/branches/pro', '/ringier/trunk/']
        self.failUnlessEqual(cr.get_all_pathes(), correct_result)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewTestCase, 'test'))
    suite.addTest(unittest.makeSuite(CodeReviewPoolTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


