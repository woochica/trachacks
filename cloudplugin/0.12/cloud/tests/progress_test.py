import unittest
import os
import sys
import json
import tempfile

dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
if dir not in sys.path:
    sys.path.append(dir)
from progress import Progress

class ProgressTest(unittest.TestCase):
    
    def setUp(self):
        self.file = tempfile.NamedTemporaryFile(delete=False)
    
    def tearDown(self):
        os.remove(self.file.name)
    
    def test_init__defaults(self):
        expected = {"status":{},"steps":[],"id":"","pidfile":"","error":""}
        Progress(self.file.name)
        f = open(self.file.name)
        data = json.loads(f.read())
        f.close()
        for k,v in expected.items():
            self.assertEquals(data.get(k),v)
        
    def test_init__nondefaults(self):
        expected = {"status":{'0':[1298924180,1298924380]},
                    "steps":['1','2','3'],
                    "id":"ip-10-122-7-227.ec2.internal",
                    "pidfile":"/pidfile",
                    "error":""}
        Progress(self.file.name, pidfile=expected['pidfile'],
                                 steps=expected['steps'],
                                 status=expected['status'],
                                 id=expected['id'])
        f = open(self.file.name)
        data = json.loads(f.read())
        f.close()
        for k,v in expected.items():
            self.assertEquals(data.get(k),v)
        
    
if __name__ == '__main__':
    unittest.main(argv=[__file__])
