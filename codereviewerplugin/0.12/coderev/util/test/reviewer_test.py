import os
import sys
import shutil
import unittest

dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
if dir not in sys.path:
    sys.path.append(dir)
from reviewer import Reviewer

"""
[Wed May 16 12:39:28 root@vookdev:/home/vook/workspace/myrepo] # git log
commit 82555dc3c5960646e60df09fb33ab288f209a65b
Author: rob <rob@example.com>
Date:   Wed May 16 11:13:48 2012 -0400

    ref #3: changeset 4

commit 71cd80944c7c8cdeff9f394b493a372b2b70ebb1
Author: rob <rob@example.com>
Date:   Wed May 16 11:10:57 2012 -0400

    ref #2, #3: changeset 3

commit d57f050a265b303ef1748a26cecb71d9e9ab92b9
Author: rob <rob@example.com>
Date:   Wed May 16 11:04:25 2012 -0400

    ref #2: changeset 2

commit 8bebe6d50698dccb68586042e3e94de4aecba945
Author: rob <rob@example.com>
Date:   Wed May 16 10:11:44 2012 -0400

    ref #1: changeset 1

commit f79ab3734db0e5230dfc93fa7182591fd900bb87
Author: rob <rob@example.com>
Date:   Wed May 16 10:08:23 2012 -0400

    initial commit
"""

class TestReviewer(unittest.TestCase):
    
    def setUp(self):
        testdata_dir = os.path.join(os.path.dirname(__file__),'testdata')
        
        # clean workdir for each test
        workdir = os.path.join('/tmp','reviewer')
        if os.path.exists(workdir):
            shutil.rmtree(workdir)
        os.mkdir(workdir)
        src_file = os.path.join(testdata_dir,'changeset.dev')
        data_file = os.path.join(workdir,'changeset.dev')
        shutil.copy(src_file, data_file)
        
        # instatiate reviewer
        self.reviewer = Reviewer(
            trac_env=os.path.join(testdata_dir,'trac_env'),
            repo_dir=os.path.join(testdata_dir,'myrepo'),
            target_ref="master",
            data_file=data_file)
    
    def test_is_complete__changeset1(self):
        changeset1 = '8bebe6d50698dccb68586042e3e94de4aecba945'
        self.assertTrue(self.reviewer.is_complete(changeset1))

    def test_is_complete__changeset2(self):
        changeset2 = 'd57f050a265b303ef1748a26cecb71d9e9ab92b9'
        self.assertTrue(self.reviewer.is_complete(changeset2))

    def test_is_complete__changeset3(self):
        changeset3 = '71cd80944c7c8cdeff9f394b493a372b2b70ebb1'
        self.assertFalse(self.reviewer.is_complete(changeset3))
    
    def test_get_next_changeset__initial(self):
        # expect changeset 3 because ticket #2 is last fully reviewed ticket
        actual = self.reviewer.get_next_changeset() # changeset 3
        expected = 'd57f050a265b303ef1748a26cecb71d9e9ab92b9'
        self.assertEqual(actual,expected)
        self.assertEqual(self.reviewer.get_current_changeset(),expected)
    
    def test_get_next_changeset__initial_no_save(self):
        # expect changeset 3 because ticket #2 is last fully reviewed ticket
        actual = self.reviewer.get_next_changeset(save=False) # changeset 3
        expected = 'd57f050a265b303ef1748a26cecb71d9e9ab92b9'
        self.assertEqual(actual,expected)
        self.assertNotEqual(self.reviewer.get_current_changeset(),expected)
    
    def test_get_next_changeset__at_next(self):
        data = '{"current": "d57f050a265b303ef1748a26cecb71d9e9ab92b9"}'
        open(self.reviewer.data_file,'w').write(data)
        actual = self.reviewer.get_next_changeset() # changeset 3
        expected = 'd57f050a265b303ef1748a26cecb71d9e9ab92b9'
        self.assertEqual(actual,expected)
        self.assertEqual(self.reviewer.get_current_changeset(),expected)
    
    def test_get_next_changeset__at_last(self):
        data = '{"current": "82555dc3c5960646e60df09fb33ab288f209a65b"}'
        open(self.reviewer.data_file,'w').write(data)
        expected = self.reviewer.get_next_changeset() # changeset 4
        self.assertEqual(expected,'82555dc3c5960646e60df09fb33ab288f209a65b')
    
    def test_get_blocking_changeset__initial(self):
        # expect changeset 3 because ticket #2 is last fully reviewed ticket
        actual = self.reviewer.get_blocking_changeset() # changeset 3
        expected = '71cd80944c7c8cdeff9f394b493a372b2b70ebb1'
        self.assertEqual(actual,expected)
    
    def test_get_vreview__initial(self):
        # ensure this method doesn't go away
        expected = '71cd80944c7c8cdeff9f394b493a372b2b70ebb1'
        review = self.reviewer.get_review(expected)
        self.assertEqual(review.changeset,expected)
        

if __name__ == '__main__':
    unittest.main()
