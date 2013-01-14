from trac.core import Component, implements, TracError
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer

# R.Wobst, @(#) Jan 11 2013, 17:50:43
#
# New plugin based on Condfield-Patch for BlackmagicPlugin
# (http://www.trac-hacks.org/ticket/2486) which does not work for Trac 0.11 or
# later. Functionality is reduced to "cond_field" and extended by "default"
# entry:
#
# Configured fields are displayed only if the ticket type has/has not certain
# value(s).
#
# This plugin is based on Genshi, not on Javascript; can easily be extended. A
# detailed documentation can be found in condfieldsgenshi.txt.


class CondfieldTweaks(Component):
    implements(ITemplateStreamFilter)

    ## ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if filename != "ticket.html":
            return stream

        enchants = self.config.get('condfieldsgenshi', 'tweaks', '')

        ticket_type = None
        id = req.args.get('id')

        if id:
            # The ticket is already in data base, just show it.
            ticket = Ticket(self.env, id)

            # The ticket type must be defined - no check
            ticket_type = ticket['type']
        else:
            # new ticket or preview
            ticket = None

            # Check if the type is defined in the URL ...
            ticket_type = req.args.get('type')

            # ... otherwise it is a new ticket or a preview.
            if not ticket_type:
                # For preview, the internal field names are given in req.args,
                # and these are formed in trac/ticket/templates/ticket.html as
                # "field_${field.name}".
                # If this changes, this plugin must be changed, too!

                ticket_type = req.args.get('field_type')

                # It is a new ticket, no type given in URL, no preview, hence
                # put the default type here.
                if not ticket_type:
                    ticket_type = self.config.get('ticket', 'default_type')

        # Test if condfields shall be shown or hidden by default.
        default = self.config.get('condfieldsgenshi', 'default', '')
        if not default:
            default = 'enable'
        if default not in ('enable', 'disable'):
            raise TracError(("Error in trac.ini [condfieldsgenshi]: " +
                    "Illegal value '%s' " +
                    "for 'default' option - allowed: " +
                    "'enable', 'disable'\n") % default)
            return stream

        for field in (x.strip() for x in enchants.split(',')):
            # Check if it is a conditional field.
            # This part can be extended to dependence on other parameters
            # than "type".

            type_cond = self.config.get('condfieldsgenshi', field+'.type_cond', None)

            # old version:
            #if type_cond and \
            #        (
            #         (default == 'enable') ==
            #            (
            #             ticket_type in
            #                [x.strip() for x in type_cond.split(',')]
            #            )
            #        ):

            if not type_cond:
                continue

            neg = False
            if type_cond.startswith('!'):
                neg = True
                type_cond = type_cond[1:].strip()

            inlst = (ticket_type in [x.strip() for x in type_cond.split(',')])
            if neg:
                inlst = not inlst

            if (default == 'enable' and inlst) or \
                    (default == 'disable' and not inlst):

                if field != 'type':
                    stream = stream | Transformer(
                            '//th[@id="h_%s"]' % field).replace(" ")
                    stream = stream | Transformer(
                            '//td[@headers="h_%s"]' % field).replace(" ")
                    stream = stream | Transformer(
                            '//label[@for="field-%s"]' % field).replace(" ")
                    stream = stream | Transformer(
                            '//*[@id="field-%s"]' % field).replace(" ")
                else:
                    stream = stream | Transformer(
                            '//label[@for="field-type"]/text()'). \
                                    replace('Type (Fixed):')

                    stream = stream | Transformer(
                            '//*[@id="field-type"]/option').remove()
                    stream = stream | Transformer(
                            '//*[@id="field-type"]').append(ticket_type)
                    stream = stream | Transformer(
                            '//*[@id="field-type"]/text()').wrap('option')

        return stream

    ## ITemplateProvider

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return []
