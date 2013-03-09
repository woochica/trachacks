# Ainsley Lawson.  ainsley.lawson@utoronto.ca
# August 2009

from genshi import HTML


def format_relations_for_flare(self, r_dict):
    """
    Takes a dictionary of relations and returns the HTML for the
    data in json format (for Flare to visualize)
    """

    #TODO:  Strength is always set to 1 at the moment, since I haven't
    #		figured out how to show edge weights yet in Flare.

    html = '['
    for file1 in r_dict:
        if r_dict[file1] == []:
            html += '{"name":"sn/' + file1 + '","strength":1,"links":[]},'
            continue
        html += '{"name":"sn/' + file1 + '","strength":1,"links":['
        for link in r_dict[file1]:
            html += '"sn/' + link + '",'
        html = html[0:len(html) - 1] + ']},'
    html = html[0:len(html) - 1] + ']'
    if html == ']':
        html = '[]'

    data = HTML(html)
    return data


def get_my_files_data(self, person, depth):
    """
    Returns the HTML for a data file that Flare uses to construct the graph
    of the my file relations.
    """
    db = self.env.get_db_cnx()
    cursor = db.cursor()

    q, relations, dist = [], [], {}

    # Get the files the person has worked on
    cursor.execute('SELECT DISTINCT path \
                    FROM node_change n, revision r \
                    WHERE n.rev = r.rev \
                    AND r.author = %s',
                   (person,))
    for row in cursor:
        q.append(row[0])
        dist[row[0]] = 0

    while len(q) != 0:

        # Grab a file from the queue and get its related files
        current = q[0]
        q.remove(current)
        cursor.execute('SELECT file1, file2 \
                        FROM code_relations \
                        WHERE file1 = %s \
                        OR file2 = %s',
                       (current, current,))

        # Examine each file neighbouring node 'current'
        for file1, file2 in cursor:
            if file1 == current:
                file1, file2 = file2, file1

            # Calculate distance from root node(s)
            if (file1 not in dist):
                dist[file1] = dist[current] + 1

                # Add file to queue if necessary
                if dist[file1] <= depth:
                    q.append(file1)

            # Record the relation
            if ((current, file1) not in relations) \
                and ((file1, current) not in relations) \
                and (dist[file1] <= depth):
                relations.append((current, file1))

                # end for
        # end while

    db.close()

    # Set up a dictionary of the relations
    r_dict = {}
    for file1, file2 in relations:
        if file2 not in r_dict:
            r_dict[file2] = []
        if file1 in r_dict:
            r_dict[file1].append(file2)
        else:
            r_dict[file1] = [file2]

    # Format data for Flare
    data = format_relations_for_flare(self, r_dict)

    return data


def get_overall_files_data(self):
    """
    Returns the HTML for a data file that Flare uses to construct the graph
    of the overall file relations.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get all the file relations
    cursor.execute('SELECT file1, file2 \
                    FROM code_relations')

    # Set up a dictionary of the relations
    r_dict = {}
    for file1, file2 in cursor:
        file1 = file1[0: file1.rfind('/')] + '/*'
        file2 = file2[0: file2.rfind('/')] + '/*'
        if file1 != file2:
            if file2 not in r_dict:
                r_dict[file2] = []
            if file1 in r_dict:
                if file2 not in r_dict[file1]:
                    r_dict[file1].append(file2)
            else:
                r_dict[file1] = [file2]

    db.close()

    # Format data for Flare
    data = format_relations_for_flare(self, r_dict)

    return data


def get_subdirs_files_data(self, subdirs):
    """
    Returns the HTML for a data file that Flare uses to construct the graph
    of the specified file relations.  subdirs is a list of directories.
    Only relations between files in the specified directories (and their
    child directories) are included.
    """

    relations = []
    subdirs.sort()

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get the relevant file relations
    for i in range(0, len(subdirs)):
        dir1 = subdirs[i]

        for j in range(i, len(subdirs)):
            dir2 = subdirs[j]
            cursor.execute('SELECT file1, file2 \
                            FROM code_relations \
                            WHERE (file1 LIKE "' + dir1 + '%" \
                            AND file2 LIKE "' + dir2 + '%")')
            for file1, file2 in cursor:
                if file1 != file2:
                    relations.append((file1, file2))

    # Set up a dictionary of the relations
    r_dict = {}
    for file1, file2 in relations:
        if file2 not in r_dict:
            r_dict[file2] = []
        if file1 in r_dict:
            r_dict[file1].append(file2)
        else:
            r_dict[file1] = [file2]

    # Format data for Flare
    data = format_relations_for_flare(self, r_dict)

    db.close()

    return data


def get_my_social_data(self, me, depth):
    """
    Returns the HTML for a data file that Flare uses to construct the graph
    of the my social relations.
    """
    db = self.env.get_db_cnx()
    cursor = db.cursor()

    q, relations, dist = [], [], {}

    q.append(me)
    dist[me] = 0

    while len(q) != 0:

        # Grab a person from the queue and get its related people
        current = q[0]
        q.remove(current)
        cursor.execute('SELECT person1, person2 \
                        FROM social_relations \
                        WHERE person1 = %s \
                        OR person2 = %s',
                       (current, current,))

        # Examine each person neighbouring node 'current'
        for person1, person2 in cursor:
            if person1 == current:
                person1, person2 = person2, person1

            # Calculate distance from root node(s)
            if (person1 not in dist):
                dist[person1] = dist[current] + 1

                # Add file to queue if necessary
                if dist[person1] <= depth:
                    q.append(person1)

            # Record the relation
            if ((current, person1) not in relations) \
                and ((person1, current) not in relations) \
                and (dist[person1] <= depth):
                relations.append((current, person1))

                # end for
        # end while

    db.close()

    # Set up a dictionary of the relations
    r_dict = {}
    for person1, person2 in relations:
        if person2 not in r_dict:
            r_dict[person2] = []
        if person1 in r_dict:
            r_dict[person1].append(person2)
        else:
            r_dict[person1] = [person2]

    # Format data for Flare
    data = format_relations_for_flare(self, r_dict)

    return data


def get_overall_social_data(self):
    """
    Returns the HTML for a data file that Flare uses to construct the graph
    of the overall social relations.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get all social relations
    cursor.execute('SELECT person1, person2, strength \
                    FROM social_relations')
    r_dict = {}

    # Set up a dictionary of the relations
    for person1, person2, strength in cursor:
        if person2 not in r_dict:
            r_dict[person2] = []
        if person1 in r_dict:
            r_dict[person1].append(person2)
        else:
            r_dict[person1] = [person2]

    # Format data for Flare
    data = format_relations_for_flare(self, r_dict)

    db.close()

    return (data)


