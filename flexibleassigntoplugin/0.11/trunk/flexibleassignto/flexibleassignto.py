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

## python imports
from pprint import pprint, pformat

## trac imports
from trac.env import Environment
from trac.core import *
from trac.util.compat import sorted
from trac.util.compat import set
from trac.util.translation import _
from trac.web import IRequestFilter
from trac.ticket.default_workflow import get_workflow_config
from trac.config import _TRUE_VALUES
from genshi.builder import tag

## versioning crud
# $Id$
__version__ = '0.6'
__revision__ = "$Revision$".replace('Revision:','').replace('$','').strip()
version = __version__
fullversion = ".".join([__version__, __revision__])


class IValidOwnerProvider(Interface):
    def getUsers(self, next_action_obj):
        """Returns a list of (unique) SimpleUser objects"""
        raise NotImplementedError


class SimpleUser:
    """
    Simple wrapper class for standard user params.  All are optional
    except:
     username
     option_value
     option_display
    Failure to provide a non-None value for these will raise assert 
    exceptions when the related get accessor method is called.
    """
    def __init__(self):
        self.personid = None
        self.firstname = None
        self.lastname = None
        self.fullname = None
        self.userlogin = None
        self.email = None
        self.username = None
        self.option_value = None
        self.option_display = None

    def setUsername(self, value):
        self.username = value

    def getUsername(self):
        assert self.username is not None
        return self.username

    def setOptionValue(self, value):
        self.option_value = value

    def getOptionValue(self):
        assert self.option_value is not None
        return self.option_value

    def setOptionDisplay(self, value):
        self.option_display = value

    def getOptionDisplay(self):
        assert self.option_display is not None
        return self.option_display


def getlist(action_obj, name, default=None, sep=',', keep_empty=False):
    """Return a list of values that have been specified as a single
    comma-separated option.

    A different separator can be specified using the `sep` parameter. If
    the `skip_empty` parameter is set to `True`, empty elements are omitted
    from the list.
    
    Shamelessly copied from Section.getlist() in trac/config.py
    """
    value = action_obj.get(name, default)
    items = None
    if value:
        if isinstance(value, basestring):
            items = [item.strip() for item in value.split(sep)]
        else:
            items = list(value)
        if not keep_empty:
            items = filter(None, items)
    return items        


def getbool(action_obj, name, default=None):
    """Return the value of the specified option as boolean.

    This method returns `True` if the option value is one of "yes", "true",
    "enabled", "on", or "1", ignoring case. Otherwise `False` is returned.
    
    Shamelessly copied from Section.getbool() in trac/config.py
    """
    value = action_obj.get(name, default)
    if isinstance(value, basestring):
        value = value.lower() in _TRUE_VALUES
    return bool(value)


