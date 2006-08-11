from tracscreenshots.api import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.util import Markup, format_datetime, TracError
import re, os, os.path, time, mimetypes

# Try import TracTagsPlugin.
try:
    from tractags.api import TagEngine
    is_tags = True
except:
    is_tags = False

no_screenshot = {'id' : 0}

class ScreenshotsCore(Component):
    """
        The core module implements plugin's main page and mainnav button,
        provides permissions and templates.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    # IPermissionRequestor methods.
    def get_permission_actions(self):
        return ['SCREENSHOTS_VIEW', 'SCREENSHOTS_ADMIN',]

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
            yield 'mainnav', 'screenshots', Markup('<a href="%s">%s</a>' % \
              (self.env.href.screenshots(), self.env.config.get('screenshots',
              'title', 'Screenshots')))

    # IRequestHandler methods.
    def match_request(self, req):
        if re.match(r'''^/screenshots($|/$)''', req.path_info):
            return True
        if re.match(r'''^/screenshots/(\d+)/(small|medium|large)$''',
          req.path_info):
            req.args['action'] = 'get_file'
            return True
        return False

    def process_request(self, req):
        self.log.debug(repr([(k,req.args.get(k)) for k in req.args.keys()]))

        # Create API object.
        self.api = ScreenshotsApi(self)

        # Get config variables.
        self.title = self.env.config.get('screenshots', 'title', 'Screenshots')
        self.path = self.env.config.get('screenshots', 'path',
          '/var/lib/trac/screenshots')
        self.component = self.env.config.get('screenshots', 'component')
        self.version = self.env.config.get('screenshots', 'version')
        self.log.debug('path: %s' % (self.path,))

        # Get current screenshot id
        self.id = int(req.args.get('id') or 0)

        # Get components and versions.
        components = self.api.get_components()
        component_id = int(req.args.get('component') or 0)
        if component_id:
            component = self._get_component(components, component_id)
        else:
            component = self._get_component_by_name(components,
              self.component) or components[0]
        versions = self.api.get_versions()
        version_id = int(req.args.get('version') or 0)
        if version_id:
            version = self._get_version(versions, version_id)
        else:
            version = self._get_version_by_name(versions, self.version) \
              or versions[0]

        self.log.debug('component_id: %s' % (component_id,))
        self.log.debug('component: %s' % (component,))
        self.log.debug('version_id: %s' % (version_id,))
        self.log.debug('version: %s' % (version,))

        # CSS styles
        add_stylesheet(req, 'screenshots/css/screenshots.css')

        # Prepare HDF structure.
        req.hdf['screenshots.component'] = component
        req.hdf['screenshots.components'] = components
        req.hdf['screenshots.versions'] = versions
        req.hdf['screenshots.version'] = version
        req.hdf['screenshots.href'] = self.env.href.screenshots()
        req.hdf['screenshots.title'] = self.title

        # Do actions and return content.
        modes = self._get_modes(req)
        self.log.debug('modes: %s' % (modes,))
        content = self._do_actions(req, modes, component, version)
        del self.api
        return content

    # Private functions.

    def _get_modes(self, req):
        action = req.args.get('action')
        self.log.debug('action: %s' % (action,))
        if action == 'get_file':
            return ['get-file']
        elif action == 'add':
            return ['add', 'add-display']
        elif action == 'post-add':
            return ['post-add', 'display']
        elif action == 'edit':
            return ['edit', 'add-display']
        elif action == 'post-edit':
            return ['post-edit', 'display']
        elif action == 'delete':
            return ['delete', 'display']
        else:
            return ['display']

    def _do_actions(self, req, modes, component, version):
        for mode in modes:
            if mode == 'get-file':
                req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Get screenshot
                match = re.match(r'''^/screenshots/(\d+)/(small|medium|large)$''',
                  req.path_info)
                if match:
                    id = match.group(1)
                    size = match.group(2)
                screenshot = self.api.get_screenshot(id)

                # Return screenshots image action.
                file = screenshot['%s_file' % (size,)]
                path = os.path.join(self.path, str(screenshot['id']), file)
                self.log.debug('file: %s' % (file,))
                self.log.debug('path: %s' % (path,))
                type = mimetypes.guess_type(path)[0]
                req.send_file(path, type)

            elif mode == 'add':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

            elif mode == 'post-add':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get form values.
                name = Markup(req.args.get('name'))
                description = Markup(req.args.get('description'))
                author = req.authname
                file, filename = self._get_file_from_req(req)
                content = file.read()

                # Check correct file type.
                reg = re.compile(r'^(.*)[.](.*)$')
                result = reg.match(filename)
                if not result.group(2) in ('png', 'jpg'):
                    raise TracError('Unsupported uploaded file type')

                # Prepare images filenames.
                large_filename = re.sub(reg, r'\1_large.\2', filename)
                medium_filename = re.sub(reg, r'\1_medium.\2', filename)
                small_filename = re.sub(reg, r'\1_small.\2', filename)

                # Add new screenshot.
                screenshot_time = int(time.time())
                self.api.add_screenshot(name, description, screenshot_time,
                  author, large_filename, medium_filename, small_filename,
                  component['name'], version['name'])

                # Get inserted screenshot.
                screenshot = self.api.get_screenshot_by_time(screenshot_time)
                self.id = screenshot['id']

                # Create screenshot tags.
                if is_tags:
                    tags = TagEngine(self.env).tagspace.screenshots
                    tags.add_tags(req, screenshot['id'], [screenshot['name'],
                      screenshot['author'], screenshot['component'],
                      screenshot['version']])

                # Prepare file paths
                path = os.path.join(self.path, str(self.id))
                large_filepath = os.path.join(path, large_filename)
                medium_filepath = os.path.join(path, medium_filename)
                small_filepath =  os.path.join(path, small_filename)
                self.log.debug('large_filepath: %s' % (large_filepath,))
                self.log.debug('medium_filepath: %s' % (medium_filepath,))
                self.log.debug('small_filepath: %s' % (small_filepath,))

                # Store uploaded image.
                try:
                    os.mkdir(path)
                    out_file = open(large_filepath, "w+")
                    out_file.write(content)
                    out_file.close()
                    os.chdir(path)
                    os.system('convert "%s" -resize 400!x300! "%s"' % (
                      large_filename, medium_filename))
                    os.system('convert "%s" -resize 120!x90! "%s"' % (
                      large_filename, small_filename))
                except:
                    raise TracError('Error storing file')

            elif mode == 'edit':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

            elif mode == 'post-edit':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get form values.
                name = Markup(req.args.get('name'))
                description = Markup(req.args.get('description'))

                # Get old screenshot
                screenshot = self.api.get_screenshot(self.id)

                # Update screenshot tags.
                if is_tags:
                    tags = TagEngine(self.env).tagspace.screenshots
                    tags.replace_tags(req, screenshot['id'], [name,
                      screenshot['author'], component['name'], version['name']])

                # Edit screenshot.
                self.api.edit_screenshot(screenshot['id'], name, description,
                  component['name'], version['name'])

            elif mode == 'delete':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get screenshots
                screenshots = self.api.get_screenshots(component['name'],
                  version['name'])
                index = self._get_screenshot_index(screenshots, self.id) or 0
                screenshot = self.api.get_screenshot(self.id)

                # Delete screenshot.
                try:
                    self.api.delete_screenshot(self.id)
                    path = os.path.join(self.path, str(self.id))
                    os.remove(os.path.join(path, screenshot['large_file']))
                    os.remove(os.path.join(path, screenshot['medium_file']))
                    os.remove(os.path.join(path, screenshot['small_file']))
                    os.rmdir(path)
                except:
                    pass

                # Delete screenshot tags.
                if is_tags:
                    tags = TagEngine(self.env).tagspace.screenshots
                    tags.remove_tags(req, screenshot['id'],
                      [screenshot['name'], screenshot['author'],
                      component['name'], version['name']])

                # Set new screenshot id.
                if index > 1:
                    self.id = screenshots[index - 1]['id']
                else:
                    self.id = screenshots[0]['id']

            elif mode == 'display':
                req.perm.assert_permission('SCREENSHOTS_VIEW')

                # Get screenshots of selected version and component.
                screenshots = self.api.get_screenshots(component['name'],
                  version['name'])
                index = self._get_screenshot_index(screenshots, self.id) or 0

                # Prepare displayed screenshots.
                lenght = len(screenshots)
                previous = []
                current = []
                next = []
                if lenght > 0:
                    current.append(screenshots[index])
                if (index + 1) < lenght:
                    next.append(screenshots[index + 1])
                else:
                    next.append(no_screenshot)
                if (index + 2) < lenght:
                    next.append(screenshots[index + 2])
                else:
                    next.append(no_screenshot)
                if (index - 1) > 0:
                    previous.append(screenshots[index - 2])
                else:
                    previous.append(no_screenshot)
                if (index) > 0:
                    previous.append(screenshots[index - 1])
                else:
                    previous.append(no_screenshot)

                # Fill HDF structure
                req.hdf['screenshots.index'] = index + 1
                req.hdf['screenshots.count'] = len(screenshots)
                req.hdf['screenshots.previous'] = previous
                req.hdf['screenshots.current'] = current
                req.hdf['screenshots.next'] = next

                return 'screenshots.cs', None

            elif mode == 'add-display':
                req.perm.assert_permission('SCREENSHOTS_ADMIN')

                # Get screenshot
                screenshot = self.api.get_screenshot(self.id)

                # Fill HDF structure
                req.hdf['screenshots.current'] = [screenshot]

                return 'screenshot-add.cs', None

    def _get_screenshot_index(self, screenshots, id):
        index = 0
        for screenshot in screenshots:
            if screenshot['id'] == id:
                return index
            index = index + 1

    def _get_component(self, components, id):
        for component in components:
            if component['id'] == id:
                return component

    def _get_component_by_name(self, components, name):
        for component in components:
            if component['name'] == name:
                return component

    def _get_version(self, versions, id):
        for version in versions:
            if version['id'] == id:
                return version

    def _get_version_by_name(self, versions, name):
        for version in versions:
            if version['name'] == name:
                return version

    def _get_file_from_req(self, req):
        image = req.args['image']

        # Test if file is uploaded.
        if not hasattr(image, 'filename') or not image.filename:
            raise TracError('No file uploaded')
        if hasattr(image.file, 'fileno'):
            size = os.fstat(image.file.fileno())[6]
        else:
            size = image.file.len
        if size == 0:
            raise TracError('Can\'t upload empty file')

        return image.file, image.filename
