# -*- coding: utf-8 -*-
#
# Author: Petr Škoda <pecast_cz@seznam.cz>
# All rights reserved.
#
# This software is licensed under GNU GPL. You can read  it at
# http://www.gnu.org/licenses/gpl-3.0.html
#

import os
import re
import random
import shutil
import time
import string
import locale
import tracdownloader.db

from string import *
from tracdownloader import form_data
from trac.core import *
from trac import util

try:
    """Captcha is included optionally"""
    import Captcha
    import Captcha.Visual
    import Captcha.Visual.Backgrounds
    import Captcha.Visual.Text
    import Captcha.Visual.Distortions
    from Captcha.Visual import ImageCaptcha
    cap_work = True
except ImportError:
    cap_work = False
    
'''import Captcha
import Captcha.Visual
import Captcha.Visual.Backgrounds
import Captcha.Visual.Text
import Captcha.Visual.Distortions
from Captcha.Visual import ImageCaptcha
cap_work = True'''

config = None
downloader_dir = None

def file_directory_check(env, req, config):
    """Downloader file directory check"""
    
    global downloader_dir
    downloader_dir = config.get('downloader', 'files_dir')
    if downloader_dir:
        downloader_dir = os.path.normpath(downloader_dir)
    if downloader_dir and not os.access(downloader_dir, os.F_OK + os.W_OK):
        downloader_dir = None
    if not downloader_dir and (not req.args.has_key('page_part') or \
            not req.args['page_part'].value == 'settings'):
        req.redirect(env.href.admin('general', 
                                    'downloader', 
                                    'settings'))
        return None
    if not downloader_dir and req.args.has_key('page_part') and \
            req.args['page_part'].value == 'settings':
        req.hdf['file_dir_not_set'] = 1
        
def config_defaults(config):
    config.setdefault('downloader', 'form_only_first_time', 'false')
    config.setdefault('downloader', 'no_quest', 'false')
    config.setdefault('downloader', 'no_captcha', 'false')
    config.setdefault('downloader', 'provide_link', 'true')
    config.setdefault('downloader', 'stats_per_page', 30)
    config.setdefault('downloader', 'captcha_font_size', 35)
    config.setdefault('downloader', 'captcha_font_border', 2)
    config.setdefault('downloader', 'captcha_num_of_letters', 4)
    config.setdefault('downloader', 'captcha_font_size', 35)
    config.setdefault('downloader', 'captcha_hardness', 'normal')
    
    
def moths_in_range(start, end, env=None):
    if not start:
        start = time.time()
    if not end:
        end = time.time()
    month_s = time.strftime("%m", time.localtime(start))
    month_e = time.strftime("%m", time.localtime(end))
    year_s = time.strftime("%Y", time.localtime(start))
    year_e = time.strftime("%Y", time.localtime(end))
    
    years = range(int(year_s), int(year_e) + 1)
    months = {}
    for year in years:
        if int(year) == int(year_s):
            start = int(month_s)
        else:
            start = 1
        if int(year) == int(year_e):
            end = int(month_e) + 1
        else:
            end = 13
        year_str = str(year)
        months[year_str] = []
        for mon in range(start, end):
            month_str = '%02d' % mon
            months[year_str].append(month_str)
    return years, months

