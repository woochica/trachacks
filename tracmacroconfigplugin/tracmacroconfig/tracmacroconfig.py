"""Help Trac macros and plugins to lookup and default configuration items.

By itself, the module does nothing.
"""

from trac.core import TracError
from trac.config import _TRUE_VALUES, ConfigurationError
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

    _is_default = 'default'
    _is_macroarg = 'macroarg'
    _is_extra = 'extra'
    _is_funny = [ _is_default, _is_macroarg, _is_extra ]

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
        self.tracenv = None
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
            self.tracenv = env
        self._log('setup(env=%s, config=%s)' % (self.tracenv, self.tracconfig))

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
        self._log('parse incoming %s' % options)
        self._parse(options)
        results = {}
        for key, ent in self.results.iteritems():
            results[key] = ent[0]
        self._log('parse results %s' % results)
        return results

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
                if ent[1] is self._is_extra:
                    extras[opt] = ent[0]
        else:
            for opt in options.keys():
                if not opt in self.wanted:
                    extras[opt] = options[opt]
                    if remove:
                        del options[opt]
        return extras

    def extra(self, opt):
        """Get the value for the extra option named opt, or None if missing."""
        if self.option_is_extra(opt):
            return self.results[opt][0]
        else:
            return None

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

    def option_qualified_name(self, opt):
        """Given an option name as you would use it in a macro call,
        return its qualified name, a pair (two-element tuple), with
        the first element being one of 'trac.ini', 'default', 'macroarg',
        or 'extra', and the second element being the full name from trac.ini,
        or the option name itself otherwise."""
        if not opt in self.results:
            return ('unknown', opt)
        elif not self.results[opt][1] in self._is_funny:
            return ('trac.ini', self.results[opt][1])
        else:
            return (self.results[opt][1], opt)

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
                self.results[opt] = self._access(wanted, opt, options[opt])

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
            self.results[opt] = (
                wanted[opt].default,
                self._is_default,
                wanted[opt]
            )

        '''Move over all UNregistered options as they were passed in.'''
        for opt in options.keys():
            if not opt in self.results:
                self.results[opt] = (
                    options[opt],
                    self._is_extra,
                    None
                )

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
            self._log('try remaining options "%s.*"' % other)
            seen[other] = 1
            parents = self._parents(other)
            for opt in wanted.keys():
                fullname = '%s.%s' % (other, opt)
                v = self.tracconfig.get(self.section, fullname, default=self)
                if not v is self:
                    self.results[opt] = self._access(wanted, opt, v, fullname)
            if parents and len(wanted) > 0:
                self._inherit(options, parents, wanted, seen)

    def _access(self, wanted, opt, value, fullname=_is_macroarg):
        """Upon access, convert the option value to its correct form
        for usage by calling code, as directed by the MacroOption accessor.
        
        Return a three-tuple in the internal format, with the resolved
        value, its fullname, and the MacroOption it is based on.

        Also remove wanted[opt] to prevent later processing."""
        result = (
            wanted[opt]._access(value),
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
            suffix = self.inherit.name
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
            self.wanted[option.name] = option
        else:
            raise Exception('TracMacroConfig._register needs a MacroOption')

    def _raise_value_error(self, option, typestring, value):
        """Helper for Macro*Option classes to raise an appropriate
        value error when a malformed value is supplied for an option."""
        qual = option._qualified_name()
        if qual[0] == 'trac.ini':
            raise ConfigurationError(
                _('trac.ini [%(sec)s] %(opt)s = "%(val)s": invalid %(type)s',
                  sec=self.section, opt=qual[1],
                  type=typestring, val=repr(value)))
        if qual[0] == 'macroarg':
            raise ValueError(
                _('macro argument %(opt)s = "%(val)s": invalid %(type)s',
                  opt=qual[1], type=typestring, val=repr(value)))
        if qual[0] == 'default':
            raise TracError(
                _('plugin default %(opt)s = "%(val)s": invalid %(type)s',
                  opt=qual[1], type=typestring, val=repr(value)))

    def _log(self, msg):
        if self.tracenv:
            self.tracenv.log.debug(str(msg))

class MacroOption(object):
    """Descriptor for string macro options. Also the base class
    of the rest of the pack."""

    def __init__(self, mc, name, default=None, doc=''):
        self.mc = mc
        self.name = name
        self.default = default
        self.__doc__ = doc
        mc._register(self)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not self.name in self.mc.results:
            return None
        return self._access(self.mc.results[self.name][0])

    def __set__(self, instance, value):
        raise AttributeError, 'can\'t set attribute'

    def __repr__(self):
        return '<%s [%s] "%s">' % (
            self.__class__.__name__, self.mc.section, self.name)

    def _qualified_name(self):
        return self.mc.option_qualified_name(self.name)

    def _access(self, value):
        self._log_access('value="%s"' % value)
        return value

    def _log_access(self, valueinfo):
        qual = self._qualified_name()
        source = qual[0]
        if source == 'trac.ini':
            source += ' [%s]' % self.mc.section
        self.mc._log('%s source="%s" key=%s %s' % (
            self.__class__.__name__, source, qual[1], valueinfo))

class MacroBoolOption(MacroOption):
    """Descriptor for boolean macro options."""

    def _access(self, value):
        if not value is None:
            if isinstance(value, basestring):
                value = value.lower() in _TRUE_VALUES
            value = bool(value)
        self._log_access('value=%s' % str(value))
        return value


class MacroIntOption(MacroOption):
    """Descriptor for int macro options."""

    def _access(self, value):
        if not value is None:
            try:
                value = int(value)
            except ValueError:
                self.mc._raise_value_error(self, 'integer', value)
        self._log_access('value=%s' % str(value))
        return value

class MacroListOption(MacroOption):
    """Descriptor for list macro options."""

    def __init__(self, mc, name, default=None,
                 sep=',', keep_empty=False, doc=''):
        self.sep = sep
        self.keep_empty = keep_empty
        super(MacroListOption, self).__init__(mc, name, default, doc)

    def _access(self, value):
        if not value is None:
            if isinstance(value, basestring):
                value = [item.strip() for item in value.split(self.sep)]
            else:
                value = list(value)
            if not self.keep_empty:
                value = filter(None, value)
        self._log_access('sep="%s" value=%s' % (self.sep, value))
        return value


class MacroInheritOption(MacroOption):
    """Descriptor for the special inherit option."""
    pass