def get_correction_dropdown(self, person):
    """
    Return the HTML for the options of a dropdown list of people
    that person does not talk to.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    all_people, spoken_to = [], [person]

    # Get all the people
    cursor.execute("SELECT DISTINCT author FROM revision \
                    UNION \
                    SELECT DISTINCT reporter FROM ticket \
                    UNION \
                    SELECT DISTINCT author FROM ticket_change")
    for row in cursor:
        all_people.append(row[0])

    # Get the people that person talks to
    cursor.execute('SELECT DISTINCT person1 \
                    FROM social_relations \
                    WHERE person2 = %s',
                   (person,))
    for row in cursor:
        spoken_to.append(row[0])

    cursor.execute('SELECT DISTINCT person2 \
                    FROM social_relations \
                    WHERE person1 = %s',
                   (person,))
    for row in cursor:
        spoken_to.append(row[0])

    # Subtract to get the people that person doesn't talk to
    all_people = set(all_people)
    spoken_to = set(spoken_to)
    not_spoken_to = all_people.difference(spoken_to)

    # Format as HTML dropdown list options
    drop_down = ""
    for p in not_spoken_to:
        drop_down += '<option value="' + p + '">' + p + '</option>'

    return HTML(drop_down)


def get_my_linkto(self, me, them):
    '''
    Returns the HTML for a data file that Flare uses to construct a graph
    of the shortest path of social connections between person 'me' and
    person 'them'.  If there is no path, then the data file is empty.
    '''

    # Make sure that people have been specified
    if me == "" or them == "":
        return HTML("[]")

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get all the social relations
    cursor.execute("SELECT person1, person2 \
                    FROM social_relations")

    # Get a list of all people who have communicated
    all_nodes = []
    for person1, person2 in cursor:
        all_nodes.append(person1)
        all_nodes.append(person2)
    all_nodes = list(set(all_nodes))

    # Make sure that 'me' and 'them' have had social communication
    if (me not in all_nodes) or (them not in all_nodes):
        return HTML("[]")

    dist = {}    # dist[p] = distance in tree from 'me' to 'p'
    prev = {}    # prev[p] = parent of person in the path from 'me' to 'p'


    # Find shortest path from 'me' to 'them' using Dijkstra's algorithm
    # http://en.wikipedia.org/wiki/Dijkstra%27s_algorithm#Pseudocode

    # Initialize variables
    for node in all_nodes:
        dist[node] = None
        prev[node] = None
    dist[me] = 0
    q = all_nodes

    while len(q) != 0:

        # Get the node in q with smalled dist[]
        smallest = q[0]
        for node in q:
            if dist[smallest] == None and dist[node] != None:
                smallest = node
            elif (dist[smallest] != None and dist[node] != None
                  and dist[node] < dist[smallest]):
                smallest = node

        # Check if 'me' has no social connection to 'them'
        if dist[smallest] == None:
            break

        # Remove smallest from q
        q.remove(smallest)

        # Get the neighbours of smallest that are still in the q
        neighbours = []
        cursor.execute("SELECT person1, person2 \
                        FROM social_relations \
                        WHERE person1 = %s \
                        OR person2 = %s",
                       (smallest, smallest,))
        for person1, person2 in cursor:
            if person1 == smallest and person2 in q:
                neighbours.append(person2)
            elif person2 == smallest and person1 in q:
                neighbours.append(person1)

        # Update distances and parent nodes
        for node in neighbours:
            alt = dist[smallest] + 1
            if dist[node] == None or alt < dist[node]:
                dist[node] = alt
                prev[node] = smallest

    # end while

    db.close()

    # Get all the people in the path from 'me' to 'them'
    r_dict = {}
    current = them
    while current != me:
        r_dict[current] = [prev[current]]
        current = prev[current]
    r_dict[me] = []

    # Format data for Flare
    data = format_relations_for_flare(self, r_dict)

    return data


def get_recent_files(self, author, base_path):
    '''
    Get the HTML for a list of author's most recent files.
    base_path should be the link to the trac environment, so that
    the list can include links to the files.
    '''

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get author's recent files
    cursor.execute('SELECT nc.path, r.time \
                    FROM node_change nc, revision r\
                    WHERE r.author=%s \
                    AND nc.rev = r.rev \
                    AND nc.node_type="F" \
                    ORDER BY r.time DESC',
                   (author,))

    html = '<ul>'        # HTML for the list
    num_recent = 0        # Number of files in the list

    # Construct the list
    for path, time in cursor:

        # Maximum of 10 files in the list
        num_recent += 1
        if num_recent > 10:
            break

        # Link to the file
        html += '<li><a href="' + base_path + '/browser/' + path + '">' + \
                path + '</a></li>'

    html += '</ul>'

    return HTML(html)


def determine_directory_structure(self, repo):
    """
    Return a dictionary where each entry is the form
    ( directory : [list of sub-directories] ).  The directory is the
    full path of the directory, and each item in the value list is a name
    of a direct sub-directory. 	For example, if the directories are:
        d1, d2, d1/d1a, d1/d1b, d1/d1a/d1aa
    the dictionary would have the following entries:
        { "":["d1", "d2"], "d1":["d1a", "d1b"], "d2":[],
          "d1/d1a":["d1aa"], "d1/d1b":[], "d1/d1a/d1aa":[] }
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get all the directories
    cursor.execute('SELECT DISTINCT path \
                    FROM node_change \
                    WHERE node_type = "D"')

    # Construct the directory dictionary
    # directory_dict[d] = [list of d's subdirectories]
    directory_dict = {}
    for (path,) in cursor:
        ind = path.rfind('/')
        directory = path[0:ind]

        if ind == -1:
            directory = ""
        if path not in directory_dict:
            directory_dict[path] = []
        if directory in directory_dict:
            directory_dict[directory].append(path)
        else:
            directory_dict[directory] = [path]
    db.close()

    return directory_dict


