import pkg_resources
from trac.core import *
from trac.perm import PermissionSystem

from trac.util import sorted
from trac.config import BoolOption
from trac.admin.api import IAdminPanelProvider

from model import *
from io import *
from trac.web.chrome import ITemplateProvider

from trac.versioncontrol import RepositoryManager

from urllib import pathname2url, url2pathname

import types
import inspect

# Mode constants
EDIT_NORMAL=0
EDIT_GROUP=1
EDIT_PATH=2


class SvnAuthzAdminPage(Component):
    implements(IAdminPanelProvider, ITemplateProvider)

    show_all_repos = BoolOption(
        'svnauthzadmin', 'show_all_repos', False,
        """Enabling this option will allow the Trac project to view
        the entire contents of the SVN trac|authz_file.""")
    read_only_display = BoolOption(
        'svnauthzadmin', 'read_only_display', False,
        """Enabling this option will prevent the Trac project from
        changing the contents of the SVN trac|authz_file.""")

    def __init__(self):
        self.authz_file = self.config.get("trac", "authz_file")

        # Retrieve info for all repositories associated with this project
        rm = RepositoryManager(self.env)
        all_repos = rm.get_all_repositories()
        self.project_repos = []
        for (reponame, info) in all_repos.iteritems():
            self.project_repos.append(reponame)
        self.env.log.debug("SvnAuthzAdminPlugin: project_repos: '%s'" % self.project_repos)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('svnauthz', 'templates')]

    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('versioncontrol', 'Version Control', 'svnauthz', 'Subversion Access')

    def render_admin_panel(self, req, cat, page, path_info):
        data = {}
        perm = PermissionSystem(self.env)
        self.env.log.debug("SvnAuthzAdminPlugin: cat=%s page=%s path_info=%s"
                           % (cat, page, path_info))
        self.authz = self._get_model();
        if req.method == 'POST':
           if req.args.get('addgroup'):
               data.update(self._add_group(req))
           elif req.args.get('addpath'):
               data.update(self._add_path(req))
           elif req.args.get('addgroupmember'):
               data.update(self._add_group_member(req))
           elif req.args.get('removegroupmembers'):
               data.update(self._del_group_member(req))
           elif req.args.get('removegroups'):
               data.update(self._del_groups(req))
           elif req.args.get('removepaths'):
               data.update(self._del_paths(req))
           elif req.args.get('addpathmember'):
               data.update(self._add_path_member(req))
           elif req.args.get('changepathmembers'):
               data.update(self._change_path_members(req))
        
        # Handle group and path edit mode handling
        editgroup = None
        editpath = None               
        if path_info and path_info.startswith("editgroup/"):
            editgroup, d = self._edit_group(req, cat, page, path_info)
	    data.update(d)
        elif path_info and path_info.startswith("editpath/"):
            editpath, d = self._edit_path(req, cat, page, path_info)
	    data.update(d)

        paths_disp = []
        for repository, path in [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]:
            if not self.show_all_repos and repository not in self.project_repos:
                # We eliminate repos associated with other Trac projects
                # unless show_all_repos is true
                continue
            path_disp = self._get_disp_path_name(repository, path)
            path_disp_url = pathname2url(path_disp)
            if editpath and editpath == path_disp_url:
                path_disp_href = req.href.admin('versioncontrol', 'svnauthz')
            else:
                path_disp_href = req.href.admin('versioncontrol', 'svnauthz', 'editpath')
                path_disp_href += "/" + path_disp_url                              
            paths_disp.append({ 'name' : path_disp,
                                'url' : path_disp_url,
                                'href': path_disp_href
                                })
        data['paths'] = sorted(paths_disp, key=lambda path : path['href'].lower())
        self.env.log.debug("SvnAuthzAdminPlugin: paths: '%s'" % data['paths'])
        
        groups_disp = []
        for group_disp in sorted([g.get_name() for g in self.authz.get_groups()]):
            group_disp_url = pathname2url(group_disp)
            if editgroup and editgroup == group_disp_url:
                group_disp_href = req.href.admin('versioncontrol', 'svnauthz')
            else:
                group_disp_href = req.href.admin('versioncontrol', 'svnauthz', 'editgroup',
                                              group_disp_url)
                
            groups_disp.append({ 'name': group_disp,
                                 'url': group_disp_url,
                                 'href': group_disp_href
                                })
        data['groups'] = sorted(groups_disp, key=lambda path : path['href'].lower())
        self.env.log.debug("SvnAuthzAdminPlugin: groups: '%s'" % data['groups'])

        data['read_only_display'] = self.read_only_display

        self._persist_model(self.authz)

        return 'admin_authz.html',data 
 
    def _add_group(self, req):
        groupname = req.args.get('groupname')
        try:
            self.authz.add_group(Group(groupname, []))
	    return {}
        except Exception, e:
            return {'addgroup_error' : e}
        
    def _del_groups(self, req):
        groups_to_del = req.args.get('selgroup')
        try:
            if isinstance(groups_to_del,types.StringTypes):
                self.authz.del_group(url2pathname(groups_to_del))
            elif isinstance(groups_to_del,types.ListType):
                for group in groups_to_del:
                    self.authz.del_group(url2pathname(group))
            else:
                return {'delgroup_error' : "Invalid type of group selection"} 
        except Exception, e:
            return {'delgroup_error' : e }
	return {}
    
    def _del_paths(self, req):
        paths_to_del = req.args.get('selpath')
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        try:
            if isinstance(paths_to_del,types.StringTypes):
                paths_to_del = [paths_to_del]
            for urlpath in paths_to_del:
                validpath = self._get_valid_path(paths, url2pathname(urlpath))
                if validpath:
                    self.authz.del_path(validpath[1], validpath[0])
        except Exception, e:
            return {'delpath_error' : e }

        return {} 
    def _add_path(self, req):
        path = req.args.get('path')
        repository = None
        tmppath = req.args.get('path') 
 	if ":" in tmppath: 
 	    repository, path = tmppath.split(":") 
 	    repository = repository.strip() 
 	    path = path.strip() 
 	else: 
 	    repository = self.project_repos[0]
 	    path = tmppath.strip() 
        try:
            self.authz.add_path(Path(path, [], repository))
	    return {}
        except Exception, e:
            return {'addpath_error' :  e}

    def _add_group_member(self, req):
        editgroup = url2pathname(req.args.get('editgroup'))
        subject = req.args.get('subject')
        if subject == '':
            subject = req.args.get('subject2')
        if subject == '':
            return {'addgroupmember_error': "No member specified" }
        group = self.authz.find_group(editgroup)
        if (group == None):
            return {'addgroupmember_error': "Group %s does not exist" % editgroup }
        try:
            member = self._get_member(subject)
            assert (member != None)
            group.append(member)
        except Exception, e:
            return {'addgroupmember_error':e} 
	return {}

    def _add_path_member(self, req):
        editpath = url2pathname(req.args.get('editpath'))
        subject = req.args.get('subject')
        if subject == '':
            subject = req.args.get('subject2')
        if subject == '':
            return {'addpathmember_error': "No member specified" }
        acls = req.args.get('addpathmember_acl')
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if not validpath:
            return {'changepathmember_error' : "Not a valid path: %s" % editpath}
        path = validpath[1]
        repo = validpath[0]
        path_members = self.authz.find_path(path, repo)
        
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
            return {'addpathmember_error' : e }
	return {}

    
    def _del_group_member(self, req):
        editgroup = url2pathname(req.args.get('editgroup'))
        members_to_del = req.args.get('selgroupmember')
        group = self.authz.find_group(editgroup)
        if not group:
            return {'delgroupmember_error': "Group %s does not exist" % editgroup }
        try:
            if isinstance(members_to_del, types.StringTypes):
                group.remove(self._get_member(members_to_del))
            elif isinstance(members_to_del, types.ListType):
                for member in members_to_del:
                    group.remove(self._get_member(member))
            else:
                return {'delgroupmember_error': "Wrong type of selection" }
        except Exception, e:
            return {'delgroupmember_error': e}

	return {}

    def _change_path_members(self, req):
        editpath = url2pathname(req.args.get('editpath'))
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if not validpath:
            return {'changepathmember_error' : "Not a valid path: %s" % editpath }
        path = validpath[1]
        repo = validpath[0] 
        members_to_del = req.args.get('selpathmember')
        member_acls = req.args.get('selpathmember_acl')
        path_members = self.authz.find_path(path, repo)
        
        if len(path_members) == 0:
            # Nothing to do
            return {}
        
        try:
            if members_to_del != None:
                if isinstance(members_to_del, types.StringTypes):
                    members_to_del = [members_to_del]
                if not isinstance(members_to_del, types.ListType):
                    return {'changepathmember_error':  "Wrong type of member selection"}
                for member in members_to_del:
                    path_members.remove(path_members.find_path_member(self._get_member(member)))
        except Exception, e:
            return {'changepathmember_error': e}
        
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
            return {'changepathmember_error':e}
	return {}
    
    def _edit_group(self, req, cat, page, path_info):
        """
            Populates the editgroup.* parts of the hdf
            @return the value of editgroup.url or None
        """
	data = {}
        editgroup = url2pathname(path_info[path_info.index('/')+1:len(path_info)])            
        group = self.authz.find_group(editgroup)
        if group != None:
            data['editgroup_name'] = editgroup
            data['editgroup_url'] = pathname2url(editgroup)
            data['editgroup_members'] = sorted([m.__str__() for m in group], key=lambda member : member.lower())
            
            # Populate member candidates
            not_in_list = [m.__str__() for m in group]
            not_in_list.append("@%s" % editgroup)
            candidates = self._get_candidate_subjects(not_in_list)
            if candidates != []:
                data['editgroup_candidates'] = candidates
            return data['editgroup_url'], data
	self.env.log.debug("SvnAuthzAdminPlugin: Group %s not found." % editgroup)
        return None, {} 

    def _get_all_users(self):
      """
      Fetches all users/groups from PermissionSystem
      """
      perm = PermissionSystem(self.env)
      users = ["*"]
      data = perm.get_all_permissions()
      if not data:
        return [] # we abort here

      for (subject, action) in data:
        if subject not in users and subject not in ["anonymous", "authenticated"]:
          users.append(subject)
      return users	

    def _get_candidate_subjects(self, not_in_list = []):
        candidates = ['']
        users = [user for user in self._get_all_users() 
                 if user not in not_in_list]
        candidates += sorted(users)
        candidates += sorted([group.__str__() for group in self.authz.get_groups() 
                              if group.__str__() not in not_in_list])
        #self.env.log.debug("Candidates:")
        #for c in candidates:
        #    self.env.log.debug("   %s" % c)             
        return candidates
    
    def _edit_path(self, req, cat, page, path_info):
        """
            Populates the editpath.* parts of the hdf
            @return the value of editgroup.url or None
        """
	data = {}
        editpath = url2pathname(path_info[path_info.index('/')+1:len(path_info)])            
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if validpath:
            data['editpath_name'] = editpath
            data['editpath_url'] = pathname2url(editpath)
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
            data['editpath_members'] = sorted(editpath_members, key=lambda member : member['subject'].lower())
            
            # Populate member candidates
            not_in_list = [m.get_member().__str__() for m in pathmembers]
            candidates = self._get_candidate_subjects(not_in_list)
            if candidates != []:
               data['editpath_candidates'] = candidates
            return data['editpath_url'], data
        return None, {} 

    def _get_valid_path(self, pathlist, path):
        for repository, pathname in pathlist:
            if self._get_disp_path_name(repository, pathname) == path:
                return (repository, pathname)
        return (None, path)
    
    def _get_disp_path_name(self, repository, path):
 	if repository == None: 
 	    return "*:%s" % path 
 	else: 
 	    return "%s:%s" % (repository, path) 

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
