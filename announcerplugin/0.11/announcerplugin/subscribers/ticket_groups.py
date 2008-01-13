from trac.core import Component, implements
from announcerplugin.api import IAnnouncementSubscriber, IAnnouncementPreferenceProvider, istrue
from trac.ticket import model
from trac.web.chrome import add_warning
from trac.config import ListOption
import re

class JoinableGroupSubscriber(Component):
    implements(IAnnouncementSubscriber, IAnnouncementPreferenceProvider)
    
    joinable_groups = ListOption('announcer', 'joinable_groups', [], 
        doc="""Joinable groups represent 'opt-in' groups that users may 
        freely join. The name of the groups should be a simple alphanumeric 
        string. By adding the group name preceeded by @ (such as @sec for
        the sec group) to the CC field of a ticket, everyone in that group
        will receive an announcement when that ticket is changed.""")
    
    def get_subscription_realms(self):
        return ('ticket',)
    
    def get_subscription_categories(self, *args):
        return ('changed', 'created', 'attachment added')
    
    def get_subscriptions_for_event(self, event):
        if event.realm == 'ticket':
            if event.category in ('changed', 'created', 'attachment added'):
                cc = event.target['cc']
                for chunk in re.split('\s|,', cc):
                    chunk = chunk.strip()
                    if chunk.startswith('@'):
                        member = None
                        for member in self._get_membership(chunk[1:]):
                            self.log.debug("JoinableGroupSubscriber added '%s' because of opt-in to group: %s" % (member[1], chunk[1:]))
                            yield member
                        
                        if member is None:
                            self.log.debug("JoinableGroupSubscriber found no members for group: %s." % chunk[1:])
                            
    def _get_membership(self, group):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT sid 
              FROM session_attribute
             WHERE authenticated=1
               AND name=%s
               AND value=%s
        """, ('announcer_joinable_group_' + group, "1"))
        
        for result in cursor.fetchall():
            yield ("email", result[0], None)

    def get_announcement_preference_boxes(self, req):
        if self.joinable_groups:
            yield "joinable_groups", "Joinable Groups (Opt-In)"
        return

    def render_announcement_preference_box(self, req, panel):
        cfg = self.config
        sess = req.session
                
        if req.method == "POST":
            for group in self.joinable_groups:
                group_opt = 'joinable_group_%s' % group
                result = req.args.get(group_opt, None)
                if result:
                    sess["announcer_" + group_opt] = '1'
                else:
                    if group_opt in sess:
                        del sess["announcer_" + group_opt]

        groups = {}
        for group in self.joinable_groups:
            groups[group] = sess.get('announcer_joinable_group_%s' % group, None)

        data = dict(
            joinable_groups = groups
        )

        return "prefs_announcer_joinable_groups.html", data
