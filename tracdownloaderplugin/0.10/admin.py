# -*- coding: utf-8 -*-
#
# Author: Petr Škoda <pecast_cz@seznam.cz>
# All rights reserved.
#
# This software is licensed under GNU GPL. You can read  it at
# http://www.gnu.org/licenses/gpl-3.0.html
#

import email
import inspect
import os
import locale
import re
import shutil
import sys
import math
import urllib

from trac import ticket, __version__ as TRAC_VERSION
from trac.core import *
from trac.perm import IPermissionRequestor
from trac import util
from trac.util import Markup
from trac.web.chrome import add_stylesheet, ITemplateProvider, add_link
from trac.web.href import Href
from webadmin.web_ui import IAdminPageProvider
from tracdownloader.model import *
from tracdownloader import form_data
from string import *
                            
try:
    import pkg_resources
except ImportError:
    pkg_resources = None

def _find_base_path(path, module_name):
    base_path = os.path.splitext(path)[0]
    while base_path.replace(os.sep, '.').endswith(module_name):
        base_path = os.path.dirname(base_path)
        module_name = '.'.join(module_name.split('.')[:-1])
        if not module_name:
            break
    return base_path

TRAC_PATH = _find_base_path(sys.modules['trac.core'].__file__, 'trac.core')

# Ideally, this wouldn't be hard-coded like this
required_components = ('AboutModule', 'DefaultPermissionGroupProvider',
    'Environment', 'EnvironmentSetup', 'PermissionSystem', 'RequestDispatcher',
    'Mimeview', 'Chrome')


