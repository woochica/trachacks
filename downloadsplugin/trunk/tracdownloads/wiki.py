# -*- coding: utf-8 -*-

from trac.core import *
from trac.mimeview import Context
from trac.resource import Resource
from trac.util.html import html
from trac.web.chrome import Chrome

from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

from tracdownloads.api import *

class DownloadsWiki(Component):
    """
        The wiki module implements macro for downloads referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # Macros documentation.
    downloads_count_macro_doc = """ """
    list_downloads_macro_doc = """ """

    # Configuration options
    visible_fields = ListOption('downloads', 'visible_fields',
      'id,file,description,size,time,count,author,tags,component,version,'
      'architecture,platform,type', doc = 'List of downloads table fields that'
      ' should be visible to users on Downloads section.')

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('download', self._download_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider

    def get_macros(self):
        yield 'DownloadsCount'
        yield 'ListDownloads'

    def get_macro_description(self, name):
        if name == 'DownloadsCount':
            return self.downloads_count_macro_doc
        if name == 'ListDownloads':
            return self.list_downloads_macro_doc

    def expand_macro(self, formatter, name, content):
        if name == 'DownloadsCount':
            # Create request context.
            context = Context.from_request(formatter.req)('downloads-wiki')

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get API component.
            api = self.env[DownloadsApi]

            # Check empty macro content.
            download_ids = []
            if content.strip() != '':
                # Get download IDs or filenames from content.
                items = [item.strip() for item in content.split(',')]

                # Resolve filenames to IDs.
                for item in items:
                    try:
                        # Try if it's download ID first.
                        download_id = int(item)
                        if download_id:
                            download_ids.append(download_id)
                        else:
                            # Any zero ID means all downloads.
                            download_ids = []
                            break;
                    except ValueError:
                        # If it wasn't ID resolve filename.
                        download_id = api.get_download_id_from_file(context,
                          item)
                        if download_id:
                            download_ids.append(download_id)
                        else:
                            self.log.debug('Could not resolve download filename'
                              ' to ID.')

            # Empty list mean all.
            if len(download_ids) == 0:
                download_ids = None

            # Ask for aggregated downloads count.
            self.log.debug(download_ids)
            count = api.get_number_of_downloads(context, download_ids)

            # Return simple <span> with result.
            return html.span(to_unicode(count), class_ = "downloads_count")

        elif name == 'ListDownloads':
            self.log.debug("Rendering ListDownloads macro...")

            # Determine wiki page name.
            page_name = formatter.req.path_info[6:] or 'WikiStart'

            # Create request context.
            context = Context.from_request(formatter.req)('downloads-wiki')

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get API object.
            api = self.env[DownloadsApi]

            # Get form values.
            order = context.req.args.get('order') or 'id'
            desc = context.req.args.get('desc')

            # Prepare template data.
            data = {}
            data['order'] = order
            data['desc'] = desc
            data['has_tags'] = self.env.is_component_enabled(
              'tractags.api.TagEngine')
            data['downloads'] = api.get_downloads(context, order, desc)
            data['visible_fields'] = [visible_field for visible_field in
              self.visible_fields]
            data['page_name'] = page_name

            # Return rendered template.
            return to_unicode(Chrome(self.env).render_template(formatter.req,
              'wiki-downloads-list.html', {'downloads' : data}, 'text/html',
              True))

    # Internal functions

    def _download_link(self, formatter, ns, params, label):
        if ns == 'download':
            if formatter.req.perm.has_permission('DOWNLOADS_VIEW'):
                # Create context.
                context = Context.from_request(formatter.req)('downloads-wiki')
                db = self.env.get_db_cnx()
                context.cursor = db.cursor()

                # Get API component.
                api = self.env[DownloadsApi]

                # Get download.
                if re.match(r'\d+', params): 
                    download = api.get_download(context, params)
                else:
                    download = api.get_download_by_file(context, params)

                if download:
                    if formatter.req.perm.has_permission('DOWNLOADS_VIEW',
                      Resource('downloads', download['id'])):
                        # Return link to existing file.
                        return html.a(label, href = formatter.href.downloads(
                          params), title = '%s (%s)' % (download['file'],
                          pretty_size(download['size'])))
                    else:
                        # File exists but no permission to download it.
                        html.a(label, href = '#', title = '%s (%s)' % (
                          download['file'], pretty_size(download['size'])),
                          class_ = 'missing')
                else:
                    # Return link to non-existing file.
                    return html.a(label, href = '#', title = 'File not found.',
                      class_ = 'missing')
            else:
                # Return link to file to which is no permission. 
                return html.a(label, href = '#', title = 'No permission to file.',
                   class_ = 'missing')