def render_downloads_table(env, req):
    """Prepares data for table of downloads."""
    
    categories_d = {}
    releases_d = {}
    files_d = {}
    categories_obj, categories_list = Categories(env).list
    categories = []
    for category in categories_list:
        category_dict = {'id': category.id,
                         'name': category.name,
                         'notes': category.notes,
                         'sort': category.sort,
                         'timestamp': category.timestamp}
        # Format timestamp
        category_dict['timestamp'] = util.format_datetime(category_dict['timestamp'])
        
        releases_obj, releases_list = category.get_releases()
        releases = []
        for release in releases_list:
            release_dict = {'id': release.id,
                            'name': release.name,
                            'notes': release.notes,
                            'sort': release.sort,
                            'timestamp': release.timestamp}
            # Format timestamp
            release_dict['timestamp'] = util.format_datetime(release_dict['timestamp'])
            
            
            files_obj, files_list = release.get_files()
            files = []
            for file in files_list:
                file_dict = {'id': file.id,
                              'file': file.file,
                              'name': file.name,
                              'name_disp': file.name_disp,
                              'notes': file.notes,
                              'sort': file.sort,
                              'architecture': file.architecture,
                              'size': '',
                              'timestamp': file.timestamp}
                # Format timestamp
                file_dict['timestamp'] = \
                    util.format_datetime(file_dict['timestamp'])
                # Get filesize
                try:
                    size = os.path.getsize(file.file) / 1024.0
                    size = round(size, 2)
                except OSError:
                    env.log.warning("Cannot access file \"" + file.name +\
                                         "\".")
                    size = 0
                size = util.to_utf8(locale.format("%0.2f", size, True))
                file_dict['size'] = size
                
                files.append(file_dict)
                files_d[file_dict['id']] = file_dict
                
            release_dict['files'] = files
            releases.append(release_dict)
            releases_d[release_dict['id']] = release_dict
            
        category_dict['releases'] = releases
        categories.append(category_dict)
        categories_d[category_dict['id']] = category_dict
        
    req.hdf['categories_list'] = categories
    req.hdf['categories'] = categories_d
    req.hdf['releases'] = releases_d
    req.hdf['files'] = files_d
    

class CntxNav:
    """Context navigation at the top of the page content."""
    
    def __init__(self, base):
        self.cntx_nav = []
        self.base = base + "/"
    
    def add(self, href, text):
        """Stores cntx_nav link to later use in template."""
        self.cntx_nav.append([self.base + href, href, text])
    
    def render(self, req):
        """Writes cntx_nav to hdf set."""
        if self.cntx_nav:
            req.hdf['cntx_nav'] = self.cntx_nav

class Categories(object):
    """Contains dictionary of categories."""
    
    def __init__(self, env, db=None):
        self.env = env
        
        if not db:
            self.db = self.env.get_db_cnx()
        else:
            self.db = db
        
        """Downloader DB existence check"""
        tracdownloader.db.DownloaderDB(self.env)
        
        self._categories = None
        
        self.list = self.get_categories()
        
    def get_categories(self):
        """
        Gets a tuple of dictionary of categories - [id: Category] and
        list of Category objects with correct order.
        """
        
        if self._categories:
            return self._categories
        
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM downloader_category "
                       "WHERE deleted IS NULL "
                       "ORDER BY sort, name")
        
        categories = {}
        categories_list = []
        for (id,) in cursor:
            categories[id] = Category(self.env, id, self.db)
            categories_list.append(categories[id])
        
        self._categories = categories, categories_list
        return categories, categories_list


class Category(object):
    """Object representation of category of downloads"""
    
    def __init__(self, env, id=None, db=None):
        self.env = env
        
        if not db:
            self.db = self.env.get_db_cnx()
        else:
            self.db = db
        
        if not id:
            self._init_defaults()
        else:
            self._fetch_cat(id)
        
        self._releases = None
            
    def _init_defaults(self):
        self.id = None
        self.name = None
        self.notes = None
        self.sort = None
        self.timestamp = time.time()
        self.is_new = True
        
    def _fetch_cat(self, id):
        cursor = self.db.cursor()
        cursor.execute("SELECT id, name, notes, sort, timestamp "
            "FROM downloader_category "
            "WHERE id = %s", (id,))
        record = cursor.fetchone()
        self.id = record[0]
        self.name = record[1]
        self.notes = record[2]
        self.sort = record[3]
        self.timestamp = record[4]
        self.is_new = False
    
    def _insert(self):
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO downloader_category"
            "(name, notes, sort, timestamp) "
            "VALUES(%s, %s, %s, %s)", 
            (self.name, self.notes, self.sort, self.timestamp))
        self.id = self.db.get_last_id(cursor, 'downloader_category')
        self.db.commit()
        self.is_new = False
        
    def _update(self):
        # Set new timestamp
        self.timestamp = time.time()
        
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE downloader_category "
            "SET name=%s, notes=%s, sort=%s, timestamp=%s "
            "WHERE id=%s", 
            (self.name, self.notes, self.sort, self.timestamp, self.id))
        self.db.commit()
        
    def save(self):
        if self.is_new:
            self._insert()
        else:
            self._update()
            
    def delete(self):
        """Deletes this Category and all releases in it."""
        
        
        # Don't do anything with unsaved
        if self.is_new:
            return
        
        # Find all releases in this category and delete them
        releases, releases_list = self.get_releases()
        for release in releases_list:
            release.delete()
           
        # Delete this category record
        cursor = self.db.cursor()
        cursor.execute("UPDATE downloader_category SET deleted=1 " 
                       "WHERE id=%s", (self.id,))
        self.db.commit()
        self.is_new = True
        self.env.log.info("Category " + self.name + " was deleted.")
    
    def get_releases(self):
        """
        Gets a tuple of dictionary of releases - [id: Release] and
        list of Release objects with correct order.
        """
        
        if self._releases:
            return self._releases
        
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM downloader_release "
                       "WHERE category=%s AND deleted IS NULL "
                       "ORDER BY sort, name", (self.id,))
        
        releases = {}
        releases_list = []
        for (id,) in cursor:
            releases[id] = Release(self.env, id, self.db)
            releases_list.append(releases[id])
        
        self._releases = releases, releases_list
        return releases, releases_list
    
    
