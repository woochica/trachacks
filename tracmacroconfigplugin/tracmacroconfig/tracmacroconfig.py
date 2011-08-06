"""Help Trac macros and plugins to lookup and default configuration items.

By itself, the module does nothing.
"""

from trac.config import Option, BoolOption, IntOption, ListOption, \
                        _TRUE_VALUES, ConfigurationError
from trac.wiki.api import parse_args
from trac.util.translation import _

__all__ = [ 'TracMacroConfig' ]

class TracMacroConfig(object):
    """Instances help a single component in retrieving options.

    See the examplemacro.py file for an example of how to use this API.

    The class is especially useful for Trac macro implementations, where
    a certain (configurable) macro argument can be used as a prefix
    to the option names that are then retrieved from trac.ini - permitting
    the site administrator to set up named sets of option values, and
    the page authors to write compact macro invocations using those.

    The option lookup even supports inheritance.
    """

    _is_default = object()
    _is_macroarg = object()
    _is_extra = object()
    _is_funny = [ _is_default, _is_macroarg, _is_extra, None ]

    def __init__(self, section, prefix = 'macro', config = 'config'):
        """
        Mandatory arguments to the constructor are:

        @param section:  The trac.ini section to look at.

        Optional arguments are:

        @param prefix:   This will be prepended by default to option names,
                         when looking for the option in trac.ini.
        @param config    If the incoming options from the macro
                         specify an option with this name, it will be
                         removed from the active option dict, and its
                         value will be used in place of prefix to create
                         the full option names during the search in trac.ini.
        """
        self.tracconfig = None
        self.env = None
        self.wanted = {}
        self.section = section
        self.prefix = prefix
        self.inherit = None
        self.config = config
        self.results = {}

    def setup(self, config, env=None):
        """You MUST call the setup() method in your components __init__
        method, before you use the macroconfig instance for option
        evaluation. Pass in the self.config of your component.

        Optionally, you can pass in your self.env, to enable debug
        logging for option lookup.
        """
        self.tracconfig = config
        if env:
            self.env = env
        self._log('setup(env=%s, config=%s)' % (self.env, self.tracconfig))

    def Option(self, *args, **kwargs):
        return MacroOption(self, *args, **kwargs)

    def BoolOption(self, *args, **kwargs):
        return MacroBoolOption(self, *args, **kwargs)

    def IntOption(self, *args, **kwargs):
        return MacroIntOption(self, *args, **kwargs)

    def ListOption(self, *args, **kwargs):
        return MacroListOption(self, *args, **kwargs)

    def InheritOption(self, *args, **kwargs):
        return MacroInheritOption(self, *args, **kwargs)

    def options(self, content):
        """
        Parse macro args given in content, returning an options dict.

        Options will be filled in from trac.ini and defaulted if missing,
        so that the returned dict will surely contain each option that was
        specified as a MacroOption.

        The resolved options are retained, and will be used when accessing
        the option variables as declared through MacroOption.

        This method returns a dictionary with all the resolved options
        in the macro call, not only those registered. You can use the
        extras() method to extract these extra options.
        """
        if not self.tracconfig:
            raise Exception('TracMacroConfig not setup properly - no config')
        _, options = parse_args(content, strict=False)
        self._parse(options)
        return_options = {}
        for key, ent in self.results.iteritems():
            return_options[key] = ent[0]
        return return_options

    def extras(self, options=None, remove=False):
        """
        Return a dict of those options which are NOT registered as options
        to this instance.

        For example, macros can use this to extract any 'unknown'
        options to guide separate processing, like passing to TracQuery.

        options -- a dict as returned by .options(). Optional, by default
                   the saved options from the last .options() call, are used.
        remove  -- if set to True, the returned options are removed from
                   the incoming options dict. Ignored when options is None
        """
        extras = {}
        if not options:
            for opt, ent in self.results.iteritems():
                if not ent[2]:
                    extras[opt] = ent[0]
        else:
            for opt in options.keys():
                if not opt in self.wanted:
                    extras[opt] = options[opt]
                    if remove:
                        del options[opt]
        return extras

    def option_is_known(self, opt):
        """Return True if the option is known in any way, False otherwise."""
        return opt in self.results

    def option_is_default(self, opt):
        """Return True if the option name is known and is at its
        builtin default value. Otherwise return false."""
        return opt in self.results and self.results[opt][1] is self._is_default

    def option_is_macroarg(self, opt):
        """Return True if the value of the option was given in
        the macro invocation, False otherwise."""
        return opt in self.results and (                     \
            self.results[opt][1] is self._is_macroarg or     \
            self.results[opt][1] is self._is_extra )

    def option_is_extra(self, opt):
        """Return True if the value of the option was given in
        the macro invocation, AND it is an extra argument, i.e.
        not a registered option. Return False otherwise."""
        return opt in self.results and self.results[opt][1] is self._is_extra

    def option_from_trac_ini(self, opt):
        """Given an option name as you would use it in a macro call,
        and regarding the current self.results set, return None if
        the option was not taken from trac.ini, or the full name
        in trac.ini where the value was taken from."""
        if opt in self.results and not self.results[opt][1] in self._is_funny:
            return self.results[opt][1]
        return ''

    def _parse(self, options):
        """
        Fill in missing values in the options[] dict, and validate the
        preexisting options.

        A new dict is returned, where the values are tree-tuples
        ( resolved_value, fullname, MacroOption_instance ) 

        The following code proceeds from explicitly given options
        (incoming options dict), through trac.ini lookup and inheritance,
        to the builtin defaults. The earliest setting, in that order, wins.
        """

        '''Start by considering all registered options, and validating them
        if they are in the incoming options dict'''
        self.results = {}
        wanted = self.wanted.copy()
        for opt in wanted.keys():
            if opt in options:
                self.results[opt] = self._retrieve(wanted, opt, options[opt])

        '''As all registered options, in trac.ini, have composite names,
        consisting of a prefix and the option name separated by a dot,
        now find the starting list of prefixes to consider. Either use
        the value of incoming option of the name found in self.config,
        or use the fixed default prefix from self.prefix'''
        if self.config in options:
            parents = self._parents_to_list(options[self.config])
            del options[self.config]
        else:
            parents = [ self.prefix ]

        '''Look up these composite options'''
        if len(wanted) > 0:
            self._inherit(options, parents, wanted, {})

        '''Set all still unresolved registered options, to their defaults'''
        for opt in wanted.keys():
            if opt not in options:
                self.results[opt] = ( wanted[opt].default, self._is_default, wanted[opt] )

        '''Move over all UNregistered options as they were passed in.'''
        for opt in options.keys():
            if not opt in self.results:
                self.results[opt] = ( options[opt], self._is_extra, None )

    def _inherit(self, options, parents, wanted, seen):
        """
        Recursive lookup in trac.ini.

        @param options:  dict of the options as known so far
        @param parents:  list of string prefixes to try for lookup in trac.ini.
        @param wanted:   as yet unseen registered, wanted, options
        @param seen:     protection against inheritance loops in trac.ini

        If parents is 'body', and self.wanted has keys 'knees'
        and 'toes', looks in trac.ini for 'body.knees' and 'body.toes'.

        When there is a MacroInheritOption defined, e.g. 'inherit',
        and trac.ini contains 'body.inherit', a recursive call will
        be made following the value of that trac.ini option to resolve
        as yet unknown, registered and wanted options.
        """
        for other in parents:
            if other in seen:
                continue
            seen[other] = 1
            parents = self._parents(other)
            for opt in wanted.keys():
                fullname = '%s.%s' % (other, opt)
                v = self.tracconfig.get(self.section, fullname, default=self)
                if not v is self:
                    self.results[opt] = self._retrieve(wanted, opt, v, fullname)
            if parents and len(wanted) > 0:
                self._inherit(options, parents, wanted, seen)

    def _retrieve(self, wanted, opt, value, fullname=_is_macroarg):
        """Upon access, convert the option value to its correct form
        for usage by calling code, as directed by the MacroOption accessor.
        
        Return a three-tuple in the internal format, with the resolved
        value, its fullname, and the MacroOption it is based on.

        Also remove wanted[opt] to prevent later processing."""
        _name = fullname or opt
        self._log('_access(%s) value="%s"' % (_name, value))
        result = (
            wanted[opt]._mc_accessor(_name, value),
            fullname,
            wanted[opt]
        )
        del wanted[opt]
        return result

    def _parents(self, prefix):
        """If self.inherit is wanted, see whether inheritance is
        configured at the specific prefix, and return a list of new
        parents."""
        if self.inherit:
            suffix = self.inherit.suffix
            value = self.tracconfig.get(
                self.section, '%s.%s' % (prefix, suffix), default=None)
            if value:
                return self._parents_to_list(value)
        return None

    def _parents_to_list(self, value):
        return [ x.strip() for x in value.split('|') ]

    def _register(self, option):
        """Called internally by the MacroOption contructor, to register
        each option against the macroconfig instance."""
        if isinstance(option, MacroInheritOption):
            self.inherit = option
        elif isinstance(option, MacroOption):
            self.wanted[option.suffix] = option
        else:
            raise Exception('TracMacroConfig._register needs a MacroOption')

    def _log(self, msg):
        if self.env:
            self.env.log.debug('TracMacroConfig %s' % msg)

