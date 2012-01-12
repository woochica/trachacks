#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#


def PatchedTicket(*args, **argv):

    # Workaround a bug in Agilo, which
    # So import at the latest moment...    
    from trac.ticket.web_ui import Ticket
    class PatchedTicketClass(Ticket):
        ''' patched version of the Ticket class, that doesn't make the difference between a field defaulting to an empty string, and a field not defaulted
        '''

        # TODO: report it as a bug, and/or check if it is fixed in more recent versions
        def _init_defaults(self, db=None):
            for field in self.fields:
                default = None
                if field['name'] in ['resolution']:
                    # Ignore for new - only change through workflow
                    pass
                elif not field.get('custom'):
                    default = self.env.config.get('ticket',
                                                  'default_' + field['name'], None)
                else:
                    default = field.get('value')
                    options = field.get('options')
                    if default and default != '' and options and default not in options:
                        try:
                            default = options[int(default)]
                        except (ValueError, IndexError):
                            self.env.log.warning('Invalid default value "%s" '
                                                 'for custom field "%s"'
                                                 % (default, field['name']))
                if default or default == '':
                    self.values.setdefault(field['name'], default)
    
        def is_modified(self):
            return self._old

    return PatchedTicketClass(*args, **argv)
