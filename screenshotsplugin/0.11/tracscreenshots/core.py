# -*- coding: utf-8 -*-

import sys, re, os, os.path, shutil, mimetypes, unicodedata, Image, ImageOps
from datetime import *
from zipfile import *
from StringIO import *

# Deprecated as for Python 2.6.
try:
    import sets
except:
    pass

from genshi.core import Markup
from genshi.builder import tag

from trac.core import *
from trac.config import Option, ListOption, PathOption
from trac.mimeview import Mimeview, Context
from trac.web.chrome import add_stylesheet, add_script, format_to_oneliner, \
  pretty_timedelta
from trac.util.text import to_unicode
from trac.util.datefmt import to_timestamp

from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider

from tracscreenshots.api import *

no_screenshot = {'id' : 0}

class ScreenshotsCore(Component):
    """
        The core module implements plugin's main page and mainnav button,
        provides permissions and templates.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    # Screenshots renderers.
    renderers = ExtensionPoint(IScreenshotsRenderer)

    # Screenshot change listeners.
    change_listeners = ExtensionPoint(IScreenshotChangeListener)

    # Items for not specified component and version.
    none_component = {'name' : 'none',
                      'description' : 'none'}
    none_version = {'name' : 'none',
                    'description' : 'none'}

    # Configuration options.
    mainnav_title = Option('screenshots', 'mainnav_title', 'Screenshots',
      doc = 'Main navigation bar button title.')
    metanav_title = Option('screenshots', 'metanav_title', '',
      doc = 'Meta navigation bar link title.')
    path = PathOption('screenshots', 'path', '../screenshots',
      doc = 'Path where to store uploaded screenshots.')
    ext = ListOption('screenshots', 'ext', 'jpg,png',
      doc = 'List of screenshot file extensions that can be uploaded. Must be'
      ' supported by PIL.')
    formats = ListOption('screenshots', 'formats', 'raw,html,jpg,png',
      doc = 'List of allowed formats for screenshot download.')
    default_format = Option('screenshots', 'default_format', 'html',
      doc = 'Default format for screenshot download links.')
    default_components = ListOption('screenshots', 'default_components', 'all',
      doc = 'List of components enabled by default.')
    default_versions = ListOption('screenshots', 'default_versions', 'all',
      doc = 'List of versions enabled by default.')
    default_filter_relation = Option('screenshots', 'default_filter_relation',
      'or', doc = 'Logical relation between component and version part of'
      ' screenshots filter.')
    default_orders = ListOption('screenshots', 'default_orders',
      'id', doc = 'List of names of database fields that are used to'
      ' sort screenshots.')
    default_order_directions = ListOption('screenshots',
      'default_order_directions', 'asc', doc = 'List of ordering '
      'directions for fields specified in default_orders configuration '
      'options.')

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        view = 'SCREENSHOTS_VIEW'
        filter = ('SCREENSHOTS_FILTER', ['SCREENSHOTS_VIEW'])
        order = ('SCREENSHOTS_ORDER', ['SCREENSHOTS_VIEW'])
        add = ('SCREENSHOTS_ADD', ['SCREENSHOTS_VIEW'])
        edit = ('SCREENSHOTS_EDIT', ['SCREENSHOTS_VIEW'])
        delete = ('SCREENSHOTS_DELETE', ['SCREENSHOTS_VIEW'])
        admin = ('SCREENSHOTS_ADMIN', ['SCREENSHOTS_ORDER',
          'SCREENSHOTS_FILTER', 'SCREENSHOTS_ADD', 'SCREENSHOTS_EDIT',
          'SCREENSHOTS_DELETE', 'SCREENSHOTS_VIEW'])
        return [view, filter, order, add, edit, delete, admin]

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('screenshots', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods.

    def get_active_navigation_item(self, req):
        return 'screenshots'

    def get_navigation_items(self, req):
        if req.perm.has_permission('SCREENSHOTS_VIEW'):
            if self.mainnav_title:
                yield ('mainnav', 'screenshots', tag.a(self.mainnav_title,
                  href = req.href.screenshots()))
            if self.metanav_title:
                yield ('metanav', 'screenshots', tag.a(self.metanav_title,
                  href = req.href.screenshots()))

    # IRequestHandler methods.

    def match_request(self, req):
        match = re.match(r'/screenshots(?:/(\d+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['action'] = 'get-file'
                req.args['id'] = match.group(1)
            return 1

    def process_request(self, req):
        # Create request context.
        context = Context.from_request(req)
        context.realm = 'screenshots-core'

        # Template data dictionary.
        req.data = {}

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Prepare data structure.
        req.data['title'] = self.mainnav_title or self.metanav_title
        req.data['has_tags'] = self.env.is_component_enabled(
          'tracscreenshots.tags.ScreenshotsTags')

        # Get action from request and perform them.
        actions = self._get_actions(context)
        self.log.debug('actions: %s' % (actions,))
        template, content_type = self._do_actions(context, actions)

        # Add CSS style and JavaScript scripts.
        add_stylesheet(req, 'screenshots/css/screenshots.css')
        add_script(req, 'screenshots/js/screenshots.js')

        # Return template and its data.
        db.commit()
        return (template + '.html', {'screenshots' : req.data}, content_type)

    # Internal functions.

    def _get_actions(self, context):
        action = context.req.args.get('action')
        self.log.debug('action: %s' % (action,))
        if action == 'get-file':
            return ['get-file']
        elif action == 'add':
            return ['add']
        elif action == 'post-add':
            return ['post-add', 'view']
        elif action == 'edit':
            return ['edit', 'add']
        elif action == 'post-edit':
            return ['post-edit', 'view']
        elif action == 'delete':
            return ['delete', 'view']
        elif action == 'filter':
            return ['filter', 'view']
        elif action == 'order':
            return ['order', 'view']
        else:
            return ['view']

    def _do_actions(self, context, actions):
        # Get API component.
        api = self.env[ScreenshotsApi]

        for action in actions:
            if action == 'get-file':
                context.req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Get request arguments.
                screenshot_id = int(context.req.args.get('id') or 0)
                format = context.req.args.get('format') or self.default_format
                width = int(context.req.args.get('width') or 0)
                height =  int(context.req.args.get('height') or 0)

                # Check if requested format is allowed.
                if not format in self.formats:
                    raise TracError('Requested screenshot format that is not'
                      ' allowed.', 'Requested format not allowed.')

                # Get screenshot.
                screenshot = api.get_screenshot(context, screenshot_id)

                # Check if requested screenshot exists.
                if not screenshot:
                    if context.req.perm.has_permission('SCREENSHOTS_ADD'):
                        context.req.redirect(context.req.href.screenshots(
                          action = 'add'))
                    else:
                        raise TracError('Screenshot not found.')

                # Set missing dimensions.
                width = width or screenshot['width']
                height = height or screenshot['height']

                if format == 'html':
                    # Format screenshot for presentation.
                    screenshot['author'] = format_to_oneliner(self.env, context,
                      screenshot['author'])
                    screenshot['name'] = format_to_oneliner(self.env, context,
                      screenshot['name'])
                    screenshot['description'] = format_to_oneliner(self.env,
                      context, screenshot['description'])
                    screenshot['time'] = pretty_timedelta(to_datetime(
                      screenshot['time'], utc))

                    # For HTML preview format return template.
                    context.req.data['screenshot'] = screenshot
                    return ('screenshot', None)
                else:
                    # Prepare screenshot filename.
                    name, ext = os.path.splitext(screenshot['file'])
                    format = (format == 'raw') and ext or '.' + format
                    path = os.path.normpath(os.path.join(self.path, to_unicode(
                      screenshot['id'])))
                    filename = os.path.normpath(os.path.join(path, '%s-%sx%s%s'
                      % (name, width, height, format)))
                    orig_name = os.path.normpath(os.path.join(path, '%s-%sx%s%s'
                      % (name, screenshot['width'], screenshot['height'], ext)))
                    base_name = os.path.normpath(os.path.basename(filename))

                    self.log.debug('filemame: %s' % (filename,))

                    # Create requested file from original if not exists.
                    if not os.path.isfile(filename.encode('utf-8')):
                        self._create_image(orig_name, path, name, format,
                          width, height)

                    # Guess mime type.
                    file = open(filename.encode('utf-8'), "r")
                    file_data = file.read(1000)
                    file.close()
                    mimeview = Mimeview(self.env)
                    mime_type = mimeview.get_mimetype(filename, file_data)
                    if not mime_type:
                        mime_type = 'application/octet-stream'
                    if 'charset=' not in mime_type:
                        charset = mimeview.get_charset(file_data, mime_type)
                        mime_type = mime_type + '; charset=' + charset

                    # Send file to request.
                    context.req.send_header('Content-Disposition',
                      'attachment;filename="%s"' % (base_name))
                    context.req.send_header('Content-Description',
                      screenshot['description'])
                    context.req.send_file(filename.encode('utf-8'), mime_type)

            elif action == 'add':
                context.req.perm.assert_permission('SCREENSHOTS_ADD')

                # Get request arguments.
                index = int(context.req.args.get('index') or 0)

                # Fill data dictionary.
                context.req.data['index'] = index
                context.req.data['versions'] = api.get_versions(context)
                context.req.data['components'] = api.get_components(context)

                # Return template with add screenshot form.
                return ('screenshot-add', None)

            elif action == 'post-add':
                context.req.perm.assert_permission('SCREENSHOTS_ADD')

                # Get image file from request.
                file, filename = self._get_file_from_req(context.req)
                name, ext = os.path.splitext(filename)
                ext = ext.lower()
                filename = name + ext

                # Is uploaded file archive or single image?
                if ext == '.zip':
                    # Get global timestamp for all files in archive.
                    timestamp = to_timestamp(datetime.now(utc))

                    # List files in archive.
                    zip_file = ZipFile(file)
                    for filename in zip_file.namelist():
                        # Test file extensions for supported type.
                        name, ext = os.path.splitext(filename)
                        tmp_ext = ext.lower()[1:]
                        if tmp_ext in self.ext and tmp_ext != 'zip':
                            # Decompress image file
                            data = zip_file.read(filename)
                            file = StringIO(data)
                            filename = to_unicode(os.path.basename(filename))

                            # Screenshots must be identified by timestamp.
                            timestamp += 1

                            # Create image object.
                            image = Image.open(file)

                            # Construct screenshot dictionary from form values.
                            screenshot = {'name' :  context.req.args.get('name'),
                              'description' : context.req.args.get('description'),
                              'time' : timestamp,
                              'author' : context.req.authname,
                              'tags' : context.req.args.get('tags'),
                              'file' : filename,
                              'width' : image.size[0],
                              'height' : image.size[1],
                              'priority' : int(context.req.args.get('priority')
                              or '0')}
                            self.log.debug('screenshot: %s' % (screenshot,))

                            # Save screenshot file and add DB entry.
                            self._add_screenshot(context, api, screenshot, file)

                    zip_file.close()
                else:
                    # Create image object.
                    image = Image.open(file)

                    # Construct screenshot dictionary from form values.
                    screenshot = {'name' :  context.req.args.get('name'),
                      'description' : context.req.args.get('description'),
                      'time' : to_timestamp(datetime.now(utc)),
                      'author' : context.req.authname,
                      'tags' : context.req.args.get('tags'),
                      'file' : filename,
                      'width' : image.size[0],
                      'height' : image.size[1],
                      'priority' : int(context.req.args.get('priority')
                      or '0')}
                    self.log.debug('screenshot: %s' % (screenshot,))

                    # Add single image.
                    self._add_screenshot(context, api, screenshot, file)

                # Close input file.
                file.close()

                # Clear ID to prevent display of edit and delete button.
                context.req.args['id'] = None

            elif action == 'edit':
                context.req.perm.assert_permission('SCREENSHOTS_EDIT')

                # Get request arguments.
                screenshot_id = context.req.args.get('id')

                # Prepare data dictionary.
                context.req.data['screenshot'] = api.get_screenshot(context,
                  screenshot_id)

            elif action == 'post-edit':
                context.req.perm.assert_permission('SCREENSHOTS_EDIT')

                # Get screenshot arguments.
                screenshot_id = int(context.req.args.get('id') or 0)

                # Get old screenshot
                old_screenshot = api.get_screenshot(context, screenshot_id)

                # Check if requested screenshot exits.
                if not old_screenshot:
                    raise TracError('Edited screenshot not found.',
                      'Screenshot not found.')

                # Get image file from request.
                image = context.req.args['image']
                if hasattr(image, 'filename') and image.filename:
                    in_file, filename = self._get_file_from_req(context.req)
                    name, ext = os.path.splitext(filename)
                    filename = name + ext.lower()
                else:
                    filename = None

                # Construct screenshot dictionary from form values.
                screenshot = {'name' :  context.req.args.get('name'),
                              'description' : context.req.args.get(
                                'description'),
                              'author' : context.req.authname,
                              'tags' : context.req.args.get('tags'),
                              'components' : context.req.args.get(
                                'components') or [],
                              'versions' : context.req.args.get('versions') or \
                                [],
                              'priority' : int(context.req.args.get('priority')
                                or '0')}

                # Update dimensions and filename if image file is updated.
                if filename:
                    image = Image.open(in_file)
                    screenshot['file'] = filename
                    screenshot['width'] = image.size[0]
                    screenshot['height'] = image.size[1]

                # Convert components and versions to list if only one item is
                # selected.
                if not isinstance(screenshot['components'], list):
                     screenshot['components'] = [screenshot['components']]
                if not isinstance(screenshot['versions'], list):
                     screenshot['versions'] = [screenshot['versions']]

                self.log.debug('screenshot: %s' % (screenshot))

                # Edit screenshot.
                api.edit_screenshot(context, screenshot_id, screenshot)

                # Prepare file paths.
                if filename:
                    name, ext = os.path.splitext(screenshot['file'])
                    path = os.path.normpath(os.path.join(self.path, to_unicode(
                      screenshot_id)))
                    filepath = os.path.normpath(os.path.join(path, '%s-%ix%i%s'
                      % (name, screenshot['width'], screenshot['height'], ext)))

                    self.log.debug('path: %s' % (path,))
                    self.log.debug('filepath: %s' % (filepath,))

                    # Delete present images.
                    try:
                        for file in os.listdir(path):
                            file = os.path.normpath(os.path.join(path,
                              to_unicode(file)))
                            os.remove(file.encode('utf-8'))
                    except Exception, error:
                        raise TracError('Error deleting screenshot. Original' \
                          ' message was: %s' % (to_unicode(error),))

                    # Store uploaded image.
                    try:
                        out_file = open(filepath.encode('utf-8'), 'wb+') 
                        in_file.seek(0)
                        shutil.copyfileobj(in_file, out_file)
                        out_file.close()
                    except Exception, error:
                        try:
                            os.remove(filepath.encode('utf-8'))
                        except:
                            pass
                        raise TracError('Error storing file. Is directory' \
                          ' specified in path config option in [screenshots]' \
                          ' section of trac.ini existing? Original message was: %s' \
                          % (to_unicode(error),))

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_changed(context.req, screenshot,
                      old_screenshot)

                # Clear ID to prevent display of edit and delete button.
                context.req.args['id'] = None

            elif action == 'delete':
                context.req.perm.assert_permission('SCREENSHOTS_DELETE')

                # Get request arguments.
                screenshot_id = context.req.args.get('id')

                # Get screenshot.
                screenshot = api.get_screenshot(context, screenshot_id)

                # Check if requested screenshot exits.
                if not screenshot:
                    raise TracError('Deleted screenshot not found.',
                      'Screenshot not found.')

                # Delete screenshot.
                api.delete_screenshot(context, screenshot['id'])

                # Delete screenshot files. Don't append any other files there :-).
                path = os.path.normpath(os.path.join(self.path, to_unicode(
                  screenshot['id'])))
                self.log.debug('path: %s' % (path,))
                try:
                    for file in os.listdir(path):
                        file = os.path.normpath(os.path.join(path,
                          to_unicode(file)))
                        os.remove(file.encode('utf-8'))
                    os.rmdir(path.encode('utf-8'))
                except Exception, error:
                    raise TracError('Error deleting screenshot. Original' \
                      ' message was: %s' % (to_unicode(error),))

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_deleted(context.req, screenshot)

                # Clear id to prevent display of edit and delete button.
                context.req.args['id'] = None

            elif action == 'filter':
                context.req.perm.assert_permission('SCREENSHOTS_FILTER')

                # Update enabled components from request.
                components = context.req.args.get('components') or []
                if not isinstance(components, list):
                    components = [components]
                self._set_enabled_components(context.req, components)

                # Update enabled versions from request.
                versions = context.req.args.get('versions') or []
                if not isinstance(versions, list):
                    versions = [versions]
                self._set_enabled_versions(context.req, versions)

                # Update filter relation from request.
                relation = context.req.args.get('filter_relation') or 'or'
                self._set_filter_relation(context.req, relation)

            elif action == 'order':
                context.req.perm.assert_permission('SCREENSHOTS_ORDER')

                # Get three order fields from request and store them to session.
                orders = []
                I = 0
                while context.req.args.has_key('order_%s' % (I,)):
                    orders.append((context.req.args.get('order_%s' % (I,)) or 'id',
                      context.req.args.get('order_direction_%s' % (I,)) or 'asc'))
                    I += 1
                self._set_orders(context.req, orders)

            elif action == 'view':
                context.req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Get request arguments.
                screenshot_id = int(context.req.args.get('id') or 0)

                # Check that at least one IScreenshotsRenderer is enabled.
                if len(self.renderers) == 0:
                    raise TracError('No screenshots renderer enabled. Enable'
                      ' at least one.', 'No screenshots renderer enabled')

                # Get all available components and versions.
                components = [self.none_component] + api.get_components(
                  context.cursor)
                versions = [self.none_version] + api.get_versions(
                  context.cursor)

                # Get enabled components, versions and filter relation from
                # request or session.
                enabled_components = self._get_enabled_components(context.req)
                enabled_versions = self._get_enabled_versions(context.req)
                relation = self._get_filter_relation(context.req)
                if 'all' in enabled_components:
                    enabled_components = [component['name'] for component in
                    components]
                if 'all' in enabled_versions:
                    enabled_versions = [version['name'] for version in
                    versions]

                self.log.debug('components: %s' % (components,))
                self.log.debug('versions: %s' % (versions,))
                self.log.debug('enabled_components: %s' % (enabled_components,))
                self.log.debug('enabled_versions: %s' % (enabled_versions,))
                self.log.debug('filter_relation: %s' % (relation,))

                # Get order fields of screenshots.
                orders = self._get_orders(context.req)

                # Filter screenshots.
                screenshots = api.get_filtered_screenshots(context,
                  enabled_components, enabled_versions, relation, orders)
                self.log.debug('screenshots: %s' % (screenshots,))

                # Convert enabled components and versions to dictionary.
                enabled_components = dict(zip(enabled_components, [True] *
                  len(enabled_components)))
                enabled_versions = dict(zip(enabled_versions, [True] *
                  len(enabled_versions)))

                # Fill data dictionary.
                context.req.data['id'] = screenshot_id
                context.req.data['components'] = components
                context.req.data['versions'] = versions
                context.req.data['screenshots'] = screenshots
                context.req.data['href'] = context.req.href.screenshots()
                context.req.data['enabled_versions'] = enabled_versions
                context.req.data['enabled_components'] = enabled_components
                context.req.data['filter_relation'] = relation
                context.req.data['orders'] = orders

                # Get screenshots content template and data.
                template, content_type = self.renderers[0]. \
                  render_screenshots(context.req)
                context.req.data['content_template'] = template

                # Return main template.
                return ('screenshots', content_type)

            elif actions == 'screenshot-add':
                context.req.perm.assert_permission('SCREENSHOTS_ADD')

                # Get screenshot
                screenshot = api.get_screenshot(context, self.id)
                self.log.debug('screenshot: %s' % (screenshot,))

    """ Full implementation of screenshot addition. It creates DB entry for
    screenshot <screenshot> and stores screenshot file <file> to file system.
    """
    def _add_screenshot(self, context, api, screenshot, file):

        # Add new screenshot to DB.
        api.add_screenshot(context, screenshot)

        # Get inserted screenshot to with new id.
        screenshot = api.get_screenshot_by_time(context, screenshot['time'])

        # Prepare file paths.
        name, ext = os.path.splitext(screenshot['file'])
        path = os.path.normpath(os.path.join(self.path, to_unicode(
          screenshot['id'])))
        filepath = os.path.normpath(os.path.join(path, '%s-%ix%i%s' % (name,
          screenshot['width'], screenshot['height'], ext)))

        self.log.debug('path: %s' % (path,))
        self.log.debug('filename: %s' % (filepath,))

        # Store uploaded image.
        try:
            os.mkdir(path.encode('utf-8'))
            out_file = open(filepath.encode('utf-8'), "wb+")
            file.seek(0)
            shutil.copyfileobj(file, out_file)
            out_file.close()
        except Exception, error:
            self.log.debug(error)

            # Delete screenshot.
            api.delete_screenshot(context, screenshot['id'])

            # Remove screenshot image and directory.
            try:
                os.remove(filepath.encode('utf-8'))
            except:
                pass
            try:
                os.rmdir(path.encode('utf-8'))
            except:
                pass
            raise TracError('Error storing file. Is directory specified in path' \
              ' config option in [screenshots] section of trac.ini existing?' \
              ' Original message was: %s' % (to_unicode(error),))

        # Add components to screenshot to DB.
        components = context.req.args.get('components') or []
        if not isinstance(components, list):
            components = [components]
        for component in components:
            component = {'screenshot' : screenshot['id'],
                         'component' : component}
            api.add_component(context, component)
        screenshot['components'] = components

        # Add versions to screenshots to DB
        versions = context.req.args.get('versions') or []
        if not isinstance(versions, list):
            versions = [versions]
        for version in versions:
            version = {'screenshot' : screenshot['id'],
                       'version' : version}
            api.add_version(context, version)
        screenshot['versions'] = versions

        # Notify change listeners.
        for listener in self.change_listeners:
            listener.screenshot_created(context.req, screenshot)

    def _create_image(self, orig_name, path, name, ext, width, height):
        image = Image.open(orig_name.encode('utf-8'))
        image = image.resize((width, height), Image.ANTIALIAS)
        image_name = os.path.normpath(os.path.join(path, '%s-%sx%s%s' % (name,
          width, height, ext)))
        image.save(image_name.encode('utf-8'))

    def _get_file_from_req(self, req):
        image = req.args['image']

        # Test if file is uploaded.
        if not hasattr(image, 'filename') or not image.filename:
            raise TracError('No file uploaded.')

        # Get file size.
        if hasattr(image.file, 'fileno'):
            size = os.fstat(image.file.fileno())[6]
        else:
            image.file.seek(0, 2)
            size = image.file.tell()
            image.file.seek(0)
        if size == 0:
            raise TracError('Can\'t upload empty file.')

        # Try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        self.log.debug('input filename: %s', (image.filename,))
        filename = unicodedata.normalize('NFC', to_unicode(image.filename,
          'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        self.log.debug('output filename: %s', (filename,))

        # Check correct file type.
        reg = re.compile(r'^(.*)[.](.*)$')
        result = reg.match(filename)
        if result:
            if not result.group(2).lower() in self.ext:
                raise TracError('Unsupported uploaded file type.')
        else:
            raise TracError('Unsupported uploaded file type.')

        return image.file, filename

    def _get_enabled_components(self, req):
        if req.perm.has_permission('SCREENSHOTS_FILTER'):
            # Return existing filter from session or create default.
            if req.session.has_key('screenshots_enabled_components'):
                components = eval(req.session.get('screenshots_enabled_'
                  'components'))
            else:
                components = self.default_components
                req.session['screenshots_enabled_components'] = str(components)
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_components' configuration option.
            components = self.default_components
        return components

    def _set_enabled_components(self, req, components):
        req.session['screenshots_enabled_components'] = str(components)

    def _get_enabled_versions(self, req):
        if req.perm.has_permission('SCREENSHOTS_FILTER'):
            # Return existing filter from session or create default.
            if req.session.has_key('screenshots_enabled_versions'):
                versions = eval(req.session.get('screenshots_enabled_versions'))
            else:
                versions = self.default_versions
                req.session['screenshots_enabled_versions'] = str(versions)
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_versions' configuration option.
            versions = self.default_versions
        return versions

    def _set_enabled_versions(self, req, versions):
        req.session['screenshots_enabled_versions'] = str(versions)

    def _get_filter_relation(self, req):
        if req.perm.has_permission('SCREENSHOTS_FILTER'):
            # Return existing filter relation from session or create default.
            if req.session.has_key('screenshots_filter_relation'):
                relation = req.session.get('screenshots_filter_relation')
            else:
                relation = self.default_filter_relation
                req.session['screenshots_filter_relation'] = relation
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_filter_relation' configuration option.
            relation = self.default_filter_relation
        return relation

    def _set_filter_relation(self, req, relation):
        req.session['screenshots_filter_relation'] = relation

    def _get_orders(self, req):
        if req.perm.has_permission('SCREENSHOTS_ORDER'):
            # Get ordering fields from session or default ones.
            if req.session.has_key('screenshots_orders'):
                orders = eval(req.session.get('screenshots_orders'))
            else:
                orders = tuple(self.default_orders)
                directions = tuple(self.default_order_directions)
                orders = [(orders[I], directions[I]) for I in \
                  xrange(len(orders))]
                req.session['screenshots_orders'] = str(orders)
        else:
            # Users without SCREENSHOTS_ORDER permission uses
            # 'default_orders' configuration option.
            orders = tuple(self.default_orders)
            directions = tuple(self.default_order_directions)
            orders = [(orders[I], directions[I]) for I in xrange(len(orders))]
        return tuple(orders)

    def _set_orders(self, req, orders):
        req.session['screenshots_orders'] = str(orders)
