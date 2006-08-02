from tracscreenshots.api import *
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.util import Markup, format_datetime, TracError
import re, os, os.path, time, mimetypes

no_screenshot = {'id' : 0}

class ScreenshotsCore(Component):
    """
        The core module implements plugin's main page and mainnav button,
        provides permissions and templates.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['SCREENSHOTS_VIEW', 'SCREENSHOTS_ADMIN',]

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('screenshots', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'screenshots'

    def get_navigation_items(self, req):
        if req.perm.has_permission('SCREENSHOTS_VIEW'):
            yield 'mainnav', 'screenshots', Markup('<a href="%s">%s</a>' % \
              (self.env.href.screenshots(), self.env.config.get('screenshots',
              'title', 'Screenshots')))

    # IRequestHandler methods
    def match_request(self, req):
        if re.match(r'''^/screenshots($|/$)''', req.path_info):
            return True
        if re.match(r'''^/screenshots/.*[.](jpg|png)$''', req.path_info):
            req.args['action'] = 'get_file'
            return True
        return False

    def process_request(self, req):
        # Create API object
        api = ScreenshotsApi(self, req)

        # Get config variables
        title = self.env.config.get('screenshots', 'title', 'Screenshots')
        path = self.env.config.get('screenshots', 'path',
          '/var/lib/trac/screenshots')
        component_name = self.env.config.get('screenshots', 'component')
        version_name = self.env.config.get('screenshots', 'version')
        self.log.debug('path %s' % (path,))

        # Get action
        action = req.args.get('action')
        add = req.args.get('add')
        delete = req.args.get('delete')
        screenshot_id = int(req.args.get('id') or 0)

        # Get versions, components
        components = api.get_components()
        component_id = int(req.args.get('component') or 0)
        if component_id:
            component = self._get_component(components, component_id)
        else:
            component = self._get_component_by_name(components,
              component_name) or components[0]
        versions = api.get_versions()
        version_id = int(req.args.get('version') or 0)
        if version_id:
           version = self._get_version(versions, version_id)
        else:
           version = self._get_version_by_name(versions, version_name) \
             or versions[0]

        req.hdf['screenshots.component'] = component
        req.hdf['screenshots.components'] = components
        req.hdf['screenshots.versions'] = versions
        req.hdf['screenshots.version'] = version

        # Get image file action
        if action == 'get_file':
            # Return screenshots image action
            req.perm.assert_permission('SCREENSHOTS_VIEW')
            file = re.sub('^/screenshots', '', req.path_info)
            path = path + file
            self.log.debug('file %s' % (file,))
            self.log.debug('path %s' % (path,))
            type = mimetypes.guess_type(path)[0]
            req.send_file(path, type)
            return None, None

        # Change version and component, add or delete screenshot actions
        if action == 'change':
            req.perm.assert_permission('SCREENSHOTS_ADMIN')

            # Detect add or delete action
            if add:
                action = 'add'
            elif delete:
                # Delete screenshot
                screenshot = api.get_screenshot(screenshot_id)
                os.chdir(path)
                files = ' '.join((screenshot['large_file'],
                  screenshot['medium_file'], screenshot['small_file']))
                self.log.debug('files %s' % (files,))
                os.system('rm %s' % files)
                api.delete_screenshot(screenshot['id'])

                # Change action
                action = 'delete'
            else:
                req.perm.assert_permission('SCREENSHOTS_VIEW')

        # Submit add screenshot form action
        elif action == 'post-add':
            req.perm.assert_permission('SCREENSHOTS_ADMIN')

            # Get form values
            name = Markup(req.args.get('name'))
            description = Markup(req.args.get('description'))
            author = req.authname
            file, filename = self._get_file_from_req(req)

            # Check correct file type
            reg = re.compile(r'^(.*)[.](.*)$')
            result = reg.match(filename)
            if not result.group(2) in ('png', 'jpg'):
                raise TracError('Unsupported uploaded file type')

            # Prepare images filenames
            large_filename = re.sub(reg, r'\1_large.\2', filename)
            medium_filename = re.sub(reg, r'\1_medium.\2', filename)
            small_filename = re.sub(reg, r'\1_small.\2', filename)

            # Check files existance
            large_filepath = os.path.join(path, large_filename)
            medium_filepath = os.path.join(path, medium_filename)
            small_filepath =  os.path.join(path, small_filename)
            if os.path.exists(large_filepath) or os.path.exists(medium_filepath) \
              or os.path.exists(small_filepath):
                raise TracError('File %s already exists' % (filename))

            # Store uploaded image
            out_file = open(large_filepath, "w+")
            content = file.read()
            out_file.write(content)
            out_file.close()
            os.chdir(path)
            os.system('convert %s -resize 400!x300! %s' % (large_filename,
              medium_filename))
            os.system('convert %s -resize 120!x90! %s' % (large_filename,
              small_filename))

            # Add new screenshot
            api.add_screenshot(name, description, author, large_filename,
              medium_filename, small_filename, component['name'],
              version['name'])
        # List screenshots action
        else:
            req.perm.assert_permission('SCREENSHOTS_VIEW')

        # CSS styles
        add_stylesheet(req, 'screenshots/css/screenshots.css')

        if action != 'add':
            # Get screenshots of selected version and component
            screenshots = api.get_screenshots(component['name'], version['name'])
            if screenshot_id:
                index = self._get_screenshot_index(screenshots, screenshot_id) or 0
            else:
                index = 0
            req.hdf['screenshots.index'] = index + 1
            req.hdf['screenshots.count'] = len(screenshots)

            # Prepare displayed screenshots
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
            req.hdf['screenshots.previous'] = previous
            req.hdf['screenshots.current'] = current
            req.hdf['screenshots.next'] = next

        # Fill up HDF structure and return plugin's content
        req.hdf['screenshots.href'] = self.env.href.screenshots()
        req.hdf['screenshots.title'] = title
        del api
        if action == 'add':
            return 'screenshot-add.cs', None
        else:
            return 'screenshots.cs', None

    # Private functions

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

        # Test if file is uploaded
        if not hasattr(image, 'filename') or not image.filename:
            raise TracError('No file uploaded')
        if hasattr(image.file, 'fileno'):
            size = os.fstat(image.file.fileno())[6]
        else:
            size = image.file.len
        if size == 0:
            raise TracError('Can\'t upload empty file')

        return image.file, image.filename