class Release(object):
    """Object representation of release of downloads"""
    
    def __init__(self, env, id=None, db=None):
        self.env = env
        
        if not db:
            self.db = self.env.get_db_cnx()
        else:
            self.db = db
        
        if not id:
            self._init_defaults()
        else:
            self._fetch_rel(id)
        
        self._files = None
            
    def _init_defaults(self):
        self.id = None
        self.category = None
        self.name = None
        self.notes = None
        self.sort = None
        self.timestamp = time.time()
        self.is_new = True
        
    def _fetch_rel(self, id):
        cursor = self.db.cursor()
        cursor.execute("SELECT id, category, name, notes, sort, timestamp "
            "FROM downloader_release "
            "WHERE id = %s", (id,))
        record = cursor.fetchone()
        self.id = record[0]
        self.category = record[1]
        self.name = record[2]
        self.notes = record[3]
        self.sort = record[4]
        self.timestamp = record[5]
        self.is_new = False
    
    def _insert(self):
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO downloader_release"
            "(name, category, notes, sort, timestamp) "
            "VALUES(%s, %s, %s, %s, %s)", 
            (self.name, self.category, self.notes, self.sort, self.timestamp))
        self.id = self.db.get_last_id(cursor, 'downloader_release')
        self.db.commit()
        self.is_new = False
        
    def _update(self):
        # Set new timestamp
        self.timestamp = time.time()
        
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE downloader_release "
            "SET name=%s, category=%s, notes=%s, sort=%s, timestamp=%s "
            "WHERE id=%s", 
            (self.name, self.category, self.notes, self.sort, self.timestamp, self.id))
        self.db.commit()
        
    def save(self):
        if self.is_new:
            self._insert()
        else:
            self._update()
            
    def delete(self):
        """Deletes this Release and all files in it."""
        
        # Don't do anything with unsaved
        if self.is_new:
            return
        
        # Find all releases in this category and delete them
        files, files_list = self.get_files()
        for file in files_list:
            file.delete()
           
        # Delete this category record
        cursor = self.db.cursor()
        cursor.execute("UPDATE downloader_release SET deleted=1 " 
                       "WHERE id=%s", (self.id,))
        self.db.commit()
        self.is_new = True
        self.env.log.info("Release " + self.name + " was deleted.")
    
    def get_releases(env):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT id FROM downloader_release "
                       "WHERE deleted IS NULL "
                       "ORDER BY name, timestamp")
        releases = []
        for (id,) in cursor:
            releases.append(Release(env, id, db))
        
        return releases
    get_releases = staticmethod(get_releases)
    
    def get_files(self):
        """
        Gets a tuple of dictionary of files - [id: File] and
        list of File objects with correct order.
        """
        
        if self._files:
            return self._files
        
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM downloader_file "
                       "WHERE release=%s AND deleted IS NULL "
                       "ORDER BY sort, name", (self.id,))
        
        files = {}
        files_list = []
        for (id,) in cursor:
            files[id] = File(self.env, id, self.db)
            files_list.append(files[id])
        
        self._files = files, files_list
        return files, files_list
            
            