def process_structure(self, directory, directory_dict, indent):
    """
    Construct the HTML for the options of a drop-down list of the
    directory structure.
    - directory is the directory you want to start the structure from
      ("" if you want to start from the root)
    - directory_dict is as the output from determine_directory_structure().
    - indent is the string of blank characters that should preceed this
      option in the dropdown list (pass in "" to start)
    """

    # Get the last token in the path to the directory
    if directory == "":
        this_dir = ""
    else:
        ind = directory.rfind('/')
        this_dir = directory[ind + 1:]

    # Add this directory to the result
    result = ''
    if this_dir != "":
        result = '<option value="' + directory + '">' + indent + \
                 ' |- ' + this_dir + '</option>'

    # Process this directory's subdirectories
    sub_directories = directory_dict[directory]
    indent += '&nbsp&nbsp&nbsp'
    for sub in sub_directories:
        result += process_structure(self, sub, directory_dict, indent)

    return result


def get_directory_list(self, repo):
    """
    Returns the HTML for a form to select directories, and pass them as
    query args to sn_overall_files page.  repo is the svn repository.
    """

    # Get the directory dictionary
    dd = determine_directory_structure(self, repo)

    # Construct the HTML
    html = '\
    <form method="GET" action="sn_overall_files"> \
    <center>\
      <table> \
        <tr> \
          <td width=200> \
            Select directories you wish to examine \
            (hold ctrl to select more than one). \
          </td> \
          <td> \
            <select name="subdirs" multiple size=6>' + \
           process_structure(self, "", dd, "") + \
           '</select> \
         </td> \
         <td width=100> \
           &nbsp&nbsp<input type="submit" value="Submit" /> \
         </td> \
       </tr> \
     </table> \
   </center> \
   </form>'

    return HTML(html)

