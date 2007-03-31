# Helloworld plugin

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web import IRequestHandler, IRequestFilter
from trac.util import escape, Markup

class UserbaseModule(Component):
    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, content_type):
        if (req.hdf.has_key('title')):
            self.store_trail(req)
            
        return template, content_type


    def store_trail(self, req):
        titles = []
        urls = []
        infos = []
        session = req.session

        if (session.has_key('trail.titles')):
            titles = session['trail.titles'].split('|')
            urls = session['trail.urls'].split('|')
            infos = session['trail.infos'].split('|')

        relevant = None

        if (req.hdf.has_key('title')):
            relevant = self.get_trail_relevant(req.hdf['title'], req.path_info)

        if (relevant == None and (req.path_info == '/' or req.path_info == '' or req.path_info == None)):
            relevant = 'Wiki', 'Wiki'
             

        if (relevant != None):

            currentTitle = relevant[0]
            currentInfo = relevant[1]

            if (currentTitle == ''):
                currentTitle = 'Wiki'
                currentInfo = 'Wiki'

            if (len(titles) > 0 and titles[len(titles) - 1] != currentTitle):
                if (len(titles) > 9):
                    titles = titles[len(titles)-9:]
                    urls = urls[len(urls)-9:]
                    infos = infos[len(infos)-9:]

                titles.append(currentTitle)
                infos.append(currentInfo)
                urls.append(req.base_path + req.path_info)

            # store values
            value = ''

            for entry in titles:
                value = value + entry + '|'

            session['trail.titles'] = value[0:len(value) - 1]

            value = ''

            for entry in urls:
                value = value + entry + '|'

            session['trail.urls'] = value[0:len(value) - 1]

            value = ''

            for entry in infos:
                value = value + entry + '|'

            session['trail.infos'] = value[0:len(value) - 1]

        i = 0;
        tuples = []

        while (i < len(titles)):
          tuple = (titles[i],urls[i],infos[i])
          tuples.append(tuple)
          i = i + 1

        req.hdf['trail'] = tuples
        req.hdf['path_info'] = req.path_info
        

    def get_trail_relevant(self, title, path):

         if (path.startswith('/wiki') or path == '/'):
            return title, title

         if (path.startswith('/milestone')):
            return path[11:], title

         if (path.startswith('/report/')):
            return '{' + path[8:] + '}', title

         if (path.startswith('/ticket/')):
            return '#' + path[8:], title

         if (path.startswith('/changeset/')):
            return '[' + path[11:] + ']', title

         return None