class File(object):
    """Object representation of file of downloads"""
    
    def __init__(self, env, id=None, db=None):
        self.env = env
        
        if not db:
            self.db = self.env.get_db_cnx()
        else:
            self.db = db
        
        if not id:
            self._init_defaults()
        else:
            self._fetch_file(id)
            
    def _init_defaults(self):
        self.id = None
        self.file = None
        self.release = None
        self.name = None
        self.notes = None
        self.sort = None
        self.name_disp = None
        self.timestamp = time.time()
        self.architecture = None
        self.is_new = True
        
    def _fetch_file(self, id):
        cursor = self.db.cursor()
        cursor.execute("SELECT id, release, name, notes, sort, timestamp, architecture "
            "FROM downloader_file "
            "WHERE id = %s", (id,))
        record = cursor.fetchone()
        if not record:
            raise TracError('File with id ' + str(id) + ' not found.')
        self.id = record[0]
        self.release = record[1]
        self.name = record[2]
        self.name_disp = self.name
        self.notes = record[3]
        self.sort = record[4]
        self.timestamp = record[5]
        self.architecture = record[6]
        self.is_new = False
        
        self.name_disp = replace(self.name_disp, '+', '+&#8203;')
        self.name_disp = replace(self.name_disp, '_', '_&#8203;')
        self.name_disp = replace(self.name_disp, '.', '.&#8203;')
        self.name_disp = replace(self.name_disp, '-', '-&#8203;')
        self.name_disp = util.Markup(self.name_disp)
        
        # Set file path
        self._set_file_path()
    
    def _set_file_path(self):
        file = downloader_dir + "/" + str(self.id)
        self.file = file
    
    def _insert(self):
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO downloader_file"
            "(name, release, notes, sort, timestamp, architecture) "
            "VALUES(%s, %s, %s, %s, %s, %s)", 
            (self.name, self.release, self.notes, self.sort, self.timestamp, self.architecture))
        self.id = self.db.get_last_id(cursor, 'downloader_file')
        self.db.commit()
        self.is_new = False
        
    def _update(self):
        # Set new timestamp
        self.timestamp = time.time()
        
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE downloader_file "
            "SET name=%s, release=%s, notes=%s, sort=%s, timestamp=%s, architecture=%s "
            "WHERE id=%s", 
            (self.name, self.release, self.notes, self.sort, self.timestamp, self.architecture, self.id))
        self.db.commit()
        
    def save(self):
        if self.is_new:
            self._insert()
            self.save_file()
        else:
            self._update()
    
    def save_file(self):
        target = file(os.path.normpath( \
            downloader_dir + '/' + str(self.id)), "wb")
        shutil.copyfileobj(self.fileobj, target)
        target.close()
        
        # Set new file path
        self._set_file_path()
    
    def serve_file(self, req):
        """Find, open, find mime type and serve file to user."""
        
        try:
            file_obj = file(self.file, "rb")
        except IOError:
            raise TracError, 'Sorry. Error reading the file ' + self.file + '.'
        
        mime = MimeTypes(self.env).dict
        mime_type = 'application/octet-stream'
        
        # Find the extension of the file
        match = re.match(r'.*\.([^\.]*?)$', self.name)
        if match:
            ext = match.group(1)
            if mime.has_key(ext):
                mime_type = mime[ext]
        
        req.send_response(200)
        req.send_header('Content-Type', mime_type)
        req.end_headers()

        # Serve file kilobyte by kilobyte
        while True:
            part = file_obj.read(1024)
            if not part:
                break
            req.write(part)
            
        file_obj.close()
    
    def delete(self):
        """Deletes this File."""
        
        if not self.is_new:
            # Delete file
            if os.access(self.file, os.F_OK + os.W_OK):
                os.remove(self.file)
            else:
                self.env.log.warning("File %s wasn't deleted - cannot access file." % self.file)
            
            # Maerk this file db record assert deleted
            cursor = self.db.cursor()
            cursor.execute("UPDATE downloader_file SET deleted=1 " 
                           "WHERE id=%s", (self.id,))
            self.db.commit()
            self.is_new = True
            self.env.log.info("File " + self.name + " was deleted.")
    
    def get_files(env):
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT id FROM downloader_file "
                       "WHERE deleted IS NULL "
                       "ORDER BY name, timestamp")
        files = []
        for (id,) in cursor:
            files.append(File(env, id, db=db))
        
        return files
    get_files = staticmethod(get_files)