class DownloaderAdminPage(Component):

    implements(IPermissionRequestor, IAdminPageProvider, ITemplateProvider)
    
    # IPermissionRequestor method
    
    def get_permission_actions(self):
        """Return a list of actions defined by this component.
        
        The items in the list may either be simple strings, or
        `(string, sequence)` tuples. The latter are considered to be "meta
        permissions" that group several simple actions under one name for
        convenience.
        """
        return [('DOWNLOADER_ADMIN')]
        
    # ITemplateProvider methods (we are input another package than webadmin is)
        
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        raise TracError, resource_filename(__name__, 'htdocs')
        return [('downloader', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # IAdminPageProvider methods

    def get_admin_pages(self, req):
        if req.perm.has_permission('DOWNLOADER_ADMIN'):
            yield ('general', 'General', 'downloader', 'Downloader')

    def process_admin_request(self, req, cat, page, path_info):
        req.perm.assert_permission('DOWNLOADER_ADMIN')
        
        self.cat = cat
        self.page = page
        
        self.config
        
        # Defaults for config in this module
        config_defaults(self, self.env)
        
        # Context navigation
        cntx_nav = CntxNav(self.env.href.admin(cat, page))
        cntx_nav.add('files', 'Files Admin')
        cntx_nav.add('stats', 'Stats Admin')
        cntx_nav.add('settings', 'Settings')
        
        # Parse path_info
        if path_info:
            match = re.match(
                '(?:([^/]+))?(?:/([^/]+))?(?:/([^/]+))?(?:/(.*)$)?', path_info)
            if match:
                req.args['page_part'] = match.group(1)
                req.args['sel_type'] = match.group(2)
                req.args['page'] = match.group(2)
                req.args['get_2'] = match.group(2)
                req.args['sel_id'] = match.group(3)
                req.args['get_3'] = match.group(3)
                req.args['get_4'] = match.group(4)
        else:
            req.args['page_part'] = 'files'
            req.args['page'] = 1
        
        # Downloader file directory check
        file_directory_check(self.env, req, self.config)
        
        self.run_info = []  # Currently unused
        self.run_err = []   # Currently unused
        
        # Decide what part of downloader admin to run, default is Files Admin
        if req.args['page_part'] == 'stats':
            template = self._serve_stats_admin(req)
        elif req.args['page_part'] == 'settings':
            template = self._serve_settings_admin(req)
        else:
            template = self._serve_files_admin(req)
        
        
        # Write infos and errors to output
        if self.run_info:
            req.hdf['run_info'] = self.run_info
        if self.run_err:
            req.hdf['run_err'] = self.run_err
        
        # Set switch that we are in admin area for list of files
        req.hdf['in_adm'] = True
        
        req.hdf['title'] = 'Manage Downloads'
        
        # Context navigation render
        cntx_nav.render(req)
        
        # Downloader stylesheet
        add_stylesheet(req, 'downloader/css/downloader.css')
        
        # Set base href to downloader plug-in
        req.hdf['href.base'] = self.env.href.admin(cat, page, \
            req.args['page_part'])
        req.hdf['href.full'] = self.env.href.admin(cat, page, \
            req.args['page_part'], req.args['page'])
        req.hdf['page_part'] = req.args['page_part']
        
        return template

    # Internal methods
    
    def _serve_files_admin(self, req):
        """Renders Files Admin page"""
        
        # Selected item input file list - maybe changed before render
        self.selected = self._get_selected(req)
        
        if req.method == 'POST' and req.args.has_key('form_type'):
            if req.args['form_type'] == 'category':
                self._serve_category(req)
            elif req.args['form_type'] == 'release':
                self._serve_release(req)
            elif req.args['form_type'] == 'file':
                self._serve_file(req)
        
        render_downloads_table(self.env, req)
        self._render_forms(req)
        
        return 'admin_downloader.cs', None
    
    def _serve_stats_admin(self, req):
        """Renders Stats Admin page"""
        
        # List of names used as GET method attrbutes for use with 
        # self.get_method_string() which returns string to href of GET method. 
        self.get_attrs = ['order', 'desc']
        
        # Manage parameters eventually in POST method
        if req.method == 'POST':
            if req.args.has_key('per_page'):
                if re.match(r'\w*[0-9]+\w*', req.args['per_page']):
                    self.config.set('downloader', 'stats_per_page', 
                                     req.args['per_page'])
                    self.config.save()
            if req.args.has_key('delete'):
                self._render_stats_delete(req, True)
            if req.args.has_key('navigate_back') and \
                    req.args.has_key('redirect_back'):
                req.redirect(req.args['redirect_back'])
            if req.args.has_key('del_range_submit'):
                self._stats_delete_range(req)
                
        
        # Get order parameters from GET, default order is by timestamp
        if req.args.has_key('order'):
            self.order = req.args['order']
        else:
            self.order = 'timestamp'
        if req.args.has_key('desc'):
            self.desc = True
        else:
            self.desc = False
            
        if req.args['get_3'] == 'really_delete':
            template = self._render_stats_delete(req)
        elif req.args['get_3'] == 'show':
            template = self._render_stats_show(req)
        else:
            template = self._render_stats_table(req)
        
        return template
    
    def _serve_settings_admin(self, req):
        """Gets settings from config file and saves them from form after edit"""
        
        req.hdf['cap_work'] = cap_work
        
        if req.method == 'POST':
            if req.args.has_key('no_quest'):
                val = 'true'
            else:
                val = 'false'
            self.config.set('downloader', 'no_quest', val)
            
            if req.args.has_key('form_only_first_time'):
                val = 'true'
            else:
                val = 'false'
            self.config.set('downloader', 'form_only_first_time', val)
            
            if req.args.has_key('provide_link'):
                val = 'true'
            else:
                val = 'false'
            self.config.set('downloader', 'provide_link', val)
            
            if req.args.has_key('no_captcha'):
                val = 'true'
            else:
                val = 'false'
            self.config.set('downloader', 'no_captcha', val)
            
            if req.args.has_key('captcha_num_of_letters'):
                try:
                    val = int(req.args['captcha_num_of_letters'])
                    self.config.set('downloader', 'captcha_num_of_letters', \
                                    str(val))
                except ValueError:
                    raise TracError, \
                        'Invalid numeric value ("%s") for Number of letters.'%\
                        req.args['captcha_num_of_letters']
            
            if req.args.has_key('captcha_font_size'):
                try:
                    val = int(req.args['captcha_font_size'])
                    self.config.set('downloader', 'captcha_font_size', \
                                    str(val))
                except ValueError:
                    raise TracError, \
                        'Invalid numeric value ("%s") for Font size.'%\
                        req.args['captcha_font_size']
                        
            if req.args.has_key('captcha_font_size'):
                try:
                    val = int(req.args['captcha_font_border'])
                    self.config.set('downloader', 'captcha_font_border', \
                                    str(val))
                except ValueError:
                    raise TracError, \
                        'Invalid numeric value ("%s") for Font border.'%\
                        req.args['captcha_font_border']
                        
            if req.args.has_key('captcha_hardness'):
                val = req.args['captcha_hardness']
                self.config.set('downloader', 'captcha_hardness', \
                                val)
                
            if req.args.has_key('files_dir'):
                val = req.args['files_dir']
                self.config.set('downloader', 'files_dir', \
                                val)
            
            self.config.save()
        
        req.hdf['no_quest'] = int(self.config.getbool('downloader', 'no_quest'))
        req.hdf['form_only_first_time'] = \
                int(self.config.getbool('downloader', 'form_only_first_time'))
        req.hdf['provide_link'] = \
                int(self.config.getbool('downloader', 'provide_link'))
        req.hdf['no_captcha'] = int(self.config.getbool('downloader', 'no_captcha'))
        req.hdf['captcha_num_of_letters'] = \
                self.config.get('downloader', 'captcha_num_of_letters')
        req.hdf['captcha_font_size'] = \
                self.config.get('downloader', 'captcha_font_size')
        req.hdf['captcha_font_border'] = \
                self.config.get('downloader', 'captcha_font_border')
        
        req.hdf['captcha_hardness_list'] = ['normal', 'hard']
        req.hdf['captcha_hardness'] = \
                self.config.get('downloader', 'captcha_hardness')
        req.hdf['files_dir'] = \
                self.config.get('downloader', 'files_dir')
        
        return 'admin_settings.cs', None
    
    def _render_stats_table_head(self, req):
        """
        Renders heading of list of downloads and 
        saves list into self.stats_head.
        """
        head = [
                ['id', 'Id:'], 
                ['file_name', 'File name:', 1], 
                ['timestamp', 'Timestamp:', 1]
               ]
        # Get list of labels for attributes
        labels = DownloadData.get_label_list()
        for lab in labels:
            if lab[2]:
                head.append([lab[0], lab[1], 1])
        
        head.append(['actions', 'Actions:'])
        
        self.stats_head = head
        req.hdf['stats.head'] = head
    
    def _render_stats_table(self, req):
        """Renders whole stats table (gets all its data)."""
        ## Head
        self._render_stats_table_head(req)
        
        ## Body
        # Get list of downloads according to sort and page
        per_page = self.config.get('downloader', 'stats_per_page')
        try:
            per_page = int(per_page)
        except ValueError:
            self.config.remove('downloader', 'stats_per_page')
            per_page = int(self.config.get('downloader', 'stats_per_page'))
            
        req.hdf['stats.per_page'] = per_page
        
        if not req.args['page']:
            page = 1
        else:
            try:
                page = int(req.args['page'])
            except ValueError:
                page = 1
            
        # Render all setting
        if req.args.has_key('renderall'):
            page = 1
            per_page = None
        
        # Fetch list of donwnloads
        rec_count, downloads = DownloadData.fetch_downloads_list(
            self.env, 
            req, 
            self.order,
            self.desc,
            per_page,
            page)
        
        rows = []
        for dwn in downloads:
            file = File(self.env, dwn.file_id)
            act_show_href = self.env.href.admin(
                                    self.cat, 
                                    self.page, 
                                    req.args['page_part'],
                                    page,
                                    'show',
                                    dwn.id)
            act_show = util.Markup('<a href="%s">show</a>' % (act_show_href \
                       + self.get_method_string(req)))
            act_del_href = self.env.href.admin(
                                    self.cat, 
                                    self.page, 
                                    req.args['page_part'],
                                    page,
                                    'really_delete',
                                    dwn.id)
            act_del = util.Markup('<a href="%s">delete</a>' % (act_del_href \
                      + self.get_method_string(req)))
            row = {
                   'id': dwn.id,
                   'timestamp': util.format_datetime(dwn.timestamp),
                   'file_id': dwn.file_id,
                   'file_name': file.name_disp,
                   'actions': act_show + util.Markup(' | ') + act_del
                   }
            for key, attr in dwn.attr.iteritems():
                row[key] = attr
            rows.append(row)
        req.hdf['stats.rows'] = rows
        
        # Render in other formats
        if req.args.has_key('format'):
            format = req.args['format']
            if format == 'csv':
                return self._render_stats_table_special(req, 
                                        self.stats_head, rows)
            if format == 'tab':
                return self._render_stats_table_special(req, 
                                        self.stats_head, rows, "\t", '')
    
        # List of pges
        page_cnt = math.ceil(rec_count * 1.0 / per_page)
        pg_lst = []
        for num in range(1, page_cnt + 1):
            href = self.env.href.admin(
                                 self.cat, 
                                 self.page, 
                                 req.args['page_part'],
                                 str(num)
                                 )
            href += self.get_method_string(req)
            pg_lst.append([href, num])
        req.hdf['stats.pg_lst'] = pg_lst
        req.hdf['stats.pg_act'] = page
        
        # Links to alternative formats of this table
        self.add_alternate_links(req)
        
        # Order in table head
        req.hdf['stats.order'] = self.order
        if self.desc:
            req.hdf['stats.desc'] = 1
            
        req.hdf['datetime_hint'] = util.get_datetime_format_hint()
            
        return 'admin_downloader_stats.cs', None
    
    def _render_stats_table_special(self, req, head, rows, delim=';', quot='"', \
                                    ):
        # Head
        head_l = []
        for it in head:
            if it[0] == 'actions':
                    continue;
            head_l.append(quot + it[1] + quot)
            
        rows_l = []
        rows_l.append(join(head_l, delim))
        # Rows
        for row in rows:
            row_l = []
            for it in head:
                if it[0] == 'actions':
                    continue;
                if not row.has_key(it[0]):
                    row[it[0]] = ''
                row_l.append(quot + 
                          unicode(row[it[0]]).replace('&#8203;', '') + quot)
            rows_l.append(join(row_l, delim))
        
        data = join(rows_l, "\n")
        req.hdf['data.text'] = data
        return 'admin_show_text.cs', None
    
    def _render_stats_show(self, req):
        href_back = self.env.href.admin(
                                        self.cat, 
                                        self.page, 
                                        req.args['page_part'],
                                        req.args['page']
                                        )
        href_back = href_back + self.get_method_string(req)
        
        if not req.args['get_4']:
            req.redirect(href_back)
        id = int(req.args['get_4'])
        try:
            dwnl = DownloadData(self.env, req, id=id)
        except TracError:
            req.redirect(href_back)
        
        req.hdf['dwn_record.redir'] = href_back
        req.hdf['dwn_record.items'] = dwnl.get_attr_list()
        
        return 'admin_downloader_stats_show.cs', None
    
    def _render_stats_delete(self, req, delete=False):
        href_back = self.env.href.admin(
                                        self.cat, 
                                        self.page, 
                                        req.args['page_part'],
                                        req.args['page']
                                        )
        if not req.args['get_4']:
            req.redirect(href_back)
        id = int(req.args['get_4'])
        try:
            dwnl = DownloadData(self.env, req, id=id)
        except TracError:
            req.redirect(href_back)
        try:
            file = File(self.env, dwnl.file_id)
        except TracError:
            file.name = 'id=' + str(dwnl.file_id)
            
        if not delete:
            req.hdf['dwn_record.redir'] = \
                    href_back + self.get_method_string(req)
            req.hdf['dwn_record.id'] = dwnl.id
            req.hdf['dwn_record.file'] = file.name
            req.hdf['dwn_record.timest'] = util.format_datetime(dwnl.timestamp)
            
            req.hdf['dwn_record.items'] = dwnl.get_attr_list()
                
            return 'admin_downloader_stats_really_delete.cs', None
        else:
            dwnl.delete()
            if req.args.has_key('redirect_back'):
                req.redirect(req.args['redirect_back'])
            else:
                req.redirect(href_back)
                
    def _stats_delete_range(self, req):
        if not req.args.has_key('start') or not req.args.has_key('end'):
            return False
        
        start = int(util.parse_date(req.args['start']))
        end = int(util.parse_date(req.args['end']))
        
        if DownloadData.delete_range(self.env, start, end):
            self.env.log.info("Deleted records from " + \
                               req.args['start'] + \
                               " to " + req.args['end'] + ".")
        
    def _render_forms(self, req):
        
        if not os.access(tracdownloader.model.downloader_dir, os.F_OK + os.W_OK):
            req.hdf['files_dir.readonly'] = True
        
        req.hdf['selected'] = self.selected
    
    def _get_selected(self, req):
        selected = None
        if req.args.has_key('sel_type'):
            selected = [req.args['sel_type'], req.args['sel_id']]
            
        return selected
    
    def _serve_category(self, req):
        if req.args.has_key('edit_id'):
            category = Category(self.env, id=req.args['edit_id'])
        else:
            category = Category(self.env)
        
        # Delete operation
        if req.args.has_key('delete'):
            self.selected = None
            category.delete()
            return
        
        category.name = req.args['name']
        category.sort = req.args['sort']
        category.notes = req.args['notes']
        
        category.save()
        self.selected = ['category', category.id]
    
    def _serve_release(self, req):
        if req.args.has_key('edit_id'):
            release = Release(self.env, id=req.args['edit_id'])
            self.selected = ['release', req.args['edit_id']]
        elif req.args.has_key('super_id'):
            release = Release(self.env)
            release.category = req.args['super_id']
            self.selected = ['category', release.category]
        else:
            self.run_err.append("Wrong form data, nothing changed.")
            return
        
        # Delete operation
        if req.args.has_key('delete'):
            self.selected = ['category', release.category]
            release.delete()
            return
        
        release.name = req.args['name']
        release.sort = req.args['sort']
        release.notes = req.args['notes']
        
        release.save()
        
    def _serve_file(self, req):
        """Server file - create, edit or delete."""
            
        if req.args.has_key('edit_id'):
            file = File(self.env, id=req.args['edit_id'])
            self.selected = ['file', req.args['edit_id']]
        elif req.args.has_key('super_id'):
            
            upload = req.args['file_to_upload']
            if not upload.filename:
                raise TracError, 'No file uploaded'
            if hasattr(upload.file, 'fileno'):
                size = os.fstat(upload.file.fileno())[6]
            else:
                size = upload.file.len
            if size == 0:
                raise TracError, 'No file uploaded'
            
            file = File(self.env)
            file.release = req.args['super_id']
            file.fileobj = upload.file
            self.selected = ['release', file.release]
        else:
            self.run_err.append("Wrong form data, nothing changed.")
            return
        
        # Delete operation
        if req.args.has_key('delete'):
            self.selected = ['release', file.release]
            file.delete()
            return
        
        file.name = req.args['name']
        file.sort = req.args['sort']
        file.architecture = req.args['architecture']
        file.notes = req.args['notes']
        
        file.save()
        
    def add_alternate_links(self, req):
        """
        Adds to the bottom of the page links to alternative formats of
        displayed document. It takes care of getting GET aruments correctly
        using method self.get_method_string()
        """
        params = self.get_method_string(req)
        if strip(params) == '':
            params = '?'
        href = params
        add_link(req, 'alternate', href + '&format=csv',
                 'Excel .csv - this view', 'text/plain')
        add_link(req, 'alternate', href + '&format=csv&renderall=true',
                 'Excel .csv - all', 'text/plain')
        add_link(req, 'alternate', href + '&format=tab',
                 'Tab-delimited Text - this view', 'text/plain')
        add_link(req, 'alternate', href + '&format=tab&renderall=true',
                 'Tab-delimited Text - all', 'text/plain')
        
        
    def get_method_string(self, req, get_attrs=None):
        """
        Gets string to use in url like getattr attributes which
        contains all attributes actually given by GET method
        listed in self.get_attrs
        """
        if not hasattr(self, 'get_attrs') and not get_attrs:
            return ''
        
        if hasattr(self, 'get_attrs'):
            get_attrs = self.get_attrs
        
        lst = []
        for item in get_attrs:
            if req.args.has_key(item):
                lst.append(str(item) + '=' + str(req.args[item]))
        
        if len(lst):
            return util.Markup('?' + join(lst, "&"))
        else:
            return ''
            
    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('downloader', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
