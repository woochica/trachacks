import re
from trac.core import *

class IRule(Interface):
    """An extension point interface for adding rules.  Rule processing
    is split into two parts: (1) rule specification (python), (2) rule
    implementation (JS).
    
    The python and JS parts are linked by instantiating the JS rule
    implementation with the corresponding python rule's class name.
    For example, the JS rule implementation corresponding with the
    HideRule python class must be instantiated as follows in rules.js:
    
      var hiderule = new Rule('HideRule');
    """
    
    def get_trigger(self, target, key, opts):
        """Return the field name that triggers the rule, or None if not found
        for the given target field and ticket-custom options key and dict.
        For example, if the 'version' field is to be hidden based on the
        ticket type, then the returned trigger field name should be 'type'."""
       
    def update_spec(self, req, key, opts, spec):
        """Update the spec dict with the rule's specifications needed for
        the JS implementation.  The spec dict is defaulted to include the
        rule's name (rule_name), the trigger field's name (trigger), the
        target field's name (target), and the preference or default value
        if applicable (value)."""
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        """Update the pref dict with the data needed for preferences.
        The primary dict keys to change are:
        
          label (of checkbox)
          type ('none' or 'select')
        
        Default values for the above are provided as well as for the
        keys below (which should usually not be changed):
        
          id (based on unique key)
          enabled ('1' or '0')
          options (list of options if type is 'select')
          value (saved preference or default value)
        """


class Rule(object):
    """Abstract class for common rule properties and utilities."""
    
    OVERWRITE = '(overwrite)'
    
    @property
    def name(self):
        """Returns the rule instance's class name.  The corresponding
        JS rule must be instantiated with this exact name."""
        return self.__class__.__name__
    
    @property
    def title(self):
        """Returns the rule class' title used for display purposes.
        This default implementation returns the rule's name with any
        camel case split into words and the last word made plural.
        This property/method can be overriden as needed."""
        # split CamelCase to Camel Case
        title = self._split_camel_case(self.name)
        if not title.endswith('s'):
            title += 's'
        return title
    
    @property
    def desc(self):
        """Returns the description of the rule.  This default implementation
        returns the first paragraph of the docstring as the desc."""
        return self.__doc__.split('\n')[0]
    
    # private methods
    def _capitalize(self, word):
        if len(word) <= 1:
            return word.upper()
        return word[0].upper() + word[1:]
    
    def _split_camel_case(self, s):
        return re.sub('((?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z]))', ' ', s)
    
    def _extract_overwrite(self, target, key, opts):
        """Extract any <overwrite> prefix from value string."""
        value = opts[key]
        if value.endswith(self.OVERWRITE):
            value = value.replace(self.OVERWRITE,'').rstrip()
            overwrite = 'true'
        else:
            overwrite = opts.get('%s.overwrite' % target,'false')
        return value,overwrite
    

class ClearRule(Component, Rule):
    """Clears one field when another changes.
    
    Example trac.ini specs:
    
      [ticket-custom]
      version.clear_on_change_of = milestone
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.clear_on_change_of' % target:
            return opts[key]
        return None
        
    def update_spec(self, req, key, opts, spec):
        target = spec['target']
        spec['op'] = 'clear'
        spec['clear_on_change'] = opts.get(target+'.clear_on_change','true')

    def update_pref(self, req, trigger, target, key, opts, pref):
        pref['label'] = "Clear %s when %s changes" % (target, trigger)


class CopyRule(Component, Rule):
    """Copies a field (when changed) to another field (if empty and visible).
    
    Example trac.ini specs:
    
      [ticket-custom]
      captain.copy_from = owner
      
    In this example, if the owner value changes, then the captain field's
    value gets set to that value if the captain field is empty and visible
    (the default).  By default, the current value if set will not be
    overwritten.  To overwrite the current value, add "(overwrite)" as
    follows:
    
      [ticket-custom]
      captain.copy_from = (overwrite) owner
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.copy_from' % target:
            return self._extract_overwrite(target, key, opts)[0]
        return None
        
    def update_spec(self, req, key, opts, spec):
        target = spec['target']
        spec['op'] = 'copy'
        spec['overwrite'] = self._extract_overwrite(target, key, opts)[1]

    def update_pref(self, req, trigger, target, key, opts, pref):
        pref['label'] = "Copy %s to %s" % (trigger, target)


