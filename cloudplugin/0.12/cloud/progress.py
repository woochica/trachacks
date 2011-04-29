import os
import stat
import time
import json
import tempfile
import signal
import subprocess

class Progress(object):
    """Manages status information in a (JSON) file.  An example JSON file
    format:
    
      {'title': 'Progress',
       'description': 'Progress on task blah',
       'started_by': 'rob',
       'steps': ['step1','step2','step3'],
       'status': {'0':(1298924180,1298924380),'1':(1298924381,None)},
       'id': 'ip-12-132-9-186.ec2.internal',
       'error': '',
       'errored_at': nil,
       'command': 'python blah blah',
       'pidfile': '/tmp/pidfile'}
    
    The 'progress' attribute is a list if start and end times of the
    completed steps and the current step (which only has a start time).
    The 'id' is the id used for viewing the item.  The 'pidfile' is of
    the remote process."""
    
    @staticmethod
    def get_file(prefix='progress-'):
        dir = tempfile.gettempdir()
        
        # delete old progress files
        for file in os.listdir(dir):
            if file.startswith(prefix):
                path = os.path.join(dir,file)
                mtime = os.stat(path).st_mtime
                if (time.time() - mtime) > 60 * 60 * 24: # 24+ hours old
                    os.remove(path)
        
        # prepare the command
        f = tempfile.NamedTemporaryFile(dir=dir, prefix=prefix, delete=False)
        return f.name
    
    def __init__(self, file, pidfile=None, steps=None, title=None,
                 description=None, status=None, id=None, started_by=None,
                 command=None):
        self.file = file
        progress = {'pidfile': pidfile or '',
                    'title': title or '',
                    'description': description or '',
                    'started_by': started_by or [],
                    'steps': steps or [],
                    'status': status or {},
                    'id': id or '',
                    'error': '',
                    'errored_at': None,
                    'command': command or '',
                    }
        if not os.path.exists(file) or os.path.getsize(file) == 0:
            self.set(progress)
    
    def pidfile(self, pidfile):
        progress = self.get()
        progress['pidfile'] = pidfile
        self.set(progress)
    
    def title(self, title):
        progress = self.get()
        progress['title'] = title
        self.set(progress)
        
    def description(self, description):
        progress = self.get()
        progress['description'] = description
        self.set(progress)
        
    def started_by(self, started_by):
        progress = self.get()
        progress['started_by'] = started_by
        self.set(progress)
        
    def steps(self, steps):
        progress = self.get()
        progress['steps'] = steps
        self.set(progress)
        
    def id(self, id):
        progress = self.get()
        progress['id'] = id
        self.set(progress)
        
    def error(self, msg):
        progress = self.get()
        progress['error'] = msg
        progress['errored_at'] = time.time()
        self.set(progress)
        
    def command(self, command):
        progress = self.get()
        progress['command'] = command
        self.set(progress)
        
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
    
    def is_done(self, step):
        """0-indexed steps."""
        step = str(step)
        progress = self.get()
        if step not in progress['status']:
            return False
        return progress['status'][step][1] and True or False
    
    def stop(self, sig=signal.SIGTERM):
        """Stop/kill the daemon."""
        progress = self.get()
        f = open(progress['pidfile'],'r')
        pid = int(f.read().strip())
        f.close()
        os.kill(pid, sig)
    
    def restart(self):
        """Restarts daemon which is expected to continue where it left off."""
        progress = self.get()
        cmd = progress['command']
        if subprocess.call(cmd):
            raise Exception("Error restarting command: %s" % cmd)
    
    def set(self, progress):
        f = open(self.file, 'w')
        f.write(json.dumps(progress))
        f.flush()
        f.close()
        os.chmod(self.file, stat.S_IRUSR | stat.S_IWUSR |
                            stat.S_IRGRP | stat.S_IWGRP |
                            stat.S_IROTH | stat.S_IWOTH )
        
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
