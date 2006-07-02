# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <trac@matt-good.net> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Matthew Good
#
# Author: Matthew Good <trac@matt-good.net>

from trac.core import *
from trac.config import *

class AccountError(TracError):
    """ A generic account error. """

class UnknownUserError(AccountError):
    """ Raise this on an action against an unknown user name. """

class IAccountStore(Interface):
    """An interface for Components that provide a storage method for accounts."""

    def get_users(self):
        """Returns an iterable of the known usernames
        """

    def has_user(self, user):
        """Returns whether the user account exists.
        """
        
    def add_user(self, user):
        """Create a new user.
        """

    def delete_user(self, user):
        """Deletes the user account."""

class IPasswordStore(Interface):
    """An interface for Components that provide a storage method for passwords."""

    def set_password(self, user, password):
        """Sets the password for the user. If you do not define this 
        method, it is assumed you cannot change passwords in this store.
        """

    def check_password(self, user, password):
        """Checks if the password is valid for the user.
        """

class IAccountChangeListener(Interface):
    """An interface for receiving account change events.
    """

    def user_created(self, user):
        """New user
        """

    def user_password_changed(self, user):
        """Password changed
        """

    def user_deleted(self, user):
        """User deleted
        """

class IAccountActionController(Interface):
    """An interface for providing and manipluation account actions.
    """
    
    def get_account_actions(req, account):
        """ Return an interable of (action, label).
        """
        
    def apply_account_action(req, account, action):
        """ Perform the given action on an account.
        """
        
    def intercept_account_action(req, account, action):
        """ Intercept, and possibly alter, an account action.
        """

class AccountManager(Component):
    """The AccountManager component handles all user account management methods
    provided by the IAccountStore and IPasswordStore interfaces.

    The methods will be handled by the underlying password storage
    implementation set in trac.ini with the "account-manager.password_format"
    setting.
    """

    implements(IAccountChangeListener)

    account_store  = OrderedExtensionsOption('account-manager','account_store',IAccountStore,
                                             include_missing=False,
                                             doc="Which account storage backends to use.")
                                             
    password_store = OrderedExtensionsOption('account-manager','password_store',IPasswordStore,
                                             include_missing=False,
                                             doc="Which password storage backends to use.")
    
    change_listeners = ExtensionPoint(IAccountChangeListener)
    action_controllers = ExtensionPoint(IAccountActionController)
    
    store_key = Option('account-manager','password_format',
                       doc='Short-code for the desired password store')

    # Public API
    
    def account_actions(self, req, user):
        """Return a dictionary of the form {action:(label, controller)}."""
        actions = {}
        for controller in self.action_controllers:
            for action, label in controller.get_account_actions(req, user)
                assert action not in actions, "Action %s already registered by %s" % \
                                       (action, actions[action][1].__class__.__name__)
                actions[action] = (label, controller)
        return actions

    def get_users(self):
        for store in self.account_stores:
            for user in store.get_users():
                yield user

    def has_user(self, user):
        for store in self.account_stores:
            if store.has_user(user):
                return True
        return False
        
    # IAccountChangeListener methods

    def user_created(self, user, password):
        self.log.info('Created new user: %s' % user)

    def user_password_changed(self, user):
        self.log.info('Updated password for user: %s' % user)

    def user_deleted(self, user):
        self.log.info('Deleted user: %s' % user)