class DownloadData:
    def __init__(self, env, req, conf=None, file_id=None, id=None):
        global config
        self.env = env
        self.req = req
        self.db = self.env.get_db_cnx()
        self.schema = form_data.quest_form
        self.conf = conf
        config = conf
        self.id = id
        self.file_id = file_id
        self.timestamp = time.time()
        self.errors = None
        self.attr = {}
        if self.req.args.has_key('submit'):
            self.unfilled = False
        else:
            self.unfilled = True
            
        # Fetch data from db if id is given
        if id:
            self.fetch_from_db(id)
    
    def read_data(self):
        """Reads data from incoming form and saves iter into internal schema."""
        req = self.req
        conf = self.conf
        self.radios_mustchoose = []
        self.errors = []
        for key, item in enumerate(self.schema):
            if not item.has_key('name'):
                continue
            
            # Check validity of data
            if not self.unfilled:
                self._check_field(key, item)
            
            # Fill structure from form data
            if req.args.has_key(item['name']):
                # Radiobox
                if item.has_key('type') and item['type'] == 'radio':
                    if req.args[item['name']].value == item['value']:
                        self.schema[key]['selected'] = True
                    continue
                # Checkbox
                if item.has_key('type') and item['type'] == 'checkb':
                    self.schema[key]['selected'] = True
                    continue
                # Everything else
                #self.env.log.info("Read_data: " + item['name'] + "=" \
                #                  + req.args[item['name']].value)
                self.schema[key]['value'] = req.args[item['name']].value        
        
        # Captcha validity
        if not conf.getbool('downloader', 'no_captcha', 'false') \
                and not self.unfilled and cap_work:
            err_mes = "Wrong code from picture, please try again."
            if req.args.has_key('captcha_key') and req.args.has_key('captcha'):
                cap = MyCaptcha(self.env).\
                    get(req.args['captcha_key'].value)
                if not cap or not cap.valid:
                    self.errors.append("Picture timed out, please try again.")
                elif not cap.testSolutions([lower(req.args['captcha'].value)]):
                    self.errors.append(err_mes)
                    req.hdf['captcha_bad'] = True
            else:
                self.errors.append(err_mes)
                req.hdf['captcha_bad'] = True
        
        return self.schema
    
    def insert_data(self):
        """Saves data about this download to DB."""
        if not self.file_id:
            self.env.log.warning("DOWNLOADER: Data about downloader wasn't " + 
                "saved because there is not specified file.")
        cursor = self.db.cursor()
        # Save record to main downloads table
        cursor.execute("INSERT INTO downloader_downloaded(file, timestamp)"
                        "VALUES(%s, %s)", (self.file_id, self.timestamp))
        id = self.db.get_last_id(cursor, 'downloader_downloaded')
        self.db.commit()
        
        for item in self.schema:
            # Skip non input items
            if not item.has_key('name') or not item.has_key('value') or \
                    item['name'] == '':
                continue
            # Skip unchoosen radios
            if item['type'] == 'radio' and (not item.has_key('selected') or \
            not item['selected']):
                continue
            # Skip unchoosen checkboxes
            if item['type'] == 'checkb' and (not item.has_key('selected') or \
            not item['selected']):
                continue
                
            cursor.execute("INSERT INTO downloader_downloaded_attributes("
                            "downloaded, name, value) VALUES(%s, %s, %s)",
                            (id, item['name'], item['value']))
        self.db.commit()
    
    def delete(self):
        """Deletes record and it's attributes from DB."""
        if not self.id:
            return
        
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM downloader_downloaded_attributes "
                       "WHERE downloaded=%s", (self.id,))
        cursor.execute("DELETE FROM downloader_downloaded WHERE id=%s", 
                        (self.id,))
        return self.db.commit()
    
    def delete_range(env, start, end):
        """
        Deletes range of records and attributes of them from DB.
        """
        if start == '' or end == '':
            return False
        try:
            start = int(start)
            end = int(end)
        except:
            return False
        
        
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT id FROM downloader_downloaded "\
                       "WHERE timestamp>=%s AND timestamp<=%s", (start, end))
        
        ids = []
        for (id,) in cursor:
            ids.append(id)
        
        for id in ids:
            cursor.execute("DELETE FROM downloader_downloaded_attributes "
                           "WHERE downloaded=%s", (id,))
        
        cursor.execute("DELETE FROM downloader_downloaded WHERE " \
                       " timestamp>=%s AND timestamp<=%s", (start, end))
        
        
        return db.commit()
    delete_range = staticmethod(delete_range)
    
    def fetch_from_db(self, id):
        """Fetchs all data about this download from DB."""
        cursor = self.db.cursor()
        cursor.execute("SELECT file, timestamp FROM downloader_downloaded "
                       "WHERE id=%s", (id,))
        row = cursor.fetchone()
        if not row:
            raise TracError('Record with id ' + str(id) + ' was not found.')
        self.file_id = row[0]
        self.timestamp = row[1]
        
        # Fetch attributes and save them.
        cursor.execute("SELECT name, value FROM "
                       "downloader_downloaded_attributes WHERE downloaded=%s"
                       , (id,))
        for (name, value) in cursor:
            self.attr[name] = value
            
    def fetch_downloads_list(env, req=None, sort='timestamp', desc=False, \
                             per_page=None, page=1, get_range=False, \
                             count=False, \
                             filter=None, filter_id=None, range=None):
        """
        Fetch list of downloads in needed sort and with needed offset and limit.
        """
        
        # Count offset
        if per_page == None:
            offset = 0
            q_limit = ' '
        else:
            offset = (page - 1) * per_page
            q_limit = ' LIMIT %d OFFSET %d ' % (per_page, offset)
        
        if desc:
            desc = ' DESC'
        else:
            desc = ''
        
        db = env.get_db_cnx()
        cursor = db.cursor()
        
        # Get count of all records
        cursor.execute("SELECT count(id) FROM downloader_downloaded")
        row = cursor.fetchone()
        rec_count = row[0]
        
        # Filter
        if filter_id:
            filter_id = int(filter_id)
        else:
            filter_id = 0
        if filter == 'category':
            q_fil_join = " LEFT OUTER JOIN downloader_file ON " + \
                         " downloader_file.id=c.file " +\
                         " LEFT OUTER JOIN downloader_release ON " + \
                         " downloader_release.id=downloader_file.release "
            q_fil_where = ' AND category=%d ' % (filter_id,)
        elif filter == 'release':
            q_fil_join = " LEFT OUTER JOIN downloader_file ON " + \
                         " downloader_file.id=c.file "
            q_fil_where = ' AND downloader_file.release=%d ' % (filter_id,)
        elif filter == 'file':
            q_fil_join = ' '
            q_fil_where = ' AND c.file=%d ' % (filter_id,)
        else:
            q_fil_join = ' '
            q_fil_where = ' '
            
        # Range
        if isinstance(range, tuple) and len(range) == 2:
            min_val, max_val = range
            q_rng_where = (" AND c.timestamp>= %d " + 
                          " AND c.timestamp<= %d ") % \
                          (min_val, max_val)
        else:
            q_rng_where = ' '
        
        # Fetech sorted piece of data
        q_attr_from = ''
        q_attr_on = ''
        q_attr_where = ' c.id > %s '
        q_attr_sort = 0    
        if sort == 'timestamp':
            sort = 'c.timestamp'
        elif sort == 'file_name':
            sort = 'c.name'
        else:
            q_attr_from = " LEFT OUTER JOIN " \
                " downloader_downloaded_attributes AS a "
            q_attr_on = " ON a.downloaded=c.id "
            q_attr_where = " a.name=%s " \
                "OR a.name='' OR a.name IS NULL "
            q_attr_sort = sort
            sort = 'a.value'
            
        # What to fetch
        if get_range:
            q_get_rng_select = ' min(c.timestamp), max(c.timestamp) '
        elif count:
            q_get_rng_select = ' count(c.id) '
        else:
            q_get_rng_select = ' c.id '
            
        """
        env.log.info(
            "SELECT %s "
            "FROM (downloader_downloaded AS d JOIN downloader_file AS f ON " \
            " f.id=d.file) AS c %s %s %s "
            "WHERE %s %s %s "
            " ORDER BY %s %s" % 
            (q_get_rng_select, q_attr_from, q_attr_on, q_fil_join, \
             q_attr_where, q_fil_where, q_rng_where, sort + desc, q_limit) % \
            (q_attr_sort,)
            )
        """
            
        cursor.execute(
            "SELECT %s "
            "FROM (downloader_downloaded AS d JOIN downloader_file AS f ON " \
            " f.id=d.file) AS c %s %s %s "
            "WHERE %s AND c.deleted IS NULL %s %s "
            " ORDER BY %s %s" % 
            (q_get_rng_select, q_attr_from, q_attr_on, q_fil_join, \
             q_attr_where, q_fil_where, q_rng_where, sort + desc, q_limit), 
            (q_attr_sort,)
            )
        
        if get_range:
            row = cursor.fetchone()
            return (row[0], row[1])
        elif count:
            row = cursor.fetchone()
            return row[0]
        else:
            dwn_list = []
            for row in cursor:
                dwn_list.append(DownloadData(env, req, id=row[0]))
            return (rec_count, dwn_list)
    fetch_downloads_list = staticmethod(fetch_downloads_list)
        
    def get_attr_list(self, short=False):
        """
        Gets list of attributes  and it's values in download data.
        """
        items = []
        labels = {}
        if not short:
            file = File(self.env, self.file_id)
            items.append(['Id:', self.id])
            items.append(['File:', file.name])
            items.append(['Timestamp:', util.format_datetime(self.timestamp)])
            
        for item in form_data.quest_form:
            # External label for radio
            if item.has_key('label_for'):
                labels[item['label_for']] = item['text']
            
            if item.has_key('name') and self.attr.has_key(item['name']):
                if item.has_key('label'):
                    label = item['label']
                else:
                    label = capitalize(item['name']) + ':'
                if not label.endswith(':'):
                    label += ":"
                
                # Radio
                if item.has_key('type') and \
                        item['type'] == 'radio' and \
                        item.has_key('value'):
                    if self.attr[item['name']] != item['value']:
                        continue
                    label = labels[item['name']]
                    
                if strip(self.attr[item['name']]) != '':
                    items.append([label, self.attr[item['name']]])
                    
        return items
            
    def save_to_session(self):
        """
        Saves data about filled form of this download to 
        session for later use with next downloads.
        """
        req = self.req
        schema = self.schema
        prefix = 'form_schema_'
        for key, item in enumerate(self.schema):
            if not item.has_key('name') or not item.has_key('value') \
            or not item.has_key('type'):
                continue
            # Save to session
            # Radio
            if item['type'] == 'radio' \
            and item.has_key('selected') and item['selected']:
                req.session[prefix + item['name']] = item['value']
            # Checkbox
            if item['type'] == 'checkb' \
            and item.has_key('selected') and item['selected']:
                req.session[prefix + item['name']] = item['value']
            # Text
            elif item['type'] == 'text':
                req.session[prefix + item['name']] = item['value']
            
    def load_from_session(self):
        """
        Loads data about download from session 
        (prefills the form with them).
        """
        req = self.req
        schema = self.schema
        prefix = 'form_schema_'
        for key, item in enumerate(self.schema):
            if not item.has_key('name') or not item.has_key('type') \
                    or not req.session.has_key(prefix + item['name']):
                continue
            # Load from session
            # Radio
            if item['type'] == 'radio' and item.has_key('value') and \
            req.session.get(prefix + item['name']) == schema[key]['value']:
                schema[key]['selected'] = True
            # Checkb
            elif item['type'] == 'checkb' and item.has_key('value') and \
            req.session.get(prefix + item['name']) == schema[key]['value']:
                schema[key]['selected'] = True
            elif item['type'] == 'text':
                schema[key]['value'] = req.session.get(prefix + item['name'])
        self.schema = schema
        
    # Internal methods
    def _check_field(self, key, item):
        """Checks validity of given field from form. True/False"""
        # Text
        if self.req.args.has_key(item['name']) \
        and item.has_key('regexp') \
        and item.has_key('type') and item['type'] == 'text':
            regexp = re.compile(item['regexp'])
            val = self.req.args[item['name']].value
            if regexp.match(val) is None:
                # Set errinfo for output if exists
                if item.has_key('errinfo'):
                    self.errors.append(item['errinfo'])
                else:
                    self.errors.append('')
                self.schema[key]['bad'] = True
        # Radiobox
        if item.has_key('type') and item['type'] == 'radio':
            if item.has_key('mustchoose') and item['mustchoose']:
                self.radios_mustchoose.append(item['name'])
            if not self.req.args.has_key(item['name']) \
            and item['name'] in self.radios_mustchoose:
                # Set errinfo for output if exists
                if item.has_key('errinfo'):
                    self.errors.append(item['errinfo'])
                else:
                    self.errors.append('')
                self.schema[key]['bad'] = True

