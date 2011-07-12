'''
Help Trac macros and plugins to lookup and default configuration items.

Provides class tracmacroconfig.TracMacroConfig

By itself, the module does nothing.
'''

from trac.wiki.api import parse_args

class TracMacroConfig:

    '''
    Instances help a single component in retrieving options.

    A specification of the valid options, and their defaults, is given
    at instantiation, to be used by later .parse or .parse_macro calls.

    The class is especially useful for Trac macro implementations, where
    a certain (configurable) macro argument can be used as a prefix
    to the option names that are then retrieved from trac.ini - permitting
    the site administrator to set up named sets of option values, and
    the page authors to write compact macro invocations using those.

    The option lookup even supports inheritance.
    '''

    def __init__(self, config, section, optionspec, defaultprefix = 'macro', inheritsuffix = 'inherit', configoption = 'config'):

        '''
        Instantiation will probably go into a component's __init__().

        Mandatory arguments to the constructor are:

        config     -- the trac config object, usually self.config,
                      to use in retrieving trac.ini values.
        section    -- the trac.ini section to look at.
        optionspec -- a dict, with the keys giving option names,
                      and the values their builtin defaults, which will
                      be used when the option is neither passed in nor
                      given somewhere in the configuration.
                      The _type_ of the default values, also determines
                      type checking, at least for int values.

        Optional arguments are:

        defaultprefix -- this will be prepended to the keys in optionspec
                         when looking for the option in trac.ini, in case
                         the incoming options to the .parse* methods do not
                         specify something else (see configoption)
        inheritsuffix -- when this is not set to None, it is appended
                         to the trac.ini option prefix under inspection,
                         and if an option with the resulting name exists,
                         its value will be used for further option lookup.
        configoption  -- if the incoming options to the .parse* methods
                         specify an option with this name, it will be
                         removed from the active option dict, and its
                         value will be used in place of defaultprefix
                         when starting the search for options in trac.ini
        '''
        self.config = config
        self.optionspec = optionspec
        self.section = section
        self.defaultprefix = defaultprefix
        self.inheritsuffix = inheritsuffix
        self.configoption = configoption

    def parse_macro(self, content):
        '''
        Parse macro args given in content, returning an options dict.

        Options will be filled in from trac.ini and defaulted if missing,
        so that the returned dict will surely contain each option that was
        specified upon instantiation in optionspec.
        '''
        _, options = parse_args(content, strict=False)
        return self.parse(options)

    def extras(self, options, remove=False):
        '''
        Return those options which are NOT in the instances' optionspec.

        For example, macros can use this to extract any 'unknown'
        option for passing to TracQuery.

        options -- a dict as returned by .parse_macro
        remove  -- if set to True, the returned options are removed from
                   the incoming options dict
        '''
        extras = {}
        for key in options.keys():
            if not key in self.optionspec:
                extras[key] = options[key]
                if remove:
                    del options[key]
        return extras

    def parse(self, options):
        '''
        Fill in missing values in the options[] dict.

        The following code proceeds from explicitly given options
        (incoming options dict), through trac.ini lookup and inheritance,
        to the builtin defaults. The earliest setting, in that order, wins.
        '''
        wanted = self.optionspec.copy()
        for opt in wanted.keys():
            if opt in options:
                if isinstance(wanted[opt], (int, long)):
                    options[opt] = int(options[opt])
                del wanted[opt]
        if self.configoption in options:
            parents = options[self.configoption]
            del options[self.configoption]
        else:
            parents = self.defaultprefix
        self._inherit(options, parents, wanted, {})
        for opt in wanted.keys():
            if opt not in options:
                options[opt] = wanted[opt]
        return options

    def _inherit(self, options, parents, wanted, seen):
        '''
        Recursive lookup in trac.ini.

        options -- dict of the options as known so far
        parents -- string of a single or possibly '|' separated
                   multiple prefixes to use for option lookup in trac.ini.

        If parents contains 'body', and self.optionspec has keys 'knees'
        and 'toes', looks in trac.ini for 'body.knees =' and 'body.toes ='.

        If parents contains a '|' separated list, first look for all
        specified options under the first entry, then under the second,
        and so on.

        If, upon instantiation, an inheritsuffix has not been set to None,
        and we have e.g. 'body.inherit = xxx', a recursive call will be
        made to look for options starting with _that_ prefix. The .inherit
        option can again contain a '|' separated list.
        '''
        for other in [x.strip() for x in parents.split('|')]:
            if other in seen:
                continue
            seen[other] = 1
            if self.inheritsuffix:
                parents = self.config.get(self.section,
                          '%s.%s' % (other, self.inheritsuffix), default=None)
            else:
                parents = None
            for opt in wanted.keys():
                if opt in options:
                    continue
                v = self.config.get(self.section,
                    '%s.%s' % (other, opt), default=self)
                if v is self:
                    continue
                if isinstance(wanted[opt], (int, long)):
                    v = int(v)
                options[opt] = v
                del wanted[opt]
            if parents:
                self._inherit(options, parents, wanted, seen)
