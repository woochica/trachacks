# Ainsley Lawson.  ainsley.lawson@utoronto.ca
# August 2009

from trac.core import *
from trac.util import escape, Markup
from trac.versioncontrol.diff import *
from pkg_resources import resource_filename
from genshi import HTML


def clear_tables(self):
    """
    Clear all the tracSNAP data out of the tables in the database.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    cursor.execute("DELETE FROM code_relations")
    cursor.execute("DELETE FROM expertise")
    cursor.execute("DELETE FROM social_relations")
    cursor.execute("DELETE FROM socialnetworkdb_data")
    cursor.execute('INSERT INTO socialnetworkdb_data VALUES ("lastRev",0)')
    cursor.execute('INSERT INTO socialnetworkdb_data VALUES ("lastRevTime",0)')

    db.commit()
    db.close()


def determine_relations(self, repo):
    """
    Examines the repository to determine how the code relations and
    expertise have changed since the last time the repository was
    analyzed, and updates the code_relations and expertise tables
    in the database accordingly.
    """

    edits_dict, expertise_dict, social_dict = {}, {}, {}

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    # Get the last revision that was analyzed
    cursor.execute('SELECT value FROM socialnetworkdb_data \
                    WHERE name = "lastRev"')
    row = cursor.fetchone()
    last_rev = int(row[0])

    # Get the time of the last comment that was analyzed
    cursor.execute('SELECT value FROM socialnetworkdb_data \
                    WHERE name = "lastRevTime"')
    row = cursor.fetchone()
    last_rev_time = int(row[0])


    ########################## GET CODE RELATIONS #############################

    # Select the revisions to analyze
    # TODO: We have had to limit the analysis to revisions in which
    #		less than 10 files were changed, because otherwise the
    #		analysis takes way too long.  This is not an ideal solution.
    revs = []
    cursor.execute('SELECT rev FROM num_changes \
                    WHERE num < 10 \
                    AND rev > %s',
                   (last_rev,))
    for row in cursor:
        revs.append(row[0])

    for rev in revs:
        # Get the files that were changed during the selected revisions
        cursor.execute('SELECT n.path, r.author \
                        FROM node_change n, revision r \
                        WHERE n.rev = r.rev \
                        AND n.rev = %s \
                        AND n.node_type != "D" ',
                       (rev,))

        for path, author in cursor:

            # Record the files edited in each revision
            # LOGIC: Create a dictionary where the key is the revision #,
            # and the value is a list of files changed at that revision
            if rev not in edits_dict:
                edits_dict[rev] = [str(path)]
            else:
                edits_dict[rev] = edits_dict[rev] + [str(path)]

            # Record the expertise
            # LOGIC: The number of lines changed in the file (between this
            # revision and the previous revision) represents the
            # amount of expertise the author has gained for the file.
            # TODO:  We should only be calculating expertise on files
            # 		 containing code, (i.e. not images, etc.)
            key = (path, author)
            if key not in expertise_dict:
                expertise_dict[key] = expertise_calculator(path, rev, repo)
            else:
                expertise_dict[key] = expertise_dict[key] + \
                                      expertise_calculator(path, rev, repo)

    # structure of code_relations_dict entries:
    # (file1, file2) : num_times_checked_in_together
    # file1 and file2 are in ALPHABETICAL ORDER within in the tuple.
    code_relations_dict = {}

    # Fill up the code relations dictionary
    for related_list in edits_dict.values():
        related_list.sort()
        length = len(related_list)

        i, j = 0, 1
        while (i < length - 1):
            while (j < length):
                file_pair = (related_list[i], related_list[j])
                if file_pair not in code_relations_dict:
                    code_relations_dict[file_pair] = 1
                else:
                    code_relations_dict[file_pair] = code_relations_dict[file_pair] + 1
                j += 1
            i += 1
            j = i + 1


    ########################## GET SOCIAL RELATIONS ###########################

    # (1.) There is a social connection between the reporter of the ticket,
    # and each person who has commented on that ticket
    cursor.execute('SELECT t.reporter, tc.author \
                    FROM ticket_change tc, ticket t \
                    WHERE t.id = tc.ticket \
                    AND tc.field = "comment"\
                    AND t.reporter != tc.author\
                    AND tc.time > %s',
                   (last_rev_time,))

    # Fill up the social relations dictionary
    for person1, person2 in cursor:

        # Keep the people in alphabetical order
        if person1 < person2:
            people = (person1, person2)
        else:
            people = (person2, person1)

        if people not in social_dict:
            social_dict[people] = 1
        else:
            social_dict[people] = social_dict[people] + 1

    # (2.) There is a social connection between people who have commented
    # on the same ticket.
    cursor.execute('SELECT t1.author, t2.author \
                    FROM ticket_change t1, ticket_change t2 \
                    WHERE t1.ticket = t2.ticket \
                    AND t1.field = "comment" \
                    AND t2.field = "comment"\
                    AND t1.time < t2.time\
                    AND t1.author != t2.author\
                    AND t2.time > %s',
                   (last_rev_time,))

    # Fill up the social relations dictionary
    for person1, person2 in cursor:

        # Keep the people in alphabetical order
        if person1 < person2:
            people = (person1, person2)
        else:
            people = (person2, person1)

        if people not in social_dict:
            social_dict[people] = 1
        else:
            social_dict[people] = social_dict[people] + 1


    ############################## UPDATE TABLES ##############################

    # Store current rev, so that we know where to update from next time
    cursor.execute('SELECT max(rev)	FROM revision')
    row = cursor.fetchone()
    last_rev = int(row[0])
    cursor.execute('UPDATE socialnetworkdb_data \
                    SET value = %s \
                    WHERE name = "lastRev"',
                   (last_rev,))

    # Store the time of the most recent comment
    cursor.execute('SELECT max(time) FROM ticket_change')
    row = cursor.fetchone()
    if row[0] == None:
        last_rev_time = 0  # no ticket comments
    else:
        last_rev_time = int(row[0])
    cursor.execute('UPDATE socialnetworkdb_data \
                    SET value = %s \
                    WHERE name = "lastRevTime"',
                   (last_rev_time,))

    db.commit()
    db.close()

    # Update the database
    fill_code_relations_table(self, code_relations_dict)
    fill_expertise_table(self, expertise_dict)
    fill_social_relations_table(self, social_dict)


def expertise_calculator(path, rev, repo):
    """
    Returns the number of changes made to the file at location [path]
    at revision [rev], compared to its previous revision.
    """

    rev = repo.normalize_rev(rev)
    path = repo.normalize_path(path)

    try:
        # get the file at location [path] and revision [rev]
        node_new = repo.get_node(path, rev)
    except:
        # TODO: deal with nodes that are deleted
        return 0


    # get the (path, rev, chg) tuple for the prev time the file was changed
    prev_rev = node_new.get_previous()

    if (prev_rev == None):
        # The file has just been added
        # TODO: assign some level of expertise
        return 50

    try:
        # get the file at location [path] on its previous revision
        node_old = repo.get_node(path, prev_rev[1])
    except:
        return 0

    # get the content of the files
    line_list_new = node_new.get_content().read().split('\n')
    line_list_old = node_old.get_content().read().split('\n')

    # get the diff between the two files
    # (unified_diff is in trac/versioncontrol/diff.py)
    diff_line_list = unified_diff(line_list_old, line_list_new)

    # count the changes
    change_count = 0
    for line in diff_line_list:
        if (line.startswith('+') or line.startswith('-')):
            change_count += 1

    return change_count


def fill_code_relations_table(self, code_relations_dict):
    """
    Update the code_relations table in the database using the entries
    from the code_relations_dict.  Entries should be as follows:
              (file1, file2) : #TimesCheckedInTogether,
    where file1, file2 are in ALPHABETICAL ORDER.
    The row in the database associated with file1, file2 will have its
    'strength' value incremented by #TimesCheckedInTogether.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    for (files, strength) in code_relations_dict.items():
        file1, file2 = files
        cursor.execute("SELECT strength \
                        FROM code_relations \
                        WHERE file1 = %s AND file2 = %s",
                       (file1, file2,))
        row = cursor.fetchone()

        if row == None:
            # Not in database yet
            cursor.execute("INSERT INTO code_relations \
                            VALUES (%s, %s, %s)",
                           (file1, file2, strength,))
        else:
            # Update database
            cursor.execute("UPDATE code_relations \
                            SET strength= %s \
                            WHERE file1 = %s AND file2 = %s",
                           (row[0] + strength, file1, file2,))
    db.commit()
    db.close()


