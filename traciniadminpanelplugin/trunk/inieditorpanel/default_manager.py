import copy

from trac.core import *
from trac.config import ChoiceOption

from inieditorpanel.api import *

class IniEditorEmptySecurityManager(Component):
  """ This security manager imposes ''no restrictions'' what so ever on the
      ini editor. It allows editing of all options.
  """

  implements(IOptionSecurityManager)
  
  def get_option_access(self, section_name, option_name):
    """Returns the access status for this option. 
    
    Must return one of ACCESS_HIDDEN (option can neither be seen nor 
    changed), ACCESS_READONLY (option can be seen but not changed), or
    ACCESS_MODIFIABLE (option can be seen and changed).
    """
    return ACCESS_MODIFIABLE

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
    return True, None


class IniEditorBasicSecurityManager(Component):
  """ Reads the option restrictions from the `trac.ini`. They're read from the
  section `[ini-editor-restrictions]`. Each option is defined as 
  `<section-name>|<option-name>` and the value is either 'hidden' (option can 
  neither be seen nor changed), 'readonly' (option can be seen but not changed),
  or 'modifiable' (option can be seen and changed). Section-wide access can be
  specified by `<section-name>|*`. The default value for options not specified
  can be set by `default-access` in `[ini-editor-restrictions]`. Setting it to
  `modifiable` results in specifying a "black-list", setting it to one of the 
  other two values resuls in specifying a "white-list".
  """

  implements(IOptionSecurityManager)
  
  DEFAULT_RESTRICTIONS = {
      'ini-editor': { '*': ACCESS_READONLY, 'password-options': ACCESS_MODIFIABLE },
      'ini-editor-restrictions': { '*': ACCESS_READONLY },
      'trac': { 'database': ACCESS_HIDDEN # <- may contain the database password
              }
    }
  
  default_access = ChoiceOption('ini-editor-restrictions', 'default-access', 
      [ ACCESS_READONLY, ACCESS_HIDDEN, ACCESS_MODIFIABLE ],
      doc="""Defines the default access level for options that don't have an
      explicit access level defined. Defaults to readonly.""", doc_domain="inieditorpanel")
  
  def __init__(self):
    restrictions = self.config.options('ini-editor-restrictions')
    
    self.restrictions = copy.deepcopy(self.DEFAULT_RESTRICTIONS)
    
    for restriction_on, level in restrictions:
      if restriction_on == 'default-access':
        continue
        
      # NOTE: A dot seems to be a valid character in a option name (see 
      #  [ticket] -> commit_ticket_update_commands.close). A colon (':') is 
      #  considered an assignment operator. So we use the pipe ('|') char in
      #  the hopes that it won't be used anywhere else. But to be on the safe
      #  side we allow it in option names.
      parts = restriction_on.split('|', 2)
      if len(parts) < 2:
        self.log.warning('Invalid restriction name: ' + restriction_on)
        continue  # no pipes in this name; so this is no valid restriction name.
                  # Note that the name may contain more than one pipe if the
                  # option name contains pipe chars.
        
      if level != ACCESS_HIDDEN and level != ACCESS_READONLY and level != ACCESS_MODIFIABLE:
        self.log.warning('Invalid restriction level for ' + restriction_on + ': ' + level)
        continue
        
      if parts[0] not in self.restrictions:
        self.restrictions[parts[0]] = { parts[1]: level }
      else:
        self.restrictions[parts[0]][parts[1]] = level
      
  def get_option_access(self, section_name, option_name):
    """Returns the access status for this option. 
    
    Must return one of ACCESS_HIDDEN (option can neither be seen nor 
    changed), ACCESS_READONLY (option can be seen but not changed), or
    ACCESS_MODIFIABLE (option can be seen and changed).
    """
    section_restrictions = self.restrictions.get(section_name, None)
    if section_restrictions is None:
      return self.default_access
    
    # Return access level with fallbacks
    return section_restrictions.get(option_name, section_restrictions.get('*', self.default_access))

    
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
    return True, None