class MimeTypes:
    def __init__(self, env):
        self.env = env
        self.py_list = os.path.normpath(os.path.dirname(__file__) + \
                '/mime_list.py')
        self.text_list = os.path.normpath(os.path.dirname(__file__) + \
                '/mime_list.txt')
        if self.check_age():
            self.update_py_list()
        import mime_list
        self.dict = mime_list.mime_dict
        
    def check_age(self):
        """
        Returns True when the text file is younger 
        than py file with list of mime types.
        """
        # If txt file is inaccessable, we just say that update is not needed
        # because thats probably the case when we are input egg package
        try:
            _ = os.path.getmtime(self.text_list)
        except OSError:
            return False
        try:
            if os.path.getmtime(self.text_list) < \
                    os.path.getmtime(self.py_list):
                return False
        except:
            return True
        return True
        
    def update_py_list(self):
        try:
            self.text_list_f = file(self.text_list, 'r')
        except IOError:
            """Try to create empty file."""
            self.text_list_f = file(self.text_list, 'w')
            
        self.py_list_f = file(self.py_list, 'w')
        
        # Write start of python dictionary
        self.py_list_f.write('mime_dict = {' + "\n")
        
        for line in self.text_list_f:
            # Skip empty lines and comment lines
            if strip(line) == '' or line.startswith('//'):
              continue
            line = string.split(line, ' ')
            self.py_list_f.write("'" + line[0] + "':'" + line[1] + "',\n")
        
        # Write end of python dictionary
        self.py_list_f.write('}')
        
        self.py_list_f.close()

