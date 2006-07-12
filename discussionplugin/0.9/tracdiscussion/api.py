from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, pretty_timedelta, escape, unescape
import time

# Get one item functions

def get_message(cursor, env, req, log, id):
    columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
    sql = "SELECT id, forum, topic, replyto, time, author, body FROM message" \
      " WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (id,))
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        return row
    return None

def get_topic(cursor, env, req, log, id):
    columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
    sql = "SELECT id, forum, time, subject, body, author FROM topic WHERE id =" \
      " %s"
    log.debug(sql)
    cursor.execute(sql, (id,))
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        row['time'] = format_datetime(row['time'])
        return row
    return None

def get_topic_by_subject(cursor, env, req, log, subject):
    columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
    sql = "SELECT id, forum, time, subject, body, author FROM topic WHERE subject =" \
      " %s"
    log.debug(sql)
    cursor.execute(sql, (subject,))
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        row['time'] = format_datetime(row['time'])
        return row
    return None

def get_forum(cursor, env, req, log, id):
    columns = ('name', 'moderators', 'id', 'time', 'subject', 'description',
      'group')
    sql = "SELECT name, moderators, id, time, subject, description, forum_group" \
      " FROM forum WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (id,))
    for row in cursor:
        row = dict(zip(columns, row))
        row['moderators'] = row['moderators'].split(' ')
        row['description'] = wiki_to_oneliner(row['description'], env)
        return row
    return None

def get_group(cursor, env, req, log, id):
    columns = ('id', 'name', 'description')
    sql = "SELECT id, name, description FROM forum_group WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (id,))
    for row in cursor:
        row = dict(zip(columns, row))
        row['name'] = wiki_to_oneliner(row['name'], env)
        row['description'] = wiki_to_oneliner(row['description'], env)
        return row
    return None

# Set item functions

def set_group(cursor, log, forum, group):
    if not group:
        group = '0'
    sql = "UPDATE forum SET forum_group = %s WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (group, forum))

def set_forum(cursor, log, topic, forum):
    sql = "UPDATE topic SET forum = %s WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (forum, topic))
    sql = "UPDATE message SET forum = %s WHERE topic = %s"
    log.debug(sql)
    cursor.execute(sql, (forum, topic))

# Edit all functons
def edit_group(cursor, log, group, name, description):
    sql = "UPDATE forum_group SET name = %s, description = %s WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (name, description, group))

def edit_forum(cursor, log, forum, name, subject, description, moderators, group):
    moderators = ' '.join(moderators)
    if not group:
        group = '0'
    sql = "UPDATE forum SET name = %s, subject = %s, description = %s," \
      " moderators = %s, forum_group = %s WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (name, subject, description, moderators, group, forum))

# Get list functions

def get_groups(cursor, env, req, log):
    # Get count of forums without group
    sql = "SELECT COUNT(id) FROM forum WHERE forum_group = 0"
    log.debug(sql)
    cursor.execute(sql)
    no_group_forums = 0
    for row in cursor:
       no_group_forums = row[0]
    groups = [{'id' : 0, 'name' : 'None', 'description' : 'No Group',
      'forums' : no_group_forums}]

    # Get forum groups
    columns = ('id', 'name', 'description', 'forums')
    sql = "SELECT id, name, description, (SELECT COUNT(id) FROM forum f WHERE" \
      " f.forum_group = forum_group.id) FROM forum_group"
    log.debug(sql)
    cursor.execute(sql)
    for row in cursor:
        row = dict(zip(columns, row))
        row['name'] = wiki_to_oneliner(row['name'], env)
        row['description'] = wiki_to_oneliner(row['description'], env)
        groups.append(row)
    return groups

def get_forums(cursor, env, req, log):
    columns = ('id', 'name', 'author', 'time', 'moderators', 'group', 'subject',
      'description', 'topics', 'replies', 'lastreply', 'lasttopic')
    sql = "SELECT id, name, author, time, moderators, forum_group, subject," \
      " description, (SELECT COUNT(id) FROM topic t WHERE t.forum = forum.id)," \
      " (SELECT COUNT(id) FROM message m WHERE m.forum = forum.id), (SELECT" \
      " MAX(time) FROM message m WHERE m.forum = forum.id), (SELECT MAX(time)" \
      " FROM topic t WHERE t.forum = forum.id) FROM forum ORDER BY subject"
    log.debug(sql)
    cursor.execute(sql)
    forums = []
    for row in cursor:
        row = dict(zip(columns, row))
        #row['name'] = wiki_to_oneliner(row['name'], env)
        #row['subject'] = wiki_to_oneliner(row['subject'], env)
        row['moderators'] = wiki_to_oneliner(row['moderators'], env)
        row['description'] = wiki_to_oneliner(row['description'], env)
        if row['lastreply']:
            row['lastreply'] = pretty_timedelta(row['lastreply'])
        else:
            row['lastreply'] = 'No replies'
        if row['lasttopic']:
            row['lasttopic'] = pretty_timedelta(row['lasttopic'])
        else:
            row['lasttopic'] = 'No topics'
        row['time'] = format_datetime(row['time'])
        forums.append(row)
    return forums

