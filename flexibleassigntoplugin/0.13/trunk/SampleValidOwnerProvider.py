# -*- coding: utf-8 -*-
#
# FlexibleAssignTo - Extension point provider for customizing 
#   the "Assign To" ticket field.
# 
# Copyright (C) 2007 Robert Morris <gt4329b@pobox.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

## trac imports
from trac.core import *
from trac.util.compat import sorted
from trac.util.compat import set
from trac.util.translation import _

## FlexibleAssignTo imports
from flexibleassignto import IValidOwnerProvider, SimpleUser, getlist

## versioning crud
# $Id: SampleValidOwnerProvider.py 2665 2007-10-17 13:08:11Z gt4329b $
__version__ = '0.5'
__revision__ = "$Revision: 2665 $".replace('Revision:','').replace('$','').strip()
version = __version__
fullversion = ".".join([__version__, __revision__])


## SampleValidOwnerProvider module "constants"
DEFAULT_ROLES = 'DEFAULT'

DEMO_USER_STORE = {'MYDOMAIN\\jdoe':{'roles':'DEFAULT',
                                            'fname':'John',
                                            'lname':'Doe',
                                            'email':'jdoe@blah.com'},
                   'MYDOMAIN\\dtabor':{'roles':'DEMOROLE3,DEMOROLE2',
                                            'fname':'Dan',
                                            'lname':'Tabor',
                                            'email':'dtabor@blah.com'},
                   'MYDOMAIN\\jdavis':{'roles':'DEMOROLE2',
                                            'fname':'Josh',
                                            'lname':'Davis',
                                            'email':'jdavis@blah.com'},
                   'MYDOMAIN\\kharrigan':{'roles':'DEMOROLE3,DEFAULT',
                                            'fname':'Kyle',
                                            'lname':'Harrigan',
                                            'email':'kharrigan@blah.com'}
                   }


class SampleValidOwnerProvider(Component):
    """
    This is a demo ValidOwnerProvider implementation, to demonstrate
    how to build a ValidOwnerProvider for use with the FlexibleAssignTo
    plugin.
    
    SampleValidOwnerProvider recognizes a new custom workflow state param
    called "roles_allowed".  The demo user store in this example is just 
    a dictionary, specified at the module level (above) DEMO_USER_STORE.  
    Yes, it's trivial ...but it was intended to be simple.  If "roles_allowed"
    is not specified for a workflow state, DEFAULT_ROLES is used to determine
    the valid owners to display in the "assign to" dropdown for that state.
    """
    implements(IValidOwnerProvider)

    
    def getUsers(self, next_action_obj):
        """
        Top-level method to be called to get users.  Cascade-calls
        specific methods as needed.
        """
        # get workflow state params, if present -- the getlist method
        #  provided by FlexibleAssignTo does some housekeeping for us
        allowedroles = getlist(next_action_obj, 'roles_allowed', 
                                                        keep_empty=False)
        if allowedroles is None:
            allowedroles = DEFAULT_ROLES
        
        # use a dictionary temporarily, to help ensure uniqueness by
        #  username
        user_obj_dict = {}
        for k,v in DEMO_USER_STORE.items():
            if [r for r in v['roles'].split(',') if r in allowedroles]:
                u = DemoSimpleUser()
                u.userlogin = k
                u.lastname = v['lname']
                u.firstname = v['fname']
                u.email = v['email']
                # cleanUsername() also sets the username class attribute
                u.cleanUsername()   
                user_obj_dict.update({u.getUsername():u})
        user_objs = user_obj_dict.values()

        #  SimpleUser *REQUIRES* that the following attributes are set:
        #    - username (set via .setUsername())
        #    - option_value (set via .setOptionValue())
        #    - option_display (set via .setOptionDisplay())
        #  Not setting these attributes will cause assertion errors.
        for u in user_objs:
            u.setOptionValue("%s" % u.getUsername())
            u.setOptionDisplay("*DEMO* - %s, %s (%s)" % (u.lastname, 
                                                            u.firstname, 
                                                            u.getUsername()))
        # sorted by last name (see DemoSimpleUser)
        return sorted(user_objs)
        

class DemoSimpleUser(SimpleUser):
    def cleanUsername(self):
        """
        Returns userlogin without any domain prefix.  Also sets the 
        username class attribute.
        """
        self.setUsername(str(self.userlogin.split('\\')[-1]))
        return self.getUsername()

    def __cmp__(self, other):
        """
        Provides sorting by user last name, via the .lastname class 
        attribute.
        """
        assert self.lastname is not None
        assert other.lastname is not None
        return cmp(self.lastname, other.lastname)
    
    def __repr__(self):
        return "<DemoSimpleUser instance - %s>" % self.userlogin
