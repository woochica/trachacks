
from trac.core import *
from trac.perm import PermissionSystem

from trac.util import sorted
from trac.config import Option
from webadmin.web_ui import IAdminPageProvider

from model import *
from io import *
from acct_mgr.api import AccountManager
from trac.web.chrome import ITemplateProvider

from urllib import pathname2url, url2pathname

import types
import inspect

# Mode constants
EDIT_NORMAL=0
EDIT_GROUP=1
EDIT_PATH=2


class SvnAuthzAdminPage(Component):

    implements(IAdminPageProvider, ITemplateProvider)

    def __init__(self):
        self.authz_file = self.env.config.get("trac", "authz_file")
        self.authz_module = self.env.config.get("trac", "authz_module_name")
        if self.authz_module != None and self.authz_module.strip() == "":
            self.authz_module = None
        self.account_manager = AccountManager(self.env)

    # IAdminPageProvider
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('subversion', 'Subversion', 'svnauthz', 'Subversion Access')

    def process_admin_request(self, req, cat, page, path_info):
        perm = PermissionSystem(self.env)
        self.env.log.debug("SvnAuthzAdminPlugin: cat=%s page=%s path_info=%s"
                           % (cat, page, path_info))
        self.authz = self._get_model();
        if req.method == 'POST':
           if req.args.get('addgroup'):
               self._add_group(req)
           elif req.args.get('addpath'):
               self._add_path(req)
           elif req.args.get('addgroupmember'):
               self._add_group_member(req)
           elif req.args.get('removegroupmembers'):
               self._del_group_member(req)
           elif req.args.get('removegroups'):
               self._del_groups(req)
           elif req.args.get('removepaths'):
               self._del_paths(req)
           elif req.args.get('addpathmember'):
               self._add_path_member(req)
           elif req.args.get('changepathmembers'):
               self._change_path_members(req)
        
        # Handle group and path edit mode handling
        editgroup = None
        editpath = None               
        if path_info and path_info.startswith("editgroup/"):
            editgroup = self._edit_group(req, cat, page, path_info)
        elif path_info and path_info.startswith("editpath/"):
            editpath = self._edit_path(req, cat, page, path_info)

        paths_disp = []
        for repository, path in [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]:
            if repository != self.authz_module:
                # We ignore the paths from other modules from the display 
                continue
            path_disp = self._get_disp_path_name(repository, path)
            path_disp_url = pathname2url("%s:%s" % (repository, path))
            if editpath and editpath == path_disp_url:
                path_disp_href = req.href.admin('subversion', 'svnauthz')
            else:
                path_disp_href = req.href.admin('subversion', 'svnauthz', 'editpath')
                path_disp_href += "/" + path_disp_url                              
            paths_disp.append({ 'name' : path_disp,
                                'url' : path_disp_url,
                                'href': path_disp_href
                                })
        req.hdf['paths'] = sorted(paths_disp)
        
        groups_disp = []
        for group_disp in sorted([g.get_name() for g in self.authz.get_groups()]):
            group_disp_url = pathname2url(group_disp)
            if editgroup and editgroup == group_disp_url:
                group_disp_href = req.href.admin('subversion', 'svnauthz')
            else:
                group_disp_href = req.href.admin('subversion', 'svnauthz', 'editgroup',
                                              group_disp_url)
                
            groups_disp.append({ 'name': group_disp,
                                 'url': group_disp_url,
                                 'href': group_disp_href
                                })
        req.hdf['groups'] = groups_disp

        self._persist_model(self.authz)

        return 'admin_authz.cs', None
 
    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def _add_group(self, req):
        groupname = req.args.get('groupname')
        try:
            self.authz.add_group(Group(groupname, []))
        except Exception, e:
            req.hdf['addgroup.error'] = e
        
    def _del_groups(self, req):
        groups_to_del = req.args.get('selgroup')
        try:
            if isinstance(groups_to_del,types.StringTypes):
                self.authz.del_group(url2pathname(groups_to_del))
            elif isinstance(groups_to_del,types.ListType):
                for group in groups_to_del:
                    self.authz.del_group(url2pathname(group))
            else:
                req.hdf['delgroup.error'] = "Invalid type of group selection"    
        except Exception, e:
            req.hdf['delgroup.error'] = e
    
    def _del_paths(self, req):
        paths_to_del = req.args.get('selpath')
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        try:
            if isinstance(paths_to_del,types.StringTypes):
                paths_to_del = [paths_to_del]
            for urlpath in paths_to_del:
                validpath = self._get_valid_path(paths, url2pathname(urlpath))
                if validpath:
                    self.authz.del_path(validpath[1], self.authz_module)
        except Exception, e:
            req.hdf['delpath.error'] = e

    
    def _add_path(self, req):
        path = req.args.get('path')
        repository = None
        try:
            self.authz.add_path(Path(path, [], self.authz_module))
        except Exception, e:
            req.hdf['addpath.error'] = e

    def _add_group_member(self, req):
        editgroup = url2pathname(req.args.get('editgroup'))
        subject = req.args.get('subject')
        group = self.authz.find_group(editgroup)
        if (group == None):
            req.hdf['addgroupmember.error'] = "Group %s does not exist" % editgroup
            return
        try:
            member = self._get_member(subject)
            assert (member != None)
            group.append(member)
        except Exception, e:
            req.hdf['addgroupmember.error'] = e

    def _add_path_member(self, req):
        editpath = url2pathname(req.args.get('editpath'))
        subject = req.args.get('subject')
        acls = req.args.get('addpathmember_acl')
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if not validpath:
            req.hdf['changepathmember.error'] = "Not a valid path: %s" % editpath
            return
        path = validpath[1]        
        path_members = self.authz.find_path(path, self.authz_module)
        
        read = False
        write = False     
        if isinstance(acls, types.ListType):
            for i in acls:
                if i == "R":
                    read = True
                elif i == "W":
                    write = True
        
        elif isinstance(acls, types.StringTypes):
                if acls == "R":
                    read = True
                elif acls == "W":
                    write = True
        try:
            s = self._get_member(subject)
            assert (s != None)
            path_members.append(PathAcl(s, read, write))
        except Exception, e:
            req.hdf['addpathmember.error'] = e

    
    def _del_group_member(self, req):
        editgroup = url2pathname(req.args.get('editgroup'))
        members_to_del = req.args.get('selgroupmember')
        group = self.authz.find_group(editgroup)
        if not group:
            req.hdf['delgroupmember.error'] = "Group %s does not exist" % editgroup
            return        
        try:
            if isinstance(members_to_del, types.StringTypes):
                group.remove(self._get_member(members_to_del))
            elif isinstance(members_to_del, types.ListType):
                for member in members_to_del:
                    group.remove(self._get_member(member))
            else:
                req.hdf['delgroupmember.error'] = "Wrong type of selection"
        except Exception, e:
            req.hdf['delgroupmember.error'] = e

    def _change_path_members(self, req):
        editpath = url2pathname(req.args.get('editpath'))
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if not validpath:
            req.hdf['changepathmember.error'] = "Not a valid path: %s" % editpath
            return
        path = validpath[1]
        members_to_del = req.args.get('selpathmember')
        member_acls = req.args.get('selpathmember_acl')
        path_members = self.authz.find_path(path, self.authz_module)
        
        if len(path_members) == 0:
            # Nothing to do
            return
        
        try:
            if members_to_del != None:
                if isinstance(members_to_del, types.StringTypes):
                    members_to_del = [members_to_del]
                if not isinstance(members_to_del, types.ListType):
                    req.hdf['changepathmember.error'] = "Wrong type of member selection"
                    return
                for member in members_to_del:
                    path_members.remove(path_members.find_path_member(self._get_member(member)))
        except Exception, e:
            req.hdf['changepathmember.error'] = e
            return
        
        if member_acls == None:
            member_acls = ""
        
        if isinstance(member_acls, types.StringTypes):
            # A single acl was set, special handling
            member_acls = [member_acls]

        try:
            for member in path_members:
                read = False
                write = False
                if "%s_R" % member.get_member() in member_acls:
                    read = True
                if "%s_W" % member.get_member() in member_acls:
                    write = True
                if (read, write) != (member.is_read(), member.is_write()):
                    member.set_read(read)
                    member.set_write(write)
        except Exception, e:
            req.hdf['changepathmember.error'] = e
    
    def _edit_group(self, req, cat, page, path_info):
        """
            Populates the editgroup.* parts of the hdf
            @return the value of editgroup.url or None
        """
        editgroup = url2pathname(path_info[path_info.index('/')+1:len(path_info)])            
        group = self.authz.find_group(editgroup)
        if group != None:
            req.hdf['editgroup.name'] = editgroup
            req.hdf['editgroup.url'] = pathname2url(editgroup)
            req.hdf['editgroup.members'] = [m.__str__() for m in group]
            
            # Populate member candidates
            not_in_list = [m.__str__() for m in group]
            not_in_list.append("@%s" % editgroup)
            candidates = self._get_candidate_subjects(not_in_list)
            if candidates != []:
                req.hdf['editgroup.candidates'] = candidates
            return req.hdf['editgroup.url']
        return None

    def _get_candidate_subjects(self, not_in_list = []):
        candidates = []
        users = [user for user in self.account_manager.get_users() 
                 if user not in not_in_list]
        candidates += sorted(users)
        candidates += sorted([group.__str__() for group in self.authz.get_groups() 
                              if group.__str__() not in not_in_list])
        self.env.log.debug("Candidates:")
        for c in candidates:
            self.env.log.debug("   %s" % c)             
        return candidates
    
    def _edit_path(self, req, cat, page, path_info):
        """
            Populates the editpath.* parts of the hdf
            @return the value of editgroup.url or None
        """
        editpath = url2pathname(path_info[path_info.index('/')+1:len(path_info)])            
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if validpath:
            req.hdf['editpath.name'] = self._get_disp_path_name(validpath[0], validpath[1])
            req.hdf['editpath.url'] = pathname2url(editpath)
            pathmembers = self.authz.find_path(validpath[1], validpath[0])
            editpath_members = []
            for member in pathmembers:
                read = write = ""
                if member.is_read():
                    read = "checked"
                if member.is_write():
                    write = "checked"
                
                editpath_members.append({'subject' : member.get_member().__str__(),
                                         'read' : read,
                                         'write' : write})
            req.hdf['editpath.members'] = editpath_members 
            
            # Populate member candidates
            not_in_list = [m.get_member().__str__() for m in pathmembers]
            candidates = self._get_candidate_subjects(not_in_list)
            if candidates != []:
                req.hdf['editpath.candidates'] = candidates
            return req.hdf['editpath.url']
        return None

    def _get_valid_path(self, pathlist, path):
        for repository, pathname in pathlist:
            if "%s:%s" % (repository, pathname) == path:
                return (repository, pathname)
        return None
    
    def _get_disp_path_name(self, repository, path):
        return path

    def _get_model(self):
       r = AuthzFileReader()
       return r.read(self.authz_file)

    def _persist_model(self, m):
       w = AuthzFileWriter()
       w.write(self.authz_file, m)

    def _get_member(self, id, creategroup=False):
        if id.startswith("@"):
            g = self.authz.find_group(id.lstrip("@"))
            if not g and creategroup:
                return Group(id.lstrip("@"), [])
            else:
                return g
        else:
            return User(id)
