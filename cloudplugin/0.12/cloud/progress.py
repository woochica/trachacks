import os
import stat
import time
import json

class Progress(object):
    """Manages status information in a (JSON) file.  An example JSON file
    format:
    
      {'steps': ['step1','step2','step3'],
       'status': {'0':(1298924180,1298924380),'1':(1298924381,None)},
       'id': 'ip-12-132-9-186.ec2.internal',
       'error': '',
       'pidfile': '/tmp/pidfile'}
    
    The 'progress' attribute is a list if start and end times of the
    completed steps and the current step (which only has a start time).
    The 'id' is the id used for viewing the item.  The 'pidfile' is of
    the remote process."""
    
    def __init__(self, file, pidfile=None, steps=None, status=None, id=None):
        self.file = file
        progress = {'pidfile': pidfile or '',
                    'steps': steps or [],
                    'status': status or {},
                    'id': id or '',
                    'error': '',
                    }
        if not os.path.exists(file) or os.path.getsize(file) == 0:
            self.set(progress)
    
    def set(self, progress):
        f = open(self.file, 'w')
        f.write(json.dumps(progress))
        f.flush()
        f.close()
        os.chmod(self.file, stat.S_IRUSR | stat.S_IWUSR |
                            stat.S_IRGRP | stat.S_IWGRP |
                            stat.S_IROTH | stat.S_IWOTH )
        
    def start(self, step, start_time=None):
        """0-indexed steps."""
        step = str(step)
        progress = self.get()
        progress['status'][step] = (start_time or time.time(),None)
        self.set(progress)
        
    def done(self, step, end_time=None):
        """0-indexed steps."""
        step = str(step)
        progress = self.get()
        start_time = progress['status'][step][0]
        progress['status'][step] = (start_time,end_time or time.time())
        self.set(progress)
    
    def error(self, msg):
        progress = self.get()
        progress['error'] = msg
        self.set(progress)
        
    def get(self, attempt=1):
        try:
            f = open(self.file, 'r')
            progress = json.loads(f.read())
            f.close()
            return progress
        except:
            if attempt < 3:
                time.sleep(0.1)
                return self.get(attempt+1)
            raise
