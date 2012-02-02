# -*- coding: utf-8 -*-
#
# Author: Petr Škoda <pecast_cz@seznam.cz>
# All rights reserved.
#
# This software is licensed under GNU GPL. You can read  it at
# http://www.gnu.org/licenses/gpl-3.0.html
#

import re
import os
import calendar
import time
import datetime

from string import *
from genshi.builder import tag
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util import Markup
from trac.util.translation import _
from trac.wiki.api import IWikiSyntaxProvider
from trac.web import IRequestHandler
from trac.web.chrome import add_stylesheet, INavigationContributor, \
                            ITemplateProvider
from trac.web.href import Href
from tracdownloader.model import *

class DownloaderModule(Component):
    
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler, 
               ITemplateProvider, IWikiSyntaxProvider)
    
    # IPermissionRequestor method
    
    def get_permission_actions(self):
        """Return a list of actions defined by this component.
        
        The items in the list may either be simple strings, or
        `(string, sequence)` tuples. The latter are considered to be "meta
        permissions" that group several simple actions under one name for
        convenience.
        """
        return ['DOWNLOADER_DOWNLOAD', 'DOWNLOADER_STATS']
        
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'downloader'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DOWNLOADER_DOWNLOAD'):
            yield 'mainnav', 'downloader', tag.a(_('Downloader'), href=req.href.downloader())

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match( \
            '/downloader(?:/([^/]+))?(?:/([^/]+))?' + \
            '(?:/([^/]+))?(?:/([^/]+))?(?:/([^/]+))?(?:/(.*)$)?', \
            req.path_info)
        if match:
            req.args['arg_1'] = match.group(1)
            self.arg_1 = match.group(1)
            req.args['arg_2'] = match.group(2)
            self.arg_2 = match.group(2)
            req.args['arg_3'] = match.group(3)
            self.arg_3 = match.group(3)
            req.args['arg_4'] = match.group(4)
            self.arg_4 = match.group(4)
            req.args['arg_5'] = match.group(5)
            self.arg_5 = match.group(5)
            req.args['arg_6'] = match.group(6)
            self.arg_6 = match.group(6)
            return True
    '''
    def _get_pages(self, req):
        """Return a list of available admin pages."""
        pages = ['notes', 'getfile', 'form']
        pages.sort()
        return pages
    '''

    def process_request(self, req):
        # Defaults for config of this Class
        config_defaults(self, self.env)
        
        req.hdf['title'] = 'Downloader'
        
        self.match_request(req)
        
        # Downloader file directory check
        file_directory_check(self.env, req, self.config)
        
        # Default page
        if not req.args.get('arg_1'):
            req.args['arg_1'] = 'download'
            self.arg_1 = 'download'
        
        # Context navigation
        cntx_nav = CntxNav(self.env.href.downloader())
        cntx_nav.add('download', 'Downloads')
        if req.perm.has_permission('DOWNLOADER_STATS'):
            cntx_nav.add('time_stats', 'Time stats')
            cntx_nav.add('file_stats', 'File stats')
            cntx_nav.add('release_stats', 'Release stats')
            cntx_nav.add('category_stats', 'Category stats')
        
        req.hdf['page_part'] = req.args.get('arg_1')
        
        output = None
        # Switch part of page
        if self.arg_1 == 'download':
            output = self._render_downloads(req)
        elif self.arg_1 == 'captcha':
            output = self._serve_captcha(req, self.arg_2)
        elif self.arg_1 == 'time_stats':
            output = self._render_daily_stats(req, self.arg_2, self.arg_3)
        elif self.arg_1 == 'file_stats':
            output = self._render_filtered_stats(req, 'file')
        elif self.arg_1 == 'release_stats':
            output = self._render_filtered_stats(req, 'release')
        elif self.arg_1 == 'category_stats':
            output = self._render_filtered_stats(req, 'category')
        
        # Set base href to downloader plug-in
        req.hdf['href.base'] = self.env.href.downloader(self.arg_1)
        
        # Context navigation render
        cntx_nav.render(req)
        
        if output == None:
            raise TracError, "No handler matched request to /%s ." % self.arg_1
        
        add_stylesheet(req, 'downloader/css/downloader.css')
        return output
    
    # Internal methods
    
    def _render_filtered_stats(self, req, filter):
        """Renders stats about choosen part of downloads data."""
        year = None
        month = None
        # Daily stats for element
        if self.arg_2 and self.arg_3 and self.arg_3 == 'daily':
            # If arg_2, is not number redirect back
            try:
                self.arg_2 = int(self.arg_2)
            except ValueError:
                req.redirect(self.env.href.downloader(self.arg_1))
            
            element = None
            if filter == 'file':
                element = File(self.env, self.arg_2)
                el_name = element.name_disp
            elif filter == 'release':
                element = Release(self.env, self.arg_2)
                el_name = element.name
            elif filter == 'category':
                element = Category(self.env, self.arg_2)
                el_name = element.name
            
            if not element or not element.timestamp:
                req.redirect(self.env.href.downloader(self.arg_1))
                return None
            
            year = self.arg_4
            month = self.arg_5
            
            output = self._render_daily_stats(req, year, month, \
                filter=filter, filter_id=self.arg_2)
            req.hdf['href.daily.base'] = self.env.href.downloader(self.arg_1,
                                                                  self.arg_2,
                                                                  self.arg_3)
            req.hdf['filter.title'] = Markup(filter + ' "' + el_name + '" ')
            return output
        # Monthly category data
        elif self.arg_2:
            # If arg_2, is not number redirect back
            try:
                self.arg_2 = int(self.arg_2)
            except ValueError:
                req.redirect(self.env.href.downloader(self.arg_1))
                
            year = self.arg_2
            if self.arg_3:
                try:
                    self.arg_3 = int(self.arg_3)
                    month = self.arg_3
                except ValueError:
                    month = None
        
        req.hdf['filter.title'] = filter + ' '
        # Display review of filtered elements
        return self._render_element_review(req, filter, year=year, month=month)
        
    def _render_daily_stats(self, req, year, month, \
                            filter=None, filter_id=None):
        req.perm.assert_permission('DOWNLOADER_STATS')
        
        # Get range of years and months with relevant data
        start, end = DownloadData.fetch_downloads_list(self.env, \
                                                       get_range=True, \
                                                       filter=filter, \
                                                       filter_id=filter_id)
        if not start or not end:
            start = time.time()
            end = time.time()
            
        if not year:
            if start:
                year = time.strftime("%Y", time.localtime(start))
            else: # Case where no data input DB
                year = time.strftime("%Y", time.time())
            if not month:
                month = None
        if not month:
            month = None
            #month = int(time.strftime("%m", time.localtime(start)))
        
        req.hdf['stats.year'] = year
        req.hdf['stats.month'] = month
        
        # Get list of months and years
        years, months = moths_in_range(start, end, self.env)
        req.hdf['stats.years'] = years
        req.hdf['stats.months'] = months
        
        maxh = 270
        if month:
            graph_data = self._create_month_stat(int(year), int(month), 
                maxh=maxh, filter=filter, filter_id=filter_id)
        else:
            graph_data = self._create_year_stat(int(year), 
                maxh=maxh, filter=filter, filter_id=filter_id)
        req.hdf['stats.graph'] = graph_data
        req.hdf['stats.graph_height'] = maxh
        
        req.hdf['href.daily.base'] = self.env.href.downloader(self.arg_1)
        
        return 'daily_s.cs', None
    
    def _create_year_stat(self, year, maxh=200, \
                           filter=None, filter_id=None):
        
        months = range(1, 13)
        months_val = []
        maximum = 0
        for month in months:
            start = int(time.mktime(datetime.datetime(year, month, 1).\
                        timetuple()))
            _, days = calendar.monthrange(year, month)
            end = int(time.mktime(datetime.datetime(year, month, days,\
                      23, 59, 59, 99).timetuple()))
            
            count = DownloadData.fetch_downloads_list( \
                             self.env, range=(start, end), count=True, 
                             filter=filter, filter_id=filter_id)
            if count > maximum:
                maximum = count
            month = "%02d" % month
            months_val.append([month, count])
            
        # Count height from count and maxh (maximal height)
        # Count posistion of label with avoidance of collision to another text.
        if float(maximum):
            piece = float(maxh) / float(maximum)
        else:
            piece = 0
            
        last_h = -10    # elevation of last label
        em = 15         # font height
        em_c = 12       # font collision height
        for key, item in enumerate(months_val):
            height = float(item[1]) * piece
            # Label position
            if not ((key + 1) % 3):
                lab_h = height + 35
            elif not ((key + 2) % 3):
                lab_h = height + 37
            elif not (key % 3):
                lab_h = height + 39
            
            count = "%d" % item[1]
            # Collisions of labels - moves collising label up or down of last
            # Collisong label is the one longer than 3 number on same height
            # as left neighbour
            if len(count) > 3:
                if abs(last_h - lab_h) < em_c:
                    lab_h = last_h + em
            last_h = lab_h
            months_val[key] = [item[0], count, height, lab_h]
        
        return months_val
    
    def _create_month_stat(self, year, month, maxh=200, \
                           filter=None, filter_id=None):
        _, days = calendar.monthrange(year, month)
        
        days_val = []
        maximum = 0
        for day in range(1, days + 1):
            start = int(time.mktime(datetime.datetime(year, month, day).\
                        timetuple()))
            end = start + 86399 # whole day
            
            count = DownloadData.fetch_downloads_list( \
                             self.env, range=(start, end), count=True, 
                             filter=filter, filter_id=filter_id)
            if count > maximum:
                maximum = count
            day = "%02d" % day
            days_val.append([day, count])
            
        # Count height from count and maxh (maximal height)
        # Count posistion of label with avoidance of collision to another text.
        if float(maximum):
            piece = float(maxh) / float(maximum)
        else:
            piece = 0
            
        last_h = -10    # elevation of last label
        em = 15         # font height
        em_c = 12       # font collision height
        for key, item in enumerate(days_val):
            height = float(item[1]) * piece
            # Label position
            if not ((key + 1) % 3):
                lab_h = height + 35
            elif not ((key + 2) % 3):
                lab_h = height + 37
            elif not (key % 3):
                lab_h = height + 39
            
            count = "%d" % item[1]
            # Collisions of labels - moves collising label up or down of last
            # Collisong label is the one longer than 3 number on same height
            # as left neighbour
            if len(count) > 3:
                if abs(last_h - lab_h) < em_c:
                    lab_h = last_h + em
            last_h = lab_h
            days_val[key] = [item[0], count, height, lab_h]
        
        return days_val
    
    def _render_element_review(self, req, filter, filter_id=None, \
                               year=None, month=None):
        req.perm.assert_permission('DOWNLOADER_STATS')
        
        # Render list of availible years and months 
        self._render_month_year_range(req, year, month, filter, filter_id)
        
        # Count start and end
        if year:
            if month:
                start = int(time.mktime(datetime.datetime(year, month, 1).\
                            timetuple()))
                _, days = calendar.monthrange(year, month)
                end = int(time.mktime(datetime.datetime(year, month, days,\
                          23, 59, 59, 99).timetuple()))
            else:
                start = int(time.mktime(datetime.datetime(year, 1, 1).\
                            timetuple()))
                end = int(time.mktime(datetime.datetime(year + 1, 1, 1).\
                            timetuple()))
            range = (start, end)
        else:
            range = None
        
        elements = None
        if filter == 'file':
            elements = File.get_files(self.env, range)
        elif filter == 'release':
            elements = Release.get_releases(self.env, range)
        elif filter == 'category':
            _, elements = Categories(self.env).get_categories(range=range)
        
        maximum = 0
        graph_data = []
        for el in elements:
            count = DownloadData.fetch_downloads_list( \
                             self.env, count=True, range=range,\
                             filter=filter, filter_id=el.id)
            if count > maximum:
                maximum = count
            # For file use name for display
            if hasattr(el, 'name_disp'):
                name = el.name_disp
            else:
                name = el.name
            graph_data.append([name, count, el.id])
            
        # Count and add size of graph cell
        max_cell_len = 100 # Use percents for horizontal size
        if maximum:
            piece = float(max_cell_len) / float(maximum)
        else:
            piece = 0
        for key, item in enumerate(graph_data):
            size = piece * float(item[1])
            name = Markup(item[0])
            # Firefox and Opera percent width hack
            if size > 0:
                size_str = '%.03f%%' % size
            else:
                size_str = '0'
            count_str = '%d' % item[1]
            graph_data[key] = [name, count_str, size_str, item[2]]
        
        req.hdf['stats.graph'] = graph_data
        #req.hdf['href.daily.base'] = self.env.href.downloader(self.arg_1)
        
        return 'filtered_s.cs', None
    
    def _render_month_year_range(self, req, year=None, month=None, \
                                 filter=None, id=None):
        """
        Renders list of years and months to choose and returns actually
        displayed year and month if given.
        """
        # Get range of years and months with relevant data
        start, end = DownloadData.fetch_downloads_list(self.env, \
                                                       get_range=True)
        if not year:
            year = None
            #year = time.strftime("%Y", time.localtime(start))
            if not month:
                month = None
        if not month:
            month = None
            #month = int(time.strftime("%m", time.localtime(start)))
        
        req.hdf['stats.year'] = year
        req.hdf['stats.month'] = month
        
        # Get list of months and years
        years, months = moths_in_range(start, end, self.env)
        req.hdf['stats.years'] = years
        req.hdf['stats.months'] = months
    
    def _render_downloads(self, req):
        req.perm.assert_permission('DOWNLOADER_DOWNLOAD')
        
        # Some preset to session
        if not req.session.get('downloader_files'):
            req.session['downloader_files'] = ''
            req.session.save()
        #self.env.log.info("Files: " + req.session.get('downloader_files'))
        
        filter = None
        f_id = None
        if req.args.get('arg_2'):
            arg_1 = req.args.get('arg_1')
            arg_2 = req.args.get('arg_2')
            arg_3 = req.args.get('arg_3')
            arg_4 = req.args.get('arg_4')
            arg_5 = req.args.get('arg_5')
            arg_6 = req.args.get('arg_6')
            if arg_2 == 'notes' and arg_3 and arg_4 != '':
                self._render_note(req, arg_3, arg_4)
            elif arg_2 == 'file' and arg_3 != '':
                href_base = self.env.href.downloader(arg_1,
                                                     arg_2)
                if self._serve_file(req, arg_3, arg_4, href_base):
                    return None
            elif arg_2 == 'release' or arg_2 == 'category' and arg_3 != '':
                try:
                    f_id = int(arg_3)
                    filter = arg_2
                except ValueError:
                    pass
                req.hdf['href.filter'] = '/' + arg_2 + '/' + arg_3
                if arg_4 == 'file' and arg_5 != '':
                    href_base = self.env.href.downloader(arg_1,
                                                         arg_2,
                                                         arg_3,
                                                         arg_4)
                    
                    if self._serve_file(req, arg_5, arg_6, href_base):
                        return None
                elif arg_4 == 'notes' and arg_5 and arg_6 != '':
                    self._render_note(req, arg_5, arg_6)
        else:
            # Test if session works
            req.session['downloader_test'] = 'test'
            req.session.save()
        
        render_downloads_table(self.env, req, filter=filter, f_id=f_id)
        
        return 'downloader.cs', None
    
    def _serve_file(self, req, id, file_name, href_base):
        """
        Workarounds and decisions about what to do when file is clicked.
        * Just serves file like real link if no_quest = true is in config.
        * First serve questionaire, then check it and eventually serve file.
            (takes care of Captcha if installed and no_captcha = false)
        * Cares about straight serving any file after first form fill up if 
            form_only_first_time = true
        """
        conf = self.config
        file = File(self.env, id)
        # Redirect to address with filename at the end
        if file_name == '' or file_name == None:
            req.redirect(href_base + '/' + str(id) + '/' + file.name)
            return False
        
        # Serve questionnaire if wanted
        if not conf.getbool('downloader', 'no_quest'):
            self.quest = DownloadData(self.env, req, conf, id)
            self.quest.read_data()
            
            # Try to fill unfilled form from session
            if self.quest.unfilled:
                self.quest.load_from_session()
            
            if (self.quest.unfilled or self.quest.errors) \
            and not self._check_file_in_session(req, id):
                req.hdf['quest'] = self.quest.schema
                if not self.quest.unfilled:
                    req.hdf['quest.errors'] = self.quest.errors
                
                # Captcha
                if not conf.getbool('downloader', 'no_captcha', 'false') and \
                        cap_work:
                    my_cap = MyCaptcha(self.env)
                    cap = my_cap.new()
                    req.hdf['quest.captcha_id'] = cap.id
                    req.hdf['quest.captcha_adr'] = my_cap.href
                return False
            
            # Serve link to file
            elif conf.getbool('downloader', 'provide_link', 'true') \
                    and not self.quest.unfilled:
                if not self._serve_link(req, conf, file_name, file):
                    return False
            
            # Save file if not using link after questionnaire
            if not self._check_file_in_session(req, file.id):
                req.session['downloader_files'] += ',' + str(file.id)
                self.quest.save_to_session()
                self.quest.insert_data()
        else:
            self.quest = DownloadData(self.env, req, conf, file_id=file.id)
            self.quest.insert_data()
        
        # Get file
        file.serve_file(req)
        return True
    
    def _serve_captcha(self, req, id):
        """Easily gets captcha picture to user"""
        captcha = MyCaptcha(self.env).get(id)
        
        req.send_response(200)
        req.send_header('Content-Type', 'image/jpeg')
        req.end_headers()
        captcha.render((100, 50)).save(req, "JPEG")
    
    def _serve_link(self, req, conf, file_name, file):
        """
        Serve to hdf set variables for final download link.
        Returns False if file has not to be served directly.
        """
        # Cannot serve link to people without session
        if req.session.get('downloader_test') \
        and not self._check_file_in_session(req, file.id):
            req.session['downloader_files'] += ',' + str(file.id)
            self.quest.save_to_session()
            self.quest.insert_data()
            
            req.hdf['download_link'] = \
                self.env.href.downloader(self.arg_1, 'file', file.id, file_name)
            req.hdf['download_name'] = file.name
            if conf.getbool('downloader', \
                                   'form_only_first_time', 'false'):
                req.hdf['form_only_first_time'] = True
            return False
        else:
            return True
    
    def _check_file_in_session(self, req, id):
        """
        Checks if file id is saved in session -
        allowed to download... Or checks if form was
        already filled if mode is form_only_first_time(True, False)
        """        
        if not req.session.get('downloader_files'):
            return False
        
        files = req.session.get('downloader_files')
        
        # Selected to get form only for first download.
        if self.config.getbool('downloader', 'form_only_first_time', 'false'):
            if strip(files) == '':
                return False
            else:
                return True
        
        # Check if the file number is in list
        files = split(files, ',')
        if str(id) in files:
            return True
        
        return False
    
    def _render_note(self, req, type, id):
        try:
            if type == 'category':
                elem = Category(self.env, id)
            if type == 'release':
                elem = Release(self.env, id)
            if type == 'file':
                elem = File(self.env, id)
        
            req.hdf['notes'] = True
            req.hdf['notes.for'] = type + " \"" + elem.name + "\":"
            req.hdf['notes.text'] = split(elem.notes, "\n")
        except TypeError:
            raise TracError('Unknown ' + type + ' id ' + "'" + id + "'.")
            
    def _format_wiki_link(self, formatter, ns, target, label):
        # Config defaults must be set
        config_defaults(self, self.env)
        
        if ns == 'downloader':
            what = 'file'
            try:
                obj = File(self.env, int(target))
            except TracError, ValueError:
                obj = None
        elif ns == 'downloaderrel':
            what = 'release'
            try:
                obj = Release(self.env, int(target))
            except TracError, ValueError:
                obj = None
        elif ns == 'downloadercat':
            try:
                obj = Category(self.env, int(target))
            except TracError, ValueError:
                obj = None
            what = 'category'
            
        try:
            # Try to use fancier code for Trac 10
            from trac.util.html import html
            return self._format_wiki_link_10(formatter, ns, target, label, obj,
                                             what)
        except ImportError:
            return self._format_wiki_link_09(formatter, ns, target, label, obj,
                                             what)
    
    def _format_wiki_link_10(self, formatter, ns, target, label, obj, what):
        from trac.util.html import html
        
        if not obj:
            return html.A(label, rel='nofollow', href='#', 
                          title = '%s with this id not found.' %\
                          capitalize(what))
            
        name = obj.name
        if label == ns + ':' + target:
            label = name
            
        if obj.deleted:
            return html.A(label, rel='nofollow', href='#', 
                          title='Sorry, %s was deleted.' % what)
        
        href = formatter.href.downloader('download', what, target, name)
        return html.A(label, href=href)
    
    def _format_wiki_link_09(self, formatter, ns, target, label, obj, what):
        if not obj:
            return ('<a href="%s" rel="%s" title="%s">%s</a>' % \
                   ('#', 'nofollow',  \
                    '%s with this id not found.' % capitalize(what), label))
            
        name = obj.name
        if label == ns + ':' + target:
            label = name
            
        if obj.deleted:
            return ('<a href="%s" rel="%s" title="%s">%s</a>' % \
                   ('#', 'nofollow',  \
                   'Sorry, %s was deleted.' % what, label))
        
        href = formatter.href.downloader('download', what, target, name)
        return ('<a href="%s">%s</a>' % (href, label))
    
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
        

    # IWikiSyntaxProvider methods
    
    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        return [('downloader', self._format_wiki_link),
                ('downloaderrel', self._format_wiki_link),
                ('downloadercat', self._format_wiki_link)]
                

