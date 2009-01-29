#!/usr/bin/env python
"""
programmatic front end to trac-admin
"""

import subprocess

from trac.admin.console import TracAdmin

class TracLegosAdmin(TracAdmin):
    """TracLegos front-end to Trac's command-line-admin interface"""

    def __init__(self, env):
        TracAdmin.__init__(self, env)

    def list(self, field):
        """
        list fields of a particular type
        """

        # XXX these fucntions are no longer in trunk
        list_functions = { 'component': self.get_component_list,
                           'milestone': self.get_milestone_list, 
                           }

        assert field in list_functions
        return list_functions[field]()

    def remove(self, field, name):
        """
        remove a field of a type with a particular name
        """
        # XXX these fucntions are no longer in trunk
        remove_functions = { 'component': self._do_component_remove,
                             'milestone': self._do_milestone_remove,
                             }

        assert field in remove_functions
        remove_functions[field](name)
        

    def delete_all(self, fields=('component', 'milestone')):
        """delete all default cruft"""
        
        for field in fields:
            for value in self.list(field):
                self.remove(field, value)
        
if __name__ == '__main__':
    pass # TODO
