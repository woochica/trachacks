from trac.ticket import TicketSystem

PREFIX = 'dynfields.'
PREF_DEFAULTS = {'(pref)':'1',
                 '(pref:enable)':'1',
                 '(pref:enabled)':'1',
                 '(pref:disable)':'0',
                 '(pref:disabled)':'0',
                 }

class Options(dict):
    """A thin dict wrapper of ticket-custom options to handle specifying,
    loading and saving user preferences for any rule.  User preferences
    are specified by '(pref)' appended to a rule spec as follows:
    
      [ticket-custom]
      version.show_when_type = enhancement (pref)
    """
    
    def __init__(self, env):
        """Fills self with ticket-custom options with '(pref)' stripped
        from values.  Maintains which options/rules have been configured
        for user preference."""
        self.env = env
        self._pref_defaults = {}
        for key, val in self.env.config['ticket-custom'].options():
            for pref,default in PREF_DEFAULTS.items():
                if val.endswith(pref):
                    val = val.replace(pref,'').rstrip()
                    self._pref_defaults[key] = default
                    break
            self[key] = val
            
        # add built-in field types
        for field in TicketSystem(self.env).get_ticket_fields():
            self[field['name']] = field['type']
    
    def has_pref(self, key):
        """Returns True if the given key is configured for user preference."""
        return key in self._pref_defaults
    
    def is_enabled(self, req, key):
        """Returns True if there's no user preference configured for this
        key or if there is and the user enabled the rule spec (the default)."""
        if key not in self._pref_defaults:
            return True
        
        # return the default pref value if not set
        return req.session.get(PREFIX+key, self._pref_defaults[key]) == '1'
    
    def get_value_and_options(self, req, target, key):
        """Returns the preference value for the given key if configured
        for being set by user preference.  If no user preference has been
        set yet, the target field's default value is returned."""
        value = ''
        options = []
        for field in TicketSystem(self.env).get_ticket_fields():
            if field['name'] == target:
                value = field.get('value', value)
                options = field.get('options', options)
                break
        if key in self._pref_defaults:
            value = req.session.get(PREFIX+key+'.value', value)
        return value,options
    
    def get_pref(self, req, target, key):
        """Returns the data needed for preferences.  The data returned
        must be a dict with these keys:
        
          id (based on unique key)
          label (of checkbox)
          enabled ('1' or '0')
          type ('none' or 'select', TODO: support 'text')
          options (list of options if type is 'select')
          value (saved preference or default value)
        """
        value,options = self.get_value_and_options(req, target, key)
        return {'id': PREFIX+key,
                'label': '%s = %s' % (key,self[key]),
                'enabled': req.session.get(PREFIX+key,self._pref_defaults[key]),
                'type': 'none',
                'options': options,
                'value': value,
                }
    
    def set_prefs(self, req):
        """Saves the user's preferences."""
        # save checkbox settings
        for key in self._pref_defaults:
            req.session[PREFIX+key] = req.args.get(PREFIX+key,'0')
        
        # now save values
        for arg,value in req.args.items():
            if not arg.startswith(PREFIX) or not arg.endswith('.value'):
                continue
            req.session[arg] = value