def fill_expertise_table(self, expertise_dict):
    """
    Update the expertise table in the database using the entries
    from the expertise_dict.  Entries should be as follows:
              (path, author) : AmountOfExpertise.
    The row in the database associated with author, path will have its
    'strength' value incremented by AmountOfExpertise.
    """
    db = self.env.get_db_cnx()
    cursor = db.cursor()

    for ((path, author), strength) in expertise_dict.items():
        cursor.execute("SELECT strength \
                        FROM expertise \
                        WHERE path = %s AND author = %s",
                       (path, author))

        row = cursor.fetchone()
        if row == None:

            # Not in database yet
            cursor.execute(
                "INSERT INTO expertise \
                 VALUES (%s, %s, %s)",
                (path, author, strength,))

        else:

            # Update database
            cursor.execute(
                "UPDATE expertise \
                 SET strength= %s \
                 WHERE path = %s AND author = %s",
                (row[0] + strength, path, author,))

    db.commit()
    db.close()


def fill_social_relations_table(self, social_dict):
    """
    Update the social realtions table in the database using the entries
    from the social_dict.  Entries should be as follows:
              (person1, person2) : StrengthOfConnection
    The row in the database associated with author, path will have its
    'strength' value incremented by StrengthOfConnection.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()

    for (people, strength) in social_dict.items():
        person1, person2 = people
        cursor.execute("SELECT strength \
                        FROM social_relations \
                        WHERE person1 = %s AND person2 = %s",
                       (person1, person2,))
        row = cursor.fetchone()

        if row == None:
            # Not in database yet
            cursor.execute("INSERT INTO social_relations \
                            VALUES (%s, %s, %s)",
                           (person1, person2, strength,))
        else:
            # Update database
            cursor.execute("UPDATE social_relations \
                            SET strength= %s \
                            WHERE person1 = %s AND person2 = %s",
                           (row[0] + strength, person1, person2,))
    db.commit()
    db.close()


def new_social_connection(self, p1, p2, strength):
    """
    Insert a new social connection between p1 and p2 into the database,
    with the specified strength.
    """

    db = self.env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute('INSERT INTO social_relations \
                    VALUES (%s, %s, %s)',
                   (p1, p2, strength))
    db.commit()
    db.close()
