# -*- coding: utf8 -*-

import sets, re, os, os.path, time, mimetypes, Image

from trac.core import *
from trac.config import Option
from trac.web.main import populate_hdf
from trac.web.chrome import Chrome, add_stylesheet
from trac.web.clearsilver import HDFWrapper
from trac.util import Markup, format_datetime, TracError
from trac.util.html import html

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

    # Configuration options.
    title = Option('screenshots', 'title', 'Screenshots',
      'Main navigation bar button title.')
    path = Option('screenshots', 'path', '/var/lib/trac/screenshots',
      'Path where to store uploaded screenshots.')
    ext = Option('screenshots', 'ext', 'jpg png',
      'List of screenshot file extensions that can be uploaded. Must be'
      ' supported by ImageMagick.')
    formats = Option('screenshots', 'formats', 'raw html jpg png',
      'List of allowed formats for screenshot download.')
    default_format = Option('screenshots', 'default_format', 'html',
      'Default format for screenshot download links.')
    component = Option('screenshots', 'component', '',
      'Name of default component.')
    version = Option('screenshots', 'version', '',
      'Name of default version.')
    show_name = Option('screenshots', 'show_name', True,
      'Option to disable display of screenshot name and author.')

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        return ['SCREENSHOTS_VIEW', 'SCREENSHOTS_FILTER', 'SCREENSHOTS_ADMIN']

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
            yield 'mainnav', 'screenshots', html.a(self.title,
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

        # Prepare HDF structure and return template.
        req.hdf['screenshots'] = data
        req.hdf['screenshots.href'] = req.href.screenshots()
        req.hdf['screenshots.title'] = self.title
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
                if not format in self.formats.split(' '):
                    raise TracError('Requested screenshot format that is not allowed.',
                      'Requested format not allowed.')

                # Get screenshot.
                screenshot = api.get_screenshot(cursor, screenshot_id)

                if screenshot:
                    # Set missing dimensions.
                    width = width or screenshot['width']
                    height = height or screenshot['height']

                    if format == 'html':
                        # Prepare data dictionary.
                        data['screenshot'] = screenshot

                        # Return screenshot template and data.
                        return ('screenshot.cs', data, None)

                    else:
                        # Prepare screenshot filename.
                        name, ext = os.path.splitext(screenshot['file'])
                        format = (format == 'raw') and ext or '.' + format
                        path = os.path.join(self.path, unicode(screenshot['id']))
                        file_name = os.path.join(path, '%s-%sx%s%s' % (name, width,
                          height, format))
                        orig_name = os.path.join(path, '%s-%sx%s%s' % (name,
                          screenshot['width'], screenshot['height'], ext))
                        self.log.debug('filemame: %s' % (file_name,))

                        # Send file to request.
                        if not os.path.exists(file_name):
                            self._create_image(orig_name, path, name, format,
                              width, height)

                        req.send_header('Content-Disposition',
                          'attachment;filename=%s' % (os.path.basename(file_name)))
                        req.send_header('Content-Description',
                          screenshot['description'])
                        req.send_file(file_name, mimetypes.guess_type(file_name)[0])
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
                file, file_name = self._get_file_from_req(req)
                name, ext = os.path.splitext(file_name)
                file_name = name + ext.lower()

                # Check correct file type.
                reg = re.compile(r'^(.*)[.](.*)$')
                result = reg.match(file_name)
                if result:
                    if not result.group(2).lower() in self.ext.split(' '):
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
                              'file' : file_name,
                              'width' : image.size[0],
                              'height' : image.size[1]}

                # Add new screenshot.
                api.add_screenshot(cursor, screenshot)

                # Get inserted screenshot to with new id.
                screenshot = api.get_screenshot_by_time(cursor,
                   screenshot['time'])

                # Add components to screenshot.
                components = req.args.get('components')
                if not isinstance(components, list):
                     components = [components]
                for component in components:
                    component = {'screenshot' : screenshot['id'],
                                 'component' : component}
                    api.add_component(cursor, component)
                screenshot['components'] = components

                # Add versions to screenshots
                versions = req.args.get('versions')
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
                file_name = os.path.join(path, '%s-%ix%i.%s' % (result.group(1),
                  screenshot['width'], screenshot['height'], result.group(2)))
                file_name = file_name.encode('utf-8')
                self.log.debug('file_name: %s' % (file_name,))

                # Store uploaded image.
                try:
                    os.mkdir(path)
                    image.save(file_name)
                except:	
                    api.delete_screenshot(cursor, screenshot['id'])
                    try:
                        os.remove(file_name)
                        os.rmdir(path)
                    except:
                        pass
                    raise TracError('Error storing file. Is directory specified' \
                      ' in path config option in [screenshots] section of' \
                      ' trac.ini existing?')

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

                if old_screenshot:
                    # Construct screenshot dictionary from form values.
                    screenshot = {'name' :  req.args.get('name'),
                                  'description' : req.args.get('description'),
                                  'author' : req.authname,
                                  'tags' : req.args.get('tags'),
                                  'components' : req.args.get('components'),
                                  'versions' : req.args.get('versions')}

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

                else:
                    raise TracError('Edited screenshot not found.',
                      'Screenshot not found.')

            elif action == 'delete':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get screenshot.
                screenshot = api.get_screenshot(cursor, req.args.get('id'))

                try:
                    # Delete screenshot.
                    api.delete_screenshot(cursor, screenshot['id'])

                    # Delete screenshot files. Don't append any other files there :-).
                    path = os.path.join(self.path, unicode(screenshot['id']))
                    for file in os.listdir(path):
                        file = os.path.join(path, file)
                        os.remove(file)
                    os.rmdir(path)
                except:
                    pass

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_deleted(screenshot)


                # Clear id to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'view':
                req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Check that at least one IScreenshotsRenderer is enabled
                if len(self.renderers) == 0:
                    raise TracError('No screenshots renderer enabled. Enable at least one.',
                      'No screenshots renderer enabled')

                # Fill data dictionary.
                data['id'] = int(req.args.get('id') or 0)
                data['versions'] = api.get_versions(cursor)
                data['components'] = api.get_components(cursor)
                data['screenshots'] = api.get_screenshots(cursor)
                data['href'] = req.href.screenshots()

                # Get screenshots content template and data.
                template, data, content_type = self.renderers[0]. \
                  render_screenshots(req, data)

                # Prepare HDF structure.
                chrome = Chrome(self.env)
                hdf = HDFWrapper(chrome.get_all_templates_dirs())
                populate_hdf(hdf, self.env, req)

                # Fixing bug in Trac 0.10.
                for action in req.perm.permissions():
                    hdf['trac.acl.' + action] = True

                # Fill HDF with screenshots data.
                hdf['screenshots'] = data

                # Return main template.
                data['content'] = Markup(hdf.render(template))
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
        file_name = os.path.basename(image.filename).decode('utf-8')
        self.log.debug(filename)
        return image.file, file_name
