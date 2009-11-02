import os
import repository_hook_system.listener as listener

from repository_hook_system.interface import IRepositoryHookSetup
from repository_hook_system.listener import command_line
from repository_hook_system.listener import option_parser
from trac.core import *
from utils import command_line_args
from utils import iswritable

class FileSystemHooks(Component):
    """
    Implementation of IRepositoryHookSetup for hooks that live on the 
    filesystem.  Currently, the filenames associated with the hooks must
    be the same as the hook names
    """
    
    implements(IRepositoryHookSetup)
    abstract = True
    mode = 0750 # mode to write hook files

    ### these methods must be implemented by the provider class

    def filename(self, hookname):
        raise NotImplementedError

    def args(self):
        raise NotImplementedError

    ### methods for manipulating the files

    def file_contents(self, hookname):
        """
        return the lines of the file for a given hook,
        or None if the file does not yet exist
        """ 
        filename = self.filename(hookname)
        if not os.path.exists(filename):
            return None

        f = file(filename)
        retval =  [ i.rstrip() for i in f.readlines() ]
        f.close()
        return retval

    def marker(self):
        """marker to place in the file to identify the hook"""
        return "# trac repository hook system"

    def projects_enabled(self, hookname):
        """
        returns enabled projects, or None if the stub is not found
        returns a tuple of (lines, index, list_of_projects) when found
        this won't work properly if the command line is used more than once 
        in the file
        """
        lines = self.file_contents(hookname)
        if lines is None:
            return None

        retval = None
        invoker = listener.filename()
        for index, line in enumerate(lines):
            if ' %s ' % invoker in line and not line.strip().startswith('#'):
                if retval is not None:
                    # TODO: raise an error indicate that multiple invocations
                    # detected in the hook file
                    pass 
                args = command_line_args(line)
                parser = option_parser()
                options, args = parser.parse_args(args)
                retval = index, lines, options.projects

        return retval

    def create(self, hookname):
        """create the stub for given hook and return the file object"""
        
        filename = self.filename(hookname)
        try:
            os.mknod(filename, self.mode)
        except: # won't work on windows
            pass
        f = file(filename, 'w')
        print >> f, "#!/bin/bash"
        return f

    ### methods for IRepositoryHookSetup

    def enable(self, hookname):
        # TODO:  remove multiple blank lines when writing

        if self.is_enabled(hookname):
            return # nothing to do

        if not self.can_enable(hookname):
            return # XXX err more gracefully

        def print_hook(f):
            print >> f, '%s%s' % (os.linesep, self.marker())
            print >> f, command_line(self.env.path, hookname, *self.args())

        filename = self.filename(hookname)
        if os.path.exists(filename):
            projects = self.projects_enabled(hookname)
            if projects is None:            
                f = file(filename, 'a')
                print_hook(f)                
            else:
                project = os.path.realpath(self.env.path)
                index, lines, projects = projects
                projects.append(project)
                lines[index] = command_line(projects, hookname, *self.args())
                f = file(filename, 'w')
                for line in lines:
                    print >> f, line                    
        else:
            f = self.create(hookname)
            print_hook(f)
            
        f.close()

    def disable(self, hookname):
        if not self.is_enabled(hookname):
            return 
        index, lines, projects = self.projects_enabled(hookname)
        projects = [ os.path.realpath(project) 
                     for project in projects ]
        project = os.path.realpath(self.env.path)
        
        projects.remove(project)
        if projects:
            lines[index] = command_line(projects, hookname, *self.args())
        else:
            lines.pop(index)
            # TODO: list bounds checking
            if lines[index-1] == self.marker():
                index = index-1
                lines.pop(index)
            if not lines[index-1].strip():
                lines.pop(index-1)
            
        f = file(self.filename(hookname), 'w')
        for line in lines:
            print >> f, line
        f.close()

    def is_enabled(self, hookname):
        if os.path.exists(self.filename(hookname)):
            projects = self.projects_enabled(hookname)
            if projects is not None:
                index, lines, projects = projects
                projects = [ os.path.realpath(project) for project in projects ]
                project = os.path.realpath(self.env.path)
                if project in projects: 
                    return True
        return False

    def can_enable(self, hookname):
        return iswritable(self.filename(hookname))
