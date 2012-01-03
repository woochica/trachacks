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
import iso8601

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

original_validate_ticket = web.TicketModule._validate_ticket

def _validate_ticket(self, req, ticket, force_collision_check=False):
    # Make sure mid air collisions dont trigger the underlying validation
    #if ticket.exists and (ticket._old or comment or force_collision_check):
    #  if req.args.get('ts') != str(ticket['changetime']):
    old_ticket_changetime = ticket['changetime']
    if not req.args.get('ts'):
        return original_validate_ticket(self, req, ticket, force_collision_check);
    comment = req.args.get('comment')
    try:
        ticket.values['changetime'] = iso8601.parse_date(req.args.get('ts'))
        valid = original_validate_ticket(self, req, ticket, force_collision_check)
        self.env.log.debug("Override edit plugin: original validation (without"
                           " midair collision check): %s, ts:%s, changetime:%s, collision?:%s /%r and (%r or %r) and %r != %r/ " % 
                           (valid, req.args.get('ts'),old_ticket_changetime,
                            ticket.exists and (ticket._old or comment) and
                            req.args.get('ts') != str(ticket['changetime']),
                            ticket.exists, ticket._old, comment,
                            req.args.get('ts'), str(ticket['changetime'])))
    finally:
        ticket.values['changetime'] = old_ticket_changetime

    # Avoidable mid air collision checks
    if ticket.exists and (ticket._old or comment) and req.args.get('id'):
        skey = "warning-"+req.args['id']+'-'+req.args.get('ts')
        if req.args.get('ts') != str(ticket['changetime']) and not req.session.has_key(skey):
            req.session[skey] = True;
            add_warning(req, _("This ticket has been modified by someone else since you started."
                               " If you are sure your change doesnt break theirs, you can go"
                               " ahead and save again."))

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


