from trac.core import *

ACCESS_HIDDEN = 'hidden'
ACCESS_READONLY = 'readonly'
ACCESS_MODIFIABLE = 'modifiable'

class IOptionSecurityManager(Interface):
  """Extension point interface for restricting access to certain `trac.ini`
  options in the ini editor as well as defining rules for valid option values.
  """
  
  def get_option_access(self, section_name, option_name):
    """Returns the access status for this option. 
    
    Must return one of ACCESS_HIDDEN (option can neither be seen nor 
    changed), ACCESS_READONLY (option can be seen but not changed), or
    ACCESS_MODIFIABLE (option can be seen and changed).
    """

  def is_value_valid(self, section_name, option_name, option_value):
    """Checks whether the specified value is valid for the specified option.
       This can be used for example to restrict system paths to a certain
       parent directory. Will also be used against default values, if they're
       to be used.
       
       Returns `True` (valid) or `False` (invalid) as first return value and
       a (possibly empty) string as second return value containing the reason 
       why this value is invalid.
       
       Note that this method is only called if the user has actually write
       permissions to this option.
       
       Note also that this method is only called for changed values. So if the
       `trac.ini` already contains invalid values, then they won't be checked.
    """
