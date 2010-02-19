from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.util import Markup
import trac.ticket.web_ui as web
from trac.web.chrome import add_link, add_script, add_stylesheet, \
                            add_warning, add_ctxtnav, prevnext_nav, Chrome, \
                            INavigationContributor, ITemplateProvider
from trac.util.translation import _
from trac.versioncontrol.diff import get_diff_options, diff_blocks
from genshi.template import TemplateLoader

def get_diffs(self, req, title, old_text, new_text):
    diff_style, diff_options, diff_data = get_diff_options(req)
    diff_context = 3
    for option in diff_options:
        if option.startswith('-U'):
            diff_context = int(option[2:])
            break
    if diff_context < 0:
        diff_context = None
    diffs = diff_blocks(old_text.splitlines(), new_text.splitlines(), context=diff_context,
                        tabwidth=2,
                        ignore_blank_lines=True,
                        ignore_case=True,
                        ignore_space_changes=True)
    
    chrome = Chrome(self.env)
    loader = TemplateLoader(chrome.get_all_templates_dirs())
    tmpl = loader.load('diff_div.html')
    
    changes=[{'diffs': diffs, 'props': [],
              'title': title,
              'new': {'path':"", 'rev':'', 'shortrev': '', 'href':''},
              'old': {'path':"", 'rev':'', 'shortrev': '', 'href': ''}}]

    data = chrome.populate_data(req,
                                { 'changes':changes , 'no_id':True, 'diff':diff_data,
                                  'longcol': '', 'shortcol': ''})
    diff_data['style']='sidebyside';
    data.update({ 'changes':changes , 'no_id':True, 'diff':diff_data,
                  'longcol': '', 'shortcol': ''})
    stream = tmpl.generate(**data)
    return stream.render()



def _validate_ticket(self, req, ticket):
    valid = True
    resource = ticket.resource

    # If the ticket has been changed, check the proper permission
    if ticket.exists and ticket._old:
        if 'TICKET_CHGPROP' not in req.perm(resource):
            add_warning(req, _("No permission to change ticket fields."))
            ticket.values.update(ticket._old)
            valid = False
        else: # TODO: field based checking
            if ('description' in ticket._old and \
                   'TICKET_EDIT_DESCRIPTION' not in req.perm(resource)) or \
               ('reporter' in ticket._old and \
                   'TICKET_ADMIN' not in req.perm(resource)):
                add_warning(req, _("No permissions to change ticket "
                                   "fields."))
                ticket.values.update(ticket._old)
                valid = False

    comment = req.args.get('comment')
    if comment:
        if not ('TICKET_CHGPROP' in req.perm(resource) or \
                'TICKET_APPEND' in req.perm(resource)):
            add_warning(req, _("No permissions to add a comment."))
            valid = False

###############################################################################


    # Mid air collision?
    if ticket.exists and (ticket._old or comment):
        skey = "warning-"+req.args['id']+'-'+req.args.get('ts')
        if req.args.get('ts') != str(ticket.time_changed) and not req.session.has_key(skey):
            req.session[skey] = True;
            add_warning(req, _("This ticket has been modified by someone else since you started."
                          " If you are sure your change doesnt break theirs, you can go ahead and save again."))

            changes, problems = self.get_ticket_changes(req, ticket, req.args.get('action'))
            if changes.has_key('description'):
                #req.session[skey] = False;
                diff = get_diffs(self, req, "Description Changed", 
                                 changes['description']['old'],
                                 changes['description']['new'])

                #strip unicode till I can figure out how to get markup to work with it
                diff = Markup(''.join([i for i in diff if ord(i) <128]))

                add_stylesheet(req, 'common/css/diff.css')
                add_warning(req, "Description Changed!")
                add_warning(req, diff);
            valid = False

        elif req.session.has_key(skey):
            del(req.session[skey])

###############################################################################

    # Always require a summary
    if not ticket['summary']:
        add_warning(req, _('Tickets must contain a summary.'))
        valid = False
        
    # Always validate for known values
    for field in ticket.fields:
        if 'options' not in field:
            continue
        if field['name'] == 'status':
            continue
        name = field['name']
        if name in ticket.values and name in ticket._old:
            value = ticket[name]
            if value:
                if value not in field['options']:
                    add_warning(req, '"%s" is not a valid value for '
                                'the %s field.' % (value, name))
                    valid = False
            elif not field.get('optional', False):
                add_warning(req, 'field %s must be set' % name)
                valid = False

    # Validate description length
    if len(ticket['description'] or '') > self.max_description_size:
        add_warning(req, _('Ticket description is too long (must be less '
                      'than %(num)s characters)',
                      num=self.max_description_size))
        valid = False

    # Validate comment length
    if len(comment or '') > self.max_comment_size:
        add_warning(req, _('Ticket comment is too long (must be less '
                           'than %(num)s characters)',
                           num=self.max_comment_size))
        valid = False

    # Validate comment numbering
    try:
        # comment index must be a number
        int(req.args.get('cnum') or 0)
        # replyto must be 'description' or a number
        replyto = req.args.get('replyto')
        if replyto != 'description':
            int(replyto or 0)
    except ValueError:
        # Shouldn't happen in "normal" circumstances, hence not a warning
        raise InvalidTicket(_('Invalid comment threading identifier'))

    # Custom validation rules
    for manipulator in self.ticket_manipulators:
        for field, message in manipulator.validate_ticket(req, ticket):
            valid = False
            if field:
                add_warning(req, _("The ticket field '%(field)s' is "
                              "invalid: %(message)s",
                              field=field, message=message))
            else:
                add_warning(req, message)
    return valid


class OverrideEditPluginSetupParticipant(Component):
    """ This component monkey patches web.TicketModule._validate_ticket so that
        you can still edit even when someone else has added a comment.
        If you are not careful you can overrite ticket description changes, the
        plugin attempts to show a diff if there are changes.
    """
    implements(IEnvironmentSetupParticipant)
    def __init__(self):
      #only if we should be enabled do we monkey patch
      if self.compmgr.enabled[self.__class__]:
        web.TicketModule._validate_ticket = _validate_ticket

    def environment_created(self):
      """Called when a new Trac environment is created."""
      pass

    def environment_needs_upgrade(self, db):
      """Called when Trac checks whether the environment needs to be upgraded.
      
      Should return `True` if this participant needs an upgrade to be
      performed, `False` otherwise.
      
      """
      pass

    def upgrade_environment(self, db):
      """Actually perform an environment upgrade.

      Implementations of this method should not commit any database
      transactions. This is done implicitly after all participants have
      performed the upgrades they need without an error being raised.
      """
      pass