class FlexibleAssignTo(Component):
    """
    FlexibleAssignTo finally gives long-suffering Trac admins a way to 
    easily customize the "assign to" field on tickets.  It provides several 
    base classes for you to override and implement your own methods for
    providing lists of valid users -- you can even customize valid users for 
    each state in your workflow.  

    See the included README for detailed setup and extension instructions.
    
    """
    
    implements(IRequestFilter)
    
    valid_owner_controllers = ExtensionPoint(IValidOwnerProvider)
    
    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self.actions = get_workflow_config(self.config)
        self.ensureUserData = self.config.getbool('flexibleassignto', 
                                                'ensure_user_data', False)
        self.use_custom_get_known_users = self.config.getbool(
            'flexibleassignto', 'use_custom_get_known_users', False)
        if self.use_custom_get_known_users:
            self._replace_get_known_users()


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if not data or len(self.valid_owner_controllers) == 0:
            return template, data, content_type
        next_action_controls = data.get('action_controls', [])
        for i in range(len(next_action_controls)):
            next_action_name, first_label, fragment, hints = \
                                                    next_action_controls[i]
            next_action_obj = self.actions[next_action_name]
            # look for an optional workflow state param 'use_flexibleassignto'
            #  if present and set to 'false', don't operate on this state
            operate_on_this_action = getbool(next_action_obj, 
                                            'use_flexibleassignto', True)
            if operate_on_this_action:
                operations = next_action_obj['operations']
                if 'set_owner' in operations:
                    new_fragment = self._build_select(req, next_action_name, 
                                                        next_action_obj)
                    next_action_controls[i] = (next_action_name, first_label,
                                                        new_fragment, hints)
        return template, data, content_type

    # "internal" methods
    def _build_select(self, req, nextActionName, nextActionObj):
        """
        Takes a request object, the name of the next action (as a string),
        and the next action object itself.  Calls each registered 
        IValidOwnerProvider and builds a dictionary of user_objs using
        usernames as keys (which is why usernames are required).  Calls
        _ensure_user_data to insert user data into session_attribute if
        the "ensure user data" capability has been enabled.
        
        Returns a complete select tag object, ready for rendering.
        """
        # get a list of data about owners valid for this next state
        #  use an intermediate dict to ensure uniqueness by username
        user_objs = {}
        for voc in self.valid_owner_controllers:
            tmpusers = voc.getUsers(nextActionObj)
            [user_objs.update({str(u.getUsername()).strip():u}) 
                                                        for u in tmpusers]
        user_objs = user_objs.values()
        if self.ensureUserData:
            self._ensure_user_data(user_objs)
        # check to see if the current owner is in the list of valid owners;
        #  if so, pre-select them in the select control
        #id = nextActionName + '_reassign_owner'
        ## updated for changed control name (0.11 release and higher) - thanks to chris on http://trac-hacks.org/ticket/3494
        id = 'action_' + nextActionName + '_reassign_owner'
        selected_owner = req.args.get(id, req.authname)
        # build the actual options tag objects 
        option_tags = []
        for u in sorted(user_objs):
            username = u.getUsername()
            isselected = (username == selected_owner or None)
            option_tags.append(tag.option(u.getOptionDisplay(), 
                                            selected=isselected, 
                                            value=u.getOptionValue()))
        # build the final select control -- minus the assumed "to"
        _tag = tag.select(option_tags, id=id, name=id)
        return _tag

    def _get_allusers_session_info(self, cnx):
        """
        """
        cursor = cnx.cursor()
        cursor.execute('''
            SELECT DISTINCT n.sid AS sid, n.value AS name, e.value AS email
            FROM session_attribute AS n 
             LEFT JOIN session_attribute AS e ON (e.sid=n.sid
                AND e.authenticated=1 AND e.name = 'email')
            WHERE n.authenticated=1 
                AND n.name = 'name'
            ORDER BY n.sid''')
        for username,name,email in cursor:
            yield username, name, email        

    def _ensure_user_data(self, users):
        """
        Insert user data for each SimpleUser object in the users list into
        session_attribute.  NOTE: this method will NOT overwrite existing
        values for 'name' or 'email'.
        """
        EMAIL_SQL = '''INSERT INTO session_attribute 
            (sid, authenticated, name, value) 
            VALUES ('%s', 1, 'email' , '%s')'''
        NAME_SQL = '''INSERT INTO session_attribute 
            (sid, authenticated, name, value) 
            VALUES ('%s', 1, 'name' , '%s')'''
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        known_users = self._get_allusers_session_info(db)
        known_usernames = [u[0] for u in known_users]
        for u in users:
            _username = str(u.getUsername()).strip()
            _email = str(u.email).strip()
            _fullname = str(u.fullname).strip()
            if u.getUsername() and _username != '' and \
                                            _username not in known_usernames:
                if u.email and _email != '':
                    cursor.execute(EMAIL_SQL % (_username, _email))
                if u.fullname and _fullname != '':
                    cursor.execute(NAME_SQL % (_username, _fullname))
        db.commit()
        cursor.close()

    # internal method for 'use_custom_get_known_users' option

    def _replace_get_known_users(self):
        _wrapfunc(Environment, "get_known_users", fat_get_known_users)
        self.env.log.info("FlexibleAssignTo plugin has replaced"
            " the default get_known_users() method in"
            " trac.environment.Environment (per trac.ini directive"
            " use_custom_get_known_users = true)")


