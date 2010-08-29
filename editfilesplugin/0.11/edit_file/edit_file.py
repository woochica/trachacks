"""
"""
import os

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.admin.api import IAdminPanelProvider

CUT_OFF = 10

class TracEditPlugin(Component):
    """
    """
    implements(ITemplateProvider, IAdminPanelProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        """
        """
        if req.perm.has_permission('TRAC_ADMIN'):
            LST = self.config.get('edit_file', 'files').split(',')
            for item in LST:
                index = LST.index(item)
                ritem = None
                if len(item) > CUT_OFF:
                    ritem='.. ' + item.split(os.path.sep)[-1]
                else:
                    ritem = item
                yield ('EditFiles', 'EditFiles', 'file_'+str(index), ritem)

    def render_admin_panel(self, req, cat, page, path_info):
        """
        """
        assert req.perm.has_permission('TRAC_ADMIN')
        index = page.split('_')[-1]

        files = self.config.get('edit_file', 'files').split(',')
        index=int(index)

        edit_file = files[index]

        # check whether file exists and is writable
        if not os.access(edit_file, os.W_OK|os.R_OK):
            file_arg=('file' in req.args)
            if file_arg:
                edit_file = req.args['file']
                if not os.access(edit_file, os.W_OK|os.R_OK):
                    err = "In GET request, can't access edit_file parameter: " + str(edit_file)
                    raise TracError(err)
            else:
                err = "Can't access edit_file parameter: " + str(edit_file)
                raise TracError(err)

        #print '\n'*4,,cat,page,path_info
        # evaluate forms
        if req.method == 'POST':
            current=req.args.get('current').strip().replace('\r', '')

            # encode to utf-8
            current = current.encode('utf-8')

            # write to disk
            try:
                fp = open(edit_file, 'wb')
                current = fp.write(current)
                fp.close()
            except Exception, e:
                raise TracError("Can't write edit_file: %s" % e)

        # read current file
        current = ""
        try:
            fp = open(edit_file,'r')
            current = fp.read()
            fp.close()
        except:
            pass

        return 'edit_file.html', {'edit_file':edit_file,
                                 'file_data':current}


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        """
        return []

