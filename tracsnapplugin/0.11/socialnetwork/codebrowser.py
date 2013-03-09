# Ainsley Lawson.  ainsley.lawson@utoronto.ca
# Sarah Strong. sarah.e.strong@gmail.com
# August 2009

from genshi import HTML


def get_css(self, req):
    css = HTML("""
    <style type="text/css">
    h2 {
        background: #aaaaaa;
        color: #ffffff;
        border-bottom: 1px solid #888888;
        margin: 0;
        padding: 5px;
    }
    #relatedModules{
        margin: 5px;
        margin-bottom:20px;
        width: 400px;
        float: left;
        background: #dddddd;
        border: 1px solid #888888;
        padding: 0;
    }
    #experts{
        margin: 5px;
        margin-bottom:20px;
        width: 400px;
        float: left;
        background: #dddddd;
        border: 1px solid #888888;
        padding: 0;
    }
    </style>
    """)

    return css


def related_files_html(self, req):
    """
    Inserts a box into code browsing pages that lists other files that are
    related to the file you are browsing
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get the path of the current file
    this_file = (req.path_info)[9:]

    # Get related modules
    cursor.execute('SELECT file1, file2, strength \
                    FROM code_relations \
                    WHERE file1 = %s OR file2 = %s \
                    ORDER BY strength DESC',
                   (this_file, this_file,))

    # The HTML to be inserted into the code browsing page
    html = '<div id="relatedModules"><h2>Related Modules (tracSNAP)</h2><ul>'

    # Create the links to the related files
    for file1, file2, strength in cursor:
        if file2 == this_file:
            file1, file2 = file2, file1
        html += '<li><a href="' + req.base_path + \
                "/browser/" + file2 + '">' + file2 + "</a></li>"

    # Check to make sure there were actually some related files
    if not html.endswith("</li>"):
        return ""

    html += "</ul></div>"
    html = HTML(html)

    return html


def experts_html(self, req):
    """
    Inserts a box into code browsing pages that lists expert colleagues of
    the file you are currently browsing.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get the path of the current file
    this_file = (req.path_info)[9:]

    # Get the experts
    cursor.execute('SELECT author, strength \
                    FROM expertise \
                    WHERE path = %s \
                    AND author != %s \
                    ORDER BY strength DESC',
                   (this_file, req.authname,))

    # The HTML to be insterted into the code browsing page
    html = '<div id="experts"><h2>Experts (tracSNAP)</h2><ul>'

    # Create the HTML list of experts
    for author, strength in cursor:
        html += '<li><a href="' + req.base_path + \
                '/sn_linkto?linkto=' + author + \
                '">' + author + "</a>, \
                (expert score = " + str(strength) + ")</li>"

    # Make sure experts actually exist
    if not html.endswith("</li>"):
        return ""

    html += "</ul></div>"
    html = HTML(html)

    return html