def get_topics(cursor, env, req, log, forum):
    columns = ('id', 'forum', 'time', 'subject', 'body', 'author',
      'replies', 'lastreply')
    sql = "SELECT id, forum, time, subject, body, author, (SELECT COUNT(id)" \
      " FROM message m WHERE m.topic = topic.id), (SELECT MAX(time) FROM" \
      " message m WHERE m.topic = topic.id) FROM topic WHERE forum = %s ORDER" \
      " BY time"
    log.debug(sql)
    cursor.execute(sql, (forum,))
    topics = []
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        if row['lastreply']:
            row['lastreply'] = pretty_timedelta(row['lastreply'])
        else:
            row['lastreply'] = 'No replies'
        row['time'] = format_datetime(row['time'])
        topics.append(row)
    return topics

def get_messages(cursor, env, req, log, topic):
    columns = ('id', 'replyto', 'time', 'author', 'body')
    sql = "SELECT id, replyto, time, author, body FROM message WHERE topic =" \
      " %s ORDER BY time"
    log.debug(sql)
    cursor.execute(sql, (topic,))

    messagemap = {}
    messages = []

    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        row['time'] = format_datetime(row['time'])
        messagemap[row['id']] = row

        # Add top-level messages to the main list, in order of time
        if row['replyto'] == -1:
            messages.append(row)

    # Second pass, add replies
    for message in messagemap.values():
        if message['replyto'] != -1:
            parent = messagemap[message['replyto']]
            if 'replies' in parent:
                parent['replies'].append(message)
            else:
                parent['replies'] = [message]
    return messages;

def get_users(env, log):
    users = []
    for user in env.get_known_users():
        users.append(user[0])
    return users

# Add items functions

def add_group(cursor, log, name, description):
    sql = "INSERT INTO forum_group (name, description) VALUES (%s, %s)"
    log.debug(sql)
    cursor.execute(sql, (name, description))


def add_forum(cursor, log, name, author, subject, description, moderators,
  group):
    moderators = ' '.join(moderators)
    if not group:
        group = '0'
    sql = "INSERT INTO forum (name, author, time, moderators, subject," \
      " description, forum_group) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    log.debug(sql)
    cursor.execute(sql, (name, author, str(int(time.time())), moderators,
      subject, description, group))

def add_topic(cursor, log, forum, subject, author, body):
    sql = "INSERT INTO topic (forum, time, author, subject, body) VALUES" \
      " (%s, %s, %s, %s, %s)"
    log.debug(sql)
    cursor.execute(sql, (forum, str(int(time.time())), author, subject, body))

def add_message(cursor, log, forum, topic, replyto, author, body):
    sql = "INSERT INTO message (forum, topic, replyto, time, author, body)" \
      " VALUES (%s, %s, %s, %s, %s, %s)"
    log.debug(sql)
    cursor.execute(sql, (forum, topic, replyto, str(int(time.time())),
      escape(author), escape(body)))

# Delete items functions

def delete_group(cursor, log, group):
    sql = "DELETE FROM forum_group WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (group,))
    sql = "UPDATE forum SET forum_group = 0 WHERE forum_group = %s"
    log.debug(sql)
    cursor.execute(sql, (group,))

def delete_forum(cursor, log, forum):
    sql = "DELETE FROM message WHERE forum = %s"
    log.debug(sql)
    cursor.execute(sql, (forum,))
    sql = "DELETE FROM topic WHERE forum = %s"
    log.debug(sql)
    cursor.execute(sql, (forum,))
    sql = "DELETE FROM forum WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (forum,))

def delete_topic(cursor, log, topic):
    sql = "DELETE FROM message WHERE topic = %s"
    log.debug(sql)
    cursor.execute(sql, (topic,))
    sql = "DELETE FROM topic WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (topic,))

def delete_message(cursor, log, message):
    # Get message replies
    sql = "SELECT id FROM message WHERE replyto = %s"
    log.debug(sql)
    cursor.execute(sql, (message,))
    replies = []
    for row in cursor:
        replies.append(row[0])

    # Delete all replies
    for reply in replies:
        delete_message(cursor, log, reply)

    # Delete message itself
    sql = "DELETE FROM message WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (message,))