class MyCaptcha:
    """Wrapper for easy use of captcha"""
    def __init__(self, env):
        self.env = env
        self.cap = Captcha.PersistentFactory(self._captcha_tmp_file())
    
    def get(self, id):
        """Wrapper for PersistentFactory().get()"""
        return self.cap.get(id)
    
    def new(self): 
        """Wrapper for PersistentFactory().new()"""
        new_captcha = self.cap.new(CaptchaStyle)
        self.href = self.env.href.downloader('captcha', new_captcha.id)
        return new_captcha
    
    def _captcha_tmp_file(self):
        return os.path.normpath(downloader_dir + "/captcha_inst.tmp")

if cap_work:
    class CaptchaStyle(Captcha.Visual.ImageCaptcha):
        """Captcha layer set."""
        def getLayers(self):
            global config # Hack coz of stupid Captcha
            # Defaults for config of this Class
            config_defaults(config)
            
            font_max = int(config.get('downloader', 'captcha_font_size', '35'))
            font_min = font_max - 7
            font_border = \
                int(config.get('downloader', 'captcha_font_border', '2'))
            
            num_of_letters = \
                int(config.get('downloader', 'captcha_num_of_letters', '4'))
            
            word = self.getWord(num_of_letters)
            self.addSolution(lower(word))
            self.addSolution(replace(lower(word), 'o', '0')) # o replace by 0
            if config.get('downloader', 'captcha_hardness', 'normal') == \
                    'normal':
                layers = [
                    Captcha.Visual.Backgrounds.TiledImage(),
                    #Captcha.Visual.Backgrounds.RandomDots(),
                    Captcha.Visual.Text.TextLayer(word, \
                        fontFactory=Captcha.Visual.Text.FontFactory((\
                        font_min, font_max), "vera"), borderSize=font_border),
                    Captcha.Visual.Distortions.SineWarp(),
                    ]
            elif config.get('downloader', 'captcha_hardness', 'normal') == \
                    'hard':
                layers = [
                    Captcha.Visual.Backgrounds.TiledImage(),
                    Captcha.Visual.Backgrounds.RandomDots(),
                    Captcha.Visual.Text.TextLayer(word, \
                        fontFactory=Captcha.Visual.Text.FontFactory((\
                        font_min, font_max), "vera"), borderSize=font_border),
                    Captcha.Visual.Distortions.SineWarp(),
                    ]
                    
            return layers
                
        def getWord(self, min_len, max_len=None):
            if max_len and max_len > min_len:
                len = random.choice(range(min_len, max_len))
            else:
                len = min_len
            
            word = ""
            i = 0
            while i < len:
                i = i + 1
                word += random.choice(list(ascii_letters + '123456789'))
            return word
    
