# -*- coding: utf-8 -*-
#

"""
Annotation for lint results
"""

__docformat__ = 'restructuredtext en'

from trac.core import Component, implements
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.resource import Resource
from trac.web.api import IRequestFilter
from trac.web.chrome import add_stylesheet, add_ctxtnav
from trac.web.chrome import ITemplateProvider
from bitten.model import BuildConfig, Build, Report
from genshi.builder import tag
from trac.util.text import unicode_urlencode


class LintAnnotator(Component):
    """Annotation for lint results"""

    implements(IRequestFilter, IHTMLPreviewAnnotator, ITemplateProvider)

    env = log = None # filled py trac

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        """unused"""
        return handler

    def post_process_request(self, req, template, data, content_type):
        """Adds a 'Lint' context navigation menu item in source view and
           links to the annotation in report summary.
        """
        if not 'BUILD_VIEW' in req.perm:
            return template, data, content_type
        resource = data and data.get('context') \
                        and data.get('context').resource or None
        if not resource or not isinstance(resource, Resource):
            pass
        elif resource.realm == 'source' and data.get('file') \
                    and not req.args.get('annotate') == 'lint':
            add_ctxtnav(req, 'Lint',
                    title='Annotate file with lint result '
                          'data (if available)',
                    href=req.href.browser(resource.id,
                        annotate='lint', rev=data.get('rev')))

        elif resource.realm == 'build' and data.get('build', {}).get('steps'):
            # in report summary, set link to lint annotation
            steps = data['build']['steps']
            rev = data['build']['rev']
            for step in steps:
                for report in step.get('reports', []):
                    if report.get('category') != 'lint':
                        continue
                    for item in report.get('data', {}).get('data', []):
                        href = item.get('href')
                        if not href or 'annotate' in href:
                            continue
                        sep = ('?' in href) and '&' or '?'
                        param = {'rev': rev, 'annotate': 'lint'}
                        href = href + sep + unicode_urlencode(param)
                        item['href'] = href + '#Lint1'
        return template, data, content_type

    # IHTMLPreviewAnnotator methods

    def get_annotation_type(self):
        """returns: type (css class), short name, long name (tip strip)"""
        return 'lint', 'Lint', 'Lint results'

    itemid = 0

    def get_annotation_data(self, context):
        """add annotation data for lint"""

        context.perm.require('BUILD_VIEW')

        add_stylesheet(context.req, 'bitten/bitten_coverage.css')
        add_stylesheet(context.req, 'bitten/bitten_lintannotator.css')

        resource = context.resource

        # attempt to use the version passed in with the request,
        # otherwise fall back to the latest version of this file.
        try:
            version = context.req.args['rev']
        except (KeyError, TypeError):
            version = resource.version
            self.log.debug('no version passed to get_annotation_data')

        builds = Build.select(self.env, rev=version)

        self.log.debug("Looking for lint report for %s@%s [%s]..." % (
                        resource.id, str(resource.version), version))

        self.itemid = 0
        data = {}
        reports = None
        for build in builds:
            config = BuildConfig.fetch(self.env, build.config)
            if not resource.id.lstrip('/').startswith(config.path.lstrip('/')):
                self.log.debug('Skip build %s' % build)
                continue
            path_in_config = resource.id[len(config.path)+1:].lstrip('/')
            reports = Report.select(self.env, build=build.id, category='lint')
            for report in reports:
                for item in report.items:
                    if item.get('file') == path_in_config:
                        line = item.get('line')
                        if line:
                            problem = {'category': item.get('category', ''),
                                       'tag': item.get('tag', ''),
                                       'bid': build.id,
                                       'rbuild': report.build,
                                       'rstep': report.step, 'rid': report.id}
                            data.setdefault(int(line), []).append(problem)
        if data:
            self.log.debug("Lint annotate for %s@%s: %s results" % \
                (resource.id, resource.version, len(data)))
            return data
        if not builds:
            self.log.debug("No builds found")
        elif not reports:
            self.log.debug("No reports found")
        else:
            self.log.debug("No item of any report matched (%s)" % reports)
        return None

    def annotate_row(self, context, row, lineno, line, data):
        "add column with Lint data to annotation"
        if data == None:
            row.append(tag.th())
            return
        row_data = data.get(lineno, None)
        if row_data == None:
            row.append(tag.th(class_='covered'))
            return

        self.log.debug('problems in line no %d:' % lineno)
        categories = ''
        problems = []
        for item in row_data:
            categories += item['category'] and item['category'][0] or '-'
            self.log.debug('  %s' % item)
            problems.append('%(category)s: %(tag)s in report %(rid)d' % item)
        problems = '\n'.join(problems)
        self.itemid += 1
        row.append(tag.th(tag.a(categories, href='#Lint%d' % self.itemid),
                          class_='uncovered', title=problems,
                          id_='Lint%d' % self.itemid))
        self.log.debug('%s' % row)



    # ITemplateProvider methods

    def get_templates_dirs(self):
        """unused"""
        return []

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('bitten', resource_filename(__name__, 'htdocs'))]
