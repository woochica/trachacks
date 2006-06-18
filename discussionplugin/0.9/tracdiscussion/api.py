from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, pretty_timedelta
import time

# Get one item functions

def get_message(cursor, env, req, log, id):
    columns = ('id', 'forum', 'topic', 'replyto', 'time', 'author', 'body')
    sql = 'SELECT id, forum, topic, replyto, time, author, body FROM message' \
      ' WHERE id = %s' % (id)
    log.debug(sql)
    cursor.execute(sql)
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        return row
    return None

def get_topic(cursor, env, req, log, id):
    columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
    sql = 'SELECT id, forum, time, subject, body, author FROM topic WHERE id =' \
      ' %s' % (id)
    log.debug(sql)
    cursor.execute(sql)
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        row['time'] = format_datetime(row['time'])
        return row
    return None

def get_topic_by_subject(cursor, env, req, log, subject):
    columns = ('id', 'forum', 'time', 'subject', 'body', 'author')
    sql = 'SELECT id, forum, time, subject, body, author FROM topic WHERE subject =' \
      ' "%s"' % (subject)
    log.debug(sql)
    cursor.execute(sql)
    for row in cursor:
        row = dict(zip(columns, row))
        row['author'] = wiki_to_oneliner(row['author'], env)
        row['body'] = wiki_to_html(row['body'], env, req)
        row['time'] = format_datetime(row['time'])
        return row
    return None

def get_forum(cursor, env, req, log, id):
    columns = ('name', 'moderators', 'id', 'time', 'subject', 'description')
    sql = 'SELECT name, moderators, id, time, subject, description FROM' \
      ' forum WHERE id = %s' % (id)
    log.debug(sql)
    cursor.execute(sql)
    for row in cursor:
        row = dict(zip(columns, row))
        row['moderators'] = row['moderators'].split(' ')
        row['description'] = wiki_to_oneliner(row['description'], env)
        return row
    return None

# Get list of items functions
def get_groups(cursor, env, req, log):
    columns = ('id', 'name', 'description')
    sql = 'SELECT id, name, description FROM forum_group'
    log.debug(sql)
    cursor.execute(sql)
    groups = []
    for row in cursor:
        row = dict(zip(columns, row))
        row['name'] = wiki_to_oneliner(row['name'], env)
        row['description'] = wiki_to_oneliner(row['description'], env)
        groups.append(row)
    return groups

def get_forums(cursor, env, req, log):
    columns = ('id', 'name', 'author', 'time', 'moderators', 'group', 'subject',
      'description', 'topics', 'replies', 'lastreply', 'lasttopic')
    sql = 'SELECT id, name, author, time, moderators, forum_group, subject,' \
      ' description, (SELECT COUNT(id) FROM topic t WHERE t.forum = forum.id),' \
      ' (SELECT COUNT(id) FROM message m WHERE m.forum = forum.id), (SELECT' \
      ' MAX(time) FROM message m WHERE m.forum = forum.id), (SELECT MAX(time)' \
      ' FROM topic t WHERE t.forum = forum.id) FROM forum ORDER BY subject'
    log.debug(sql)
    cursor.execute(sql)
    forums = []
    for row in cursor:
        row = dict(zip(columns, row))
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
    sql = 'SELECT id, forum, time, subject, body, author, (SELECT COUNT(id)' \
      ' FROM message m WHERE m.topic = topic.id), (SELECT MAX(time) FROM' \
      ' message m WHERE m.topic = topic.id) FROM topic WHERE forum = %s ORDER' \
      ' BY time' % (forum)
    log.debug(sql)
    cursor.execute(sql)
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
    sql = 'SELECT id, replyto, time, author, body FROM message WHERE topic =' \
      ' %s ORDER BY time' % (topic)
    log.debug(sql)
    cursor.execute(sql)

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

def get_users(env):
    users = []
    for user in env.get_known_users():
        users.append(user[0])
    return users

# Add items functions

def add_forum(cursor, log, name, author, subject, description, moderators,
  group):
    moderators = ' '.join(moderators)
    if not group:
        group = 'NULL'
    sql = 'INSERT INTO forum (name, author, time, moderators, subject,' \
      ' description, forum_group) VALUES ("%s", "%s", %s, "%s", "%s", "%s",' \
      ' %s)' % (name, author, str(int(time.time())), moderators, subject,
      description, group)
    log.debug(sql)
    cursor.execute(sql)

def add_topic(cursor, log, forum, subject, author, body):
    sql = 'INSERT INTO topic (forum, time, author, subject, body) VALUES' \
      ' (%s, %s, "%s", "%s", "%s")' % (forum, str(int(time.time())), author,
      subject, body)
    log.debug(sql)
    cursor.execute(sql)

def add_message(cursor, log, forum, topic, replyto, author, body):
    sql = 'INSERT INTO message (forum, topic, replyto, time, author, body)' \
      ' VALUES (%s, %s, %s, %s, "%s", "%s")' % (forum, topic, replyto,
      str(int(time.time())), author, body)
    log.debug(sql)
    cursor.execute(sql)

# Delete items functions

def delete_forum(cursor, log, forum):
    sql = 'DELETE FROM message WHERE forum = %s' % (forum)
    log.debug(sql)
    cursor.execute(sql)
    sql = 'DELETE FROM topic WHERE forum = %s' % (forum)
    log.debug(sql)
    cursor.execute(sql)
    sql = 'DELETE FROM forum WHERE id = %s' % (forum)
    log.debug(sql)
    cursor.execute(sql)

def delete_topic(cursor, log, topic):
    sql = 'DELETE FROM message WHERE topic = %s' % (topic)
    log.debug(sql)
    cursor.execute(sql)
    sql = 'DELETE FROM topic WHERE id = %s' % (topic)
    log.debug(sql)
    cursor.execute(sql)

def delete_message(cursor, log, message):
    # Get message replies
    sql = 'SELECT id FROM message WHERE replyto = %s' % (message)
    log.debug(sql)
    cursor.execute(sql)
    replies = []
    for row in cursor:
        replies.append(row[0])

    # Delete all replies
    for reply in replies:
        delete_message(cursor, log, reply)

    # Delete message itself
    sql = 'DELETE FROM message WHERE id = %s' % (message)
    log.debug(sql)
    cursor.execute(sql)
