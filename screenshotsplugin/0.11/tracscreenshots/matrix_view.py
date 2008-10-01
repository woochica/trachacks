# -*- coding: utf8 -*-

from trac.core import *
from trac.config import Option, IntOption
from trac.web.chrome import add_stylesheet

from tracscreenshots.api import *
from tracscreenshots.core import *

class ScreenshotsMatrixView(Component):

    implements(ITemplateProvider, IScreenshotsRenderer)

    # Configuration options.
    rows = IntOption('screenshots-matrix', 'rows', 3, 'Number of screenshot preview rows.')
    columns = IntOption('screenshots-matrix', 'columns', 3, 'Number of screenshot columns.')
    width = IntOption('screenshots-matrix', 'width', 160, 'Width of screenshot preview.')
    height = IntOption('screenshots-matrix', 'height', 120, 'Height of screenshot preview.')

    null_screenshot = {'id' : -1,
                       'name' : '',
                       'description' : ''}

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('screenshots', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IScreenshotsRenderer methods.

    def render_screenshots(self, req, data):
        # Add CSS style and JavaScript scripts.
        add_stylesheet(req, 'screenshots/css/matrix-view.css')

        # Get custom request arguments.
        index = int(req.args.get('index') or -1)
        page = int(req.args.get('page') or -1)

        self.log.debug('index: %s' % (index))
        self.log.debug('page: %s' % (page))

        # Count index or page depending on user input.
        count = len(data['screenshots'])
        count_on_page = self.rows * self.columns
        if index != -1:
            page = (index / count_on_page) + 1
        elif page != -1:
            index = (page - 1) * count_on_page
        else:
            index = 0
            page = 1

        self.log.debug('index: %s' % (index))
        self.log.debug('page: %s' % (page))

        # Compute page count, next and previous page id.
        page_cout = (count + (count_on_page - 1)) / count_on_page
        prev_index = (index - count_on_page)
        next_index = (index + count_on_page)
        max_index = page_cout * count_on_page - 1
        if prev_index < 0:
             prev_index = -1
        if next_index > max_index:
             next_index = -1

        # Fill data dictionary.
        data['rows'] = self.rows
        data['columns'] = self.columns
        data['width'] = self.width
        data['height'] = self.height
        data['matrix'] = self._build_matrix(index, data['screenshots'])
        data['index'] = index
        data['page'] = page
        data['page_count'] = page_cout
        data['prev_index'] = prev_index
        data['next_index'] = next_index
        data['screenshot_count'] = len(data['screenshots'])
        return ('screenshots-matrix-view.html', None)

    def get_screenshots_view(req):
        yield ('matrix', 'Matrix View')

    # Private methods.

    def _build_matrix(self, index, screenshots):
        # Determine index of first screenshot.
        count = self.rows * self.columns
        index = index - (index % count)

        # Construct rows x columns matrix.
        row = []
        matrix = []
        for I in xrange(count):
            # Add screenshot.
            if ((index + I) < len(screenshots)) and ((index + I) >= 0):
                row.append(screenshots[index + I])
            else:
                row.append(self.null_screenshot)

            # Move to next row.
            if ((I + 1) % self.columns) == 0:
                matrix.append(row)
                row = []

        return matrix