class DefaultRule(Component, Rule):
    """Defaults a field to a user-specified value if empty.
    
    Example trac.ini specs:
    
      [ticket-custom]
      cc.default_value = (pref)
      cc.append = true
      
    If the field is a non-empty text field and 'append' is true, then the
    field is presumed to be a comma-delimited list and the preference value
    is appended if not already present.
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.default_value' % target:
            return target
        return None
        
    def update_spec(self, req, key, opts, spec):
        spec['op'] = 'default'
        spec['append'] = opts.get(spec['target']) == 'select' and 'false' or \
                         opts.get(spec['target']+'.append','false')
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        # "Default trigger to <select options>"
        pref['label'] = "Default %s to" % target
        if opts.get(target) == 'select':
            pref['type'] = 'select'
        else:
            pref['type'] = 'text'


class HideRule(Component, Rule):
    """Hides a field based on another field's value (or always).
    
    Example trac.ini specs:
    
      [ticket-custom]
      version.show_when_type = enhancement
      milestone.hide_when_type = defect
      alwayshide.hide_always = True
      alwayshide.clear_on_hide = False
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        rule_re = re.compile(r"%s.(?P<op>(show|hide))_when_(?P<trigger>.*)" \
                             % target)
        match = rule_re.match(key)
        if match:
            return match.groupdict()['trigger']
            
        # try finding hide_always rule
        if key == "%s.hide_always" % target:
            return 'type' # requires that 'type' field is enabled
        return None
    
    def update_spec(self, req, key, opts, spec):
        target = spec['target']
        trigger = spec['trigger']
        
        spec_re = re.compile(r"%s.(?P<op>(show|hide))_when_%s" \
                             % (target,trigger))
        match = spec_re.match(key)
        if match:
            spec['op'] = match.groupdict()['op']
            spec['trigger_value'] = opts[key]
            spec['hide_always'] = \
                str(self._is_always_hidden(req, key, opts, spec)).lower()
        else: # assume 'hide_always' rule
            spec['op'] = 'show'
            spec['trigger_value'] = 'invalid_value'
            spec['hide_always'] = 'true'
        spec['clear_on_hide'] = opts.get(target+'.clear_on_hide','true')
        spec['link_to_show'] = opts.get(target+'.link_to_show','false')
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        spec = {'trigger':trigger,'target':target}
        self.update_spec(req, key, opts, spec)
        # "Show/Hide target when trigger = value"
        trigval = spec['trigger_value'].replace('|',' or ')
        pref['label'] = "%s %s when %s = %s" % (self._capitalize(spec['op']),
                                                target, trigger, trigval)
        
        # special case when trigger value is not a select option
        _,options = opts.get_value_and_options(req, trigger, key)
        value = spec['trigger_value']
        if options and value and value not in options and '|' not in value:
            # "Always hide/show target"
            if spec['op'] == 'hide':
                opp = 'show'
            else:
                opp = 'hide'
            pref['label'] = "Always %s %s" % (opp, target)
    
    def _is_always_hidden(self, req, key, opts, spec):
        trigger = spec['trigger']
        _, options = opts.get_value_and_options(req, trigger, key)
        value = spec['trigger_value']
        if options and value and value not in options and '|' not in value:
            return spec['op'] == 'show'
        return False


class ValidateRule(Component, Rule):
    """Checks a field for an invalid value.
    
    Example trac.ini specs:
    
      [ticket-custom]
      milestone.invalid_if = 
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.invalid_if' % target:
            return target
        return None
    
    def update_spec(self, req, key, opts, spec):
        spec['op'] = 'validate'
        spec['value'] = opts[key]
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        suffix = opts[key] and "= %s" % opts[key] or "is empty"
        pref['label'] = "Invalid if %s %s" % (target, suffix)


class SetRule(Component, Rule):
    """Sets a field based on another field's value.
    
    Example trac.ini specs:
    
      [ticket-custom]
      milestone.set_to_!_when_phase = implementation|verifying
    
    The "!" is used only for select fields to specify the first non-empty
    option; a common use case is to auto-select the current milestone.
    By default, the current value if set will not be overwritten.  To
    overwrite the current value, add "(overwrite)" as follows:
    
      [ticket-custom]
      milestone.set_to_!_when_phase = (overwrite) implementation|verifying
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        rule_re = re.compile(r"%s.set_to_(.*)_when_(?P<trigger>.+)" % target)
        match = rule_re.match(key)
        if match:
            return match.groupdict()['trigger']
        return None
    
    def update_spec(self, req, key, opts, spec):
        target,trigger = spec['target'],spec['trigger']
        spec_re = re.compile(r"%s.set_to_(?P<to>.*)_when_%s" % (target,trigger))
        match = spec_re.match(key)
        if not match:
            return
        spec['set_to'] = match.groupdict()['to']
        spec['trigger_value'],spec['overwrite'] = \
            self._extract_overwrite(target, key, opts)
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        spec = {'target':target,'trigger':trigger}
        self.update_spec(req, key, opts, spec)
        # "When trigger = value set target to"
        trigval = spec['trigger_value'].replace('|',' or ')
        if spec['set_to'] == '*':
            set_to = ''
            if opts.get(target) == 'select':
                pref['type'] = 'select'
            else:
                pref['type'] = 'text'
        elif spec['set_to'] == '!':
            set_to = 'the first non-empty option'
        elif spec['set_to'] == '':
            set_to = '(empty)'
        else:
            set_to = spec['set_to']
        pref['label'] = "When %s = %s, set %s to %s" % \
                            (trigger, trigval, target, set_to)