def fat_get_known_users(original_callable, the_class, cnx=None, 
                                                            *args, **kwargs):
    """Generator that yields information about all known user info.
    This is markedly different from the default Trac (trac.env) method
    of the same name: whereas the Trac default get_known_users returns
    info only for those users who have logged in, this method returns
    info for every user who has data in the session_attribute table and
    is flagged authenticated (e.g., session_attribute.authenticated = 1).
    
    This functionality was designed to work in concert with the 
    "ensure_user_data" feature, which autopopulates user email & name 
    in the session_attribute table.  See the README for more about this 
    capability.

    This function generates one tuple for every user, of the form
    (username, name, email) ordered alpha-numerically by username.

    @param cnx: the database connection
    """
    the_class.log.debug("retrieving user info from session_attribute")
    if not cnx:
        cnx = the_class.get_db_cnx()
    cursor = cnx.cursor()
    cursor.execute('''
SELECT DISTINCT n.sid AS sid, n.value AS name, e.value AS email
FROM session_attribute AS n 
 LEFT JOIN session_attribute AS e ON (e.sid=n.sid
    AND e.authenticated=1 AND e.name = 'email')
WHERE n.authenticated=1 
    AND n.name = 'name'
ORDER BY n.sid
        ''')
    for username,name,email in cursor:
        yield username, name, email



# ===========================================================================
# Thanks to osimons for this excellent Python method replacement wizardry...
#
# ===========================================================================

def _wrapfunc(obj, name, processor, avoid_doublewrap=True):
     """ patch obj.<name> so that calling it actually calls, instead,
             processor(original_callable, *args, **kwargs)

     Function wrapper (wrap function to extend functionality)
     Implemented from Recipe 20.6 / Python Cookbook 2. edition

     Example usage of funtion wrapper:

     def tracing_processor(original_callable, *args, **kwargs):
         r_name = getattr(original_callable, '__name__', '<unknown>')
         r_args = map(repr, args)
         r_args.extend(['%s=%s' % x for x in kwargs.iteritems()])
         print "begin call to %s(%s)" % (r_name, ", ".join(r_args))
         try:
             result = original_callable(*args, **kwargs)
         except:
             print "EXCEPTION in call to %s" % (r_name,)
             raise
         else:
             print "call to %s result: %r" % (r_name, result)
             return result

     def add_tracing_prints_to_method(class_object, method_name):
         wrapfunc(class_object, method_name, tracing_processor)
     """
     # get the callable at obj.<name>
     call = getattr(obj, name)
     # optionally avoid multiple identical wrappings
     if avoid_doublewrap and getattr(call, 'processor', None) is processor:
         return
     # get underlying function (if any), and anyway def the wrapper closure
     original_callable = getattr(call, 'im_func', call)
     def wrappedfunc(*args, **kwargs):
         return processor (original_callable, *args, **kwargs)
     # set attributes, for future unwrapping and to avoid double-wrapping
     wrappedfunc.original = call
     wrappedfunc.processor = processor
     # 2.4 only: wrappedfunc.__name__ = getattr(call, '__name__', name)
     # rewrap staticmethod and classmethod specifically (if obj is a class)
     import inspect
     if inspect.isclass(obj):
         if hasattr(call, 'im_self'):
             if call.im_self:
                 wrappedfunc = classmethod(wrappedfunc)
         else:
             wrappedfunc = staticmethod(wrappedfunc)
     # finally, install the wrapper closure as requested
     setattr(obj, name, wrappedfunc)


def _unwrap(obj, name):
     """ undo the effects of wrapfunc(obj, name, processor) """
     setattr(obj, name, getattr(obj, name).original)