class MacroOption(object):
    """Descriptor for string macro options. Also the base class
    of the rest of the pack."""

    def __init__(self, mc, name, default=None, doc=''):
        self.mc = mc
        self.suffix = name
        self.name = mc.prefix + '.' + name
        self.default = default
        self.__doc__ = doc
        mc._register(self)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not self.suffix in self.mc.results:
            return None
        return self._mc_accessor(self.name, self.mc.results[self.suffix][0])

    def _mc_accessor(self, key, value):
        self.mc._log('MacroOption key="%s" value="%s"' % (key, value))
        return value

    def __set__(self, instance, value):
        raise AttributeError, 'can\'t set attribute'

    def __repr__(self):
        return '<%s [%s] "%s">' % (self.__class__.__name__, self.mc.section,
                                   self.name)

class MacroBoolOption(MacroOption):
    """Descriptor for boolean macro options."""

    def __init__(self, mc, name, default=None, doc=''):
        super(MacroBoolOption, self).__init__(mc, name, default, doc)

    def _mc_accessor(self, key, value):
        if isinstance(value, basestring):
            value = value.lower() in _TRUE_VALUES
        self.mc._log('MacroBoolOption key="%s" value=%s' % (key, value))
        return bool(value)


class MacroIntOption(MacroOption):
    """Descriptor for int macro options."""

    def __init__(self, mc, name, default=None, doc=''):
        super(MacroIntOption, self).__init__(mc, name, default, doc)

    def _mc_accessor(self, key, value):
        if value is None:
            return None
        try:
            value = int(value)
        except ValueError:
            raise ConfigurationError(
                   _('[%(section)s] %(entry)s: expected integer, got %(value)s',
                      section=self.mc.section, entry=key, value=repr(value)))
        self.mc._log('MacroIntOption key="%s" value=%s' % (key, value))
        return value

class MacroListOption(MacroOption):
    """Descriptor for list macro options."""

    def __init__(self, mc, name, default=None,
                 sep=',', keep_empty=False, doc=''):
        super(MacroListOption, self).__init__(mc, name, default, doc)
        self.sep = sep
        self.keep_empty = keep_empty

    def _mc_accessor(self, key, value):
        if value:
            if isinstance(value, basestring):
                items = [item.strip() for item in value.split(self.sep)]
            else:
                items = list(value)
            if not self.keep_empty:
                items = filter(None, items)
        else:
            items = []
        self.mc._log('MacroListOption key="%s" sep="%s" value=%s' % (
            key, self.sep, items))
        return items


class MacroInheritOption(MacroOption):
    """Descriptor for the special inherit option."""
    pass
