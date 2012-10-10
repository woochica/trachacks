# -*- coding: utf-8 -*-

from __future__ import generators

# Track includes
from trac.core import *
from trac.wiki import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.util.text import to_unicode

from pickle import *

class VisitCounterMacro(Component):
    """
Macro displays how many times was wiki page displayed.

This macro accepts up to tree parameters. First parameter is wiki page
name which visit count you want to display. If no parameters specified
current page visit count is displayed. Second parameter determines if
displaying of macro should update specified page visit count. Accepted values
of this parameter are: True, False, true, false, 1, 0. Default value is true.
Third parameter specifies number of digits for visit count display. If its
value is 0 then visit count is displayed as simple text. Default value is 4.

Examples:

{{{
 [[VisitCounter(WikiStart)]]
 [[VisitCounter(WikiStart, True)]]
 [[VisitCounter(WikiStart, True, 3)]]
}}}
    """

    implements(IWikiMacroProvider, ITemplateProvider)

    #
    # Public methods
    #

    # ITemplateProvider methods

    """
      Returns additional path where stylesheets are placed.
    """
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('visitcounter', resource_filename(__name__, 'htdocs'))]

    """
      Returns additional path where templates are placed.
    """
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IWikiMacroProvider

    """
      Returns list of provided macro names.
    """
    def get_macros(self):
        yield 'VisitCounter'

    """
      Returns documentation for provided macros.
    """
    def get_macro_description(self, name):
        if name == 'VisitCounter':
            return self.__doc__
            #return inspect.getdoc(self._load_macro(name))
        else:
            return ""

    """
      Returns macro content.
    """
    def render_macro(self, req, name, content):
        if name == 'VisitCounter':
            # Get config values or its default values.
            expires = int(self.config.get('visitcounter', 'expires') or 0)

            # Get access to database
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Add CSS stylesheet
            add_stylesheet(req, 'visitcounter/css/visitcounter.css')

            # Get macro arguments.
	    if content:
                args = content.split(',')
	    else:
	        args = []
            argc = len(args)
            for I in xrange(argc):
                args[I] = args[I].strip()

            # Check right arguments count.
            if argc > 3:
                raise TracError('VisitCounter macro take at most 3 arguments')

            # Get argument values
            if argc >=1:
                page = args[0]
            else:
                page = req.path_info[6:] or 'WikiStart'
            if argc >= 2:
                update = args[1] in ('True', 'true', '1')
            else:
                update = True
            if argc >= 3:
                digits = int(args[2])
            else:
                digits = 4

            # Getting page visit count.
            count = self._get_count(cursor, page)

            # Check if should update visit count.
            if update:
                # Getting list of visited page
                if req.session.has_key('visited-pages'):
                    visited = req.session.get('visited-pages').split('|')
                else:
                    visited = []

                if not (page in visited):
                    # Update count;
                    count = count + 1
                    self._set_count(cursor, page, count)

                    # Update cookie.
                    visited.append(page)
                    req.session['visited-pages'] = '|'.join(visited)
                    req.session.bake_cookie(expires)

            # Set template values and return rendered macro
            db.commit()
            req.hdf['visitcounter.count'] = count
            req.hdf['visitcounter.show_digits'] = digits > 0
            req.hdf['visitcounter.digits'] = self._get_digits(count, digits)
            return to_unicode(req.hdf.render('visitcounter.cs'))
        else:
            raise TracError('Not implemented macro %s' % (name))

    #
    # Private methods
    #

    def _get_digits(self, number, digit_count):
        digits = str(number)
        digits = digits.rjust(digit_count, '0')
        digits = list(digits)
        return digits

    def _get_count(self, cursor, page):
        sql = 'SELECT count FROM visit WHERE page = "%s"' % (page)
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            return row[0]
        return 0

    def _set_count(self, cursor, page, count):
        sql = 'SELECT count FROM visit WHERE page = "%s"' % (page)
        self.log.debug(sql)
        is_in_db = False
        for row in cursor:
            is_in_db = True
        if is_in_db:
            sql = 'UPDATE visit SET count = %s WHERE page = "%s"' % (count,
              page)
        else:
            sql = 'INSERT INTO visit (page, count) VALUES ("%s", %s)' % \
              (page, count)
        self.log.debug(sql)
        cursor.execute(sql)
