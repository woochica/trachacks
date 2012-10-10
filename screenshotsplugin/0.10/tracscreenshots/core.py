# -*- coding: utf-8 -*-

import sets, re, os, os.path, shutil, time, mimetypes, unicodedata, Image

from trac.core import *
from trac.config import Option, ListOption
from trac.web.main import populate_hdf
from trac.web.chrome import Chrome, add_stylesheet, add_script
from trac.web.clearsilver import HDFWrapper
from trac.util import format_datetime, pretty_timedelta, TracError
from trac.util.html import html
from trac.util.text import to_unicode

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
    path = Option('screenshots', 'path', '/var/lib/trac/screenshots',
      doc = 'Path where to store uploaded screenshots.')
    ext = ListOption('screenshots', 'ext', 'jpg,png',
      doc = 'List of screenshot file extensions that can be uploaded. Must be'
      ' supported by PIL.')
    formats = ListOption('screenshots', 'formats', 'raw,html,jpg,png',
      doc = 'List of allowed formats for screenshot download.')
    default_format = Option('screenshots', 'default_format', 'html',
      doc = 'Default format for screenshot download links.')
    default_components = ListOption('screenshots', 'default_components', 'none',
      doc = 'List of components enabled by default.')
    default_versions = ListOption('screenshots', 'default_versions', 'none',
      doc = 'List of versions enabled by default.')

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        view = 'SCREENSHOTS_VIEW'
        filter = ('SCREENSHOTS_FILTER', ['SCREENSHOTS_VIEW'])
        admin = ('SCREENSHOTS_ADMIN', ['SCREENSHOTS_FILTER',
          'SCREENSHOTS_VIEW'])
        return [view, filter, admin]

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
                yield 'mainnav', 'screenshots', html.a(self.mainnav_title,
                  href = req.href.screenshots())
            if self.metanav_title:
                yield 'metanav', 'screenshots', html.a(self.metanav_title,
                  href = req.href.screenshots())

    # IRequestHandler methods.

    def match_request(self, req):
        match = re.match(r'''^/screenshots($|/$)''', req.path_info)
        if match:
            return True
        match = re.match(r'''^/screenshots/(\d+)$''', req.path_info)
        if match:
            req.args['action'] = 'get-file'
            req.args['id'] = match.group(1)
            return True
        return False

    def process_request(self, req):
        # Get action from request and perform them.
        actions = self._get_actions(req)
        self.log.debug('actions: %s' % (actions,))
        template, data, content_type = self._do_actions(req, actions)

        # Add CSS style and JavaScript scripts.
        add_stylesheet(req, 'screenshots/css/screenshots.css')
        add_script(req, 'screenshots/js/screenshots.js')

        # Prepare HDF structure and return template.
        req.hdf['screenshots'] = data
        req.hdf['screenshots.href'] = req.href.screenshots()
        req.hdf['screenshots.title'] = self.mainnav_title or self.metanav_title
        req.hdf['screenshots.has_tags'] = self.env.is_component_enabled(
          'tracscreenshots.tags.ScreenshotsTags')
        return template, content_type

    # Internal functions.

    def _get_actions(self, req):
        action = req.args.get('action')
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
        else:
            return ['view']

    def _do_actions(self, req, actions):
        # Initialize dictionary for data.
        data = {}

        # Get database access.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get API component.
        api = self.env[ScreenshotsApi]

        for action in actions:
            if action == 'get-file':
                req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Get request arguments.
                screenshot_id = int(req.args.get('id') or 0)
                format = req.args.get('format') or self.default_format
                width = int(req.args.get('width') or 0)
                height =  int(req.args.get('height') or 0)

                # Check if requested format is allowed.
                if not format in self.formats:
                    raise TracError('Requested screenshot format that is not allowed.',
                      'Requested format not allowed.')

                # Get screenshot.
                screenshot = api.get_screenshot(cursor, screenshot_id)

                if screenshot:
                    # Set missing dimensions.
                    width = width or screenshot['width']
                    height = height or screenshot['height']

                    if format == 'html':
                        # Format screenshot attributes.
                        screenshot['time'] = pretty_timedelta(screenshot['time'])

                        # Prepare data dictionary.
                        data['screenshot'] = screenshot

                        # Return screenshot template and data.
                        return ('screenshot.cs', data, None)

                    else:
                        # Prepare screenshot filename.
                        name, ext = os.path.splitext(screenshot['file'])
                        format = (format == 'raw') and ext or '.' + format
                        path = os.path.join(self.path, unicode(screenshot['id']))
                        filename = os.path.join(path, '%s-%sx%s%s' % (name, width,
                          height, format))
                        orig_name = os.path.join(path, '%s-%sx%s%s' % (name,
                          screenshot['width'], screenshot['height'], ext))
                        self.log.debug('filemame: %s' % (filename,))

                        # Send file to request.
                        if not os.path.exists(filename):
                            self._create_image(orig_name, path, name, format,
                              width, height)

                        req.send_header('Content-Disposition',
                          'attachment;filename=%s' % (os.path.basename(filename)))
                        req.send_header('Content-Description',
                          screenshot['description'])
                        req.send_file(filename, mimetypes.guess_type(filename)[0])
                else:
                    raise TracError('Screenshot not found.')

            elif action == 'add':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Fill data dictionary.
                data['index'] = req.args.get('index')
                data['versions'] = api.get_versions(cursor)
                data['components'] = api.get_components(cursor)

                # Return template with add screenshot form.
                return ('screenshot-add.cs', data, None)

            elif action == 'post-add':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get image file from request.
                file, filename = self._get_file_from_req(req)
                name, ext = os.path.splitext(filename)
                filename = name + ext.lower()

                # Check correct file type.
                reg = re.compile(r'^(.*)[.](.*)$')
                result = reg.match(filename)
                if result:
                    if not result.group(2).lower() in self.ext:
                        raise TracError('Unsupported uploaded file type.')
                else:
                    raise TracError('Unsupported uploaded file type.')

                # Create image object.
                image = Image.open(file)

                # Construct screenshot dictionary from form values.
                screenshot = {'name' :  req.args.get('name'),
                              'description' : req.args.get('description'),
                              'time' : int(time.time()),
                              'author' : req.authname,
                              'tags' : req.args.get('tags'),
                              'file' : filename,
                              'width' : image.size[0],
                              'height' : image.size[1]}

                # Add new screenshot.
                api.add_screenshot(cursor, screenshot)

                # Get inserted screenshot to with new id.
                screenshot = api.get_screenshot_by_time(cursor,
                   screenshot['time'])

                # Add components to screenshot.
                components = req.args.get('components') or []
                if not isinstance(components, list):
                    components = [components]
                for component in components:
                    component = {'screenshot' : screenshot['id'],
                                 'component' : component}
                    api.add_component(cursor, component)
                screenshot['components'] = components

                # Add versions to screenshots
                versions = req.args.get('versions') or []
                if not isinstance(versions, list):
                    versions = [versions]
                for version in versions:
                    version = {'screenshot' : screenshot['id'],
                               'version' : version}
                    api.add_version(cursor, version)
                screenshot['versions'] = versions

                self.log.debug(screenshot)

                # Prepare file paths
                path = os.path.join(self.path, unicode(screenshot['id']))
                filepath = os.path.join(path, '%s-%ix%i.%s' % (result.group(1),
                  screenshot['width'], screenshot['height'], result.group(2)))
                path = os.path.normpath(path)
                filepath = os.path.normpath(filepath)
                self.log.debug('path: %s' % (path,))
                self.log.debug('filepath: %s' % (filepath,))

                # Store uploaded image.
                try:
                    os.mkdir(path)
                    out_file = open(filepath, 'wb+')
                    file.seek(0)
                    shutil.copyfileobj(file, out_file)
                    out_file.close()
                except Exception, error:
                    api.delete_screenshot(cursor, screenshot['id'])
                    try:
                       self.log.debug(error)
                    except:
                       pass
                    try:
                        os.remove(filename)
                    except:
                        pass
                    try:
                        os.rmdir(path)
                    except:
                        pass
                    raise TracError('Error storing file. Is directory' \
                      ' specified in path config option in [screenshots]' \
                      ' section of trac.ini existing? Original message was: %s' \
                      % (error,))

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_created(screenshot)

                # Clear id to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'edit':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get request arguments.
                screenshot_id = req.args.get('id')

                # Prepare data dictionary.
                data['screenshot'] = api.get_screenshot(cursor, screenshot_id)
                self.log.debug(data['screenshot'])

            elif action == 'post-edit':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get old screenshot
                screenshot_id = int(req.args.get('id') or 0)
                old_screenshot = api.get_screenshot(cursor, screenshot_id)

                # Check if requested screenshot exits.
                if not old_screenshot:
                    raise TracError('Edited screenshot not found.',
                      'Screenshot not found.')

                # Construct screenshot dictionary from form values.
                screenshot = {'name' :  req.args.get('name'),
                              'description' : req.args.get('description'),
                              'author' : req.authname,
                              'tags' : req.args.get('tags'),
                              'components' : req.args.get('components') or [],
                              'versions' : req.args.get('versions') or []}

                # Converst components and versions to list if only one item is
                # selected.
                if not isinstance(screenshot['components'], list):
                     screenshot['components'] = [screenshot['components']]
                if not isinstance(screenshot['versions'], list):
                     screenshot['versions'] = [screenshot['versions']]

                # Edit screenshot.
                api.edit_screenshot(cursor, screenshot_id, screenshot)

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_changed(screenshot, old_screenshot)

                # Clear id to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'delete':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get screenshot.
                screenshot = api.get_screenshot(cursor, req.args.get('id'))

                # Check if requested screenshot exits.
                if not screenshot:
                    raise TracError('Deleted screenshot not found.',
                      'Screenshot not found.')

                # Delete screenshot.
                api.delete_screenshot(cursor, screenshot['id'])

                # Delete screenshot files. Don't append any other files there :-).
                try:
                    path = os.path.join(self.path, to_unicode(screenshot['id']))
                    path = os.path.normpath(path)
                    self.log.debug('path: %s' % (path,))
                    for file in os.listdir(path):
                        file = os.path.join(path, file)
                        file = os.path.normpath(file)
                        os.remove(file)
                    os.rmdir(path)
                except:
                    pass

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_deleted(screenshot)

                # Clear id to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'filter':
                # Update enabled components from request.
                components = req.args.get('components') or []
                if not isinstance(components, list):
                    components = [components]
                req.session['enabled_components'] = str(components)

                # Update enabled versions from request.
                versions = req.args.get('versions') or []
                if not isinstance(versions, list):
                    versions = [versions]
                req.session['enabled_versions'] = str(versions)

            elif action == 'view':
                req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Check that at least one IScreenshotsRenderer is enabled
                if len(self.renderers) == 0:
                    raise TracError('No screenshots renderer enabled. Enable at least one.',
                      'No screenshots renderer enabled')

                # Get all available components and versions.
                components = [self.none_component] + api.get_components(cursor)
                versions = [self.none_version] + api.get_versions(cursor)

                # Get enabled components and versions from request or session.
                enabled_components = self._get_enabled_components(req)
                enabled_versions = self._get_enabled_versions(req)
                if 'all' in enabled_components:
                    enabled_components = [component['name'] for component in
                    components]
                if 'all' in enabled_versions:
                    enabled_versions = [version['name'] for version in
                    versions]

                self.log.debug(enabled_components)

                # Filter screenshots.
                screenshots = api.get_filtered_screenshots(cursor,
                  enabled_components, enabled_versions)

                # Convert enabled components and versions to dictionary.
                enabled_components = dict(zip(enabled_components, [True] *
                  len(enabled_components)))
                enabled_versions = dict(zip(enabled_versions, [True] *
                  len(enabled_versions)))

                # Fill data dictionary.
                data['id'] = int(req.args.get('id') or 0)
                data['components'] = components
                data['versions'] = versions
                data['screenshots'] = screenshots
                data['href'] = req.href.screenshots()
                data['enabled_versions'] = enabled_versions
                data['enabled_components'] = enabled_components

                # Get screenshots content template and data.
                template, data, content_type = self.renderers[0]. \
                  render_screenshots(req, data)
                data['content_template'] = template

                # Return main template.
                return ('screenshots.cs', data, content_type)

            elif actions == 'screenshot-add':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get screenshot
                screenshot = api.get_screenshot(cursor, self.id)
                self.log.debug('screenshot: %s' % (screenshot,))

                # Fill HDF structure
                req.hdf['screenshots.current'] = [screenshot]

        # Commit database changes.
        db.commit()

    def _create_image(self, orig_name, path, name, ext, width, height):
        image = Image.open(orig_name)
        image = image.resize((width, height), Image.BICUBIC)
        image.save(os.path.join(path, '%s-%sx%s%s' % (name, width, height,
          ext)))

    def _get_file_from_req(self, req):
        image = req.args['image']

        # Test if file is uploaded.
        if not hasattr(image, 'filename') or not image.filename:
            raise TracError('No file uploaded.')
        if hasattr(image.file, 'fileno'):
            size = os.fstat(image.file.fileno())[6]
        else:
            size = image.file.len
        if size == 0:
            raise TracError('Can\'t upload empty file.')
        filename = os.path.basename(image.filename).decode('utf-8')
        self.log.debug(filename)
        return image.file, filename

    def _get_enabled_components(self, req):
        if req.perm.has_permission('SCREENSHOTS_FILTER'):
            # Return existing filter from session or create default.
            if req.session.has_key('enabled_components'):
                components = eval(req.session.get('enabled_components'))
            else:
                components = self.default_components
                req.session['enabled_components'] = str(components)
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_components' configuration option.
            components = self.default_components
        self.log.debug('enabled_components: %s' % (components,))
        return components

    def _get_enabled_versions(self, req):
        if req.perm.has_permission('SCREENSHOTS_FILTER'):
            # Return existing filter from session or create default.
            if req.session.has_key('enabled_versions'):
                versions = eval(req.session.get('enabled_versions'))
            else:
                versions = self.default_versions
                req.session['enabled_versions'] = str(versions)
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_versions' configuration option.
            versions = self.default_versions
        self.log.debug('enabled_versions: %s' % (versions,))
        return versions
