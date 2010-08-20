# model.py

import time


status_str = {
             -1 : "No need to review",             # No need to Review
              2 : "Awaiting review",               # Awaiting review
              1 : "Undergoing review",             # Need to Review
              0 : "Completely reviewed"            # Completed
             }


str_status = {
              "NoNeedToReview"   : -1,
              "UndergoingReview" :  1,
              "CompletelyReview" :  0,
              "AwaitingReview"   :  2
             }

class CodeReviewPool(object):
    '''CodeReviewPool class
    '''
    def __init__(self, env):
        self.env = env
        self.db = self.env.get_db_cnx()
        self.cursor = self.db.cursor()

    def get_rev_count(self):
        self.cursor.execute("SELECT count(rev) FROM revision")
        return int(self.cursor.fetchone()[0])

    def get_codereviews_by_time(self, start_time, stop_time):
        self.cursor.execute("SELECT c.time, c.author, c.text, c.id, " \
                            "c.status, c.version, r.message FROM " \
                            "codereview c LEFT OUTER JOIN revision r " \
                            "ON(c.id=CAST(r.rev AS integer)) " \
                            "WHERE c.time>=%s AND c.time<=%s " \
                            "ORDER BY c.time", \
                            (start_time, stop_time))
        for record in self.cursor:
            yield record

    def get_revisions_by_status(self, status=None, start_rev=0):
        last_rev = self.get_rev_count()
        if status == "Completed":
            status_list = [str_status["CompletelyReview"], str_status["NoNeedToReview"]]
        elif status == "Undergoing":
            status_list = [str_status["UndergoingReview"], ]
        if status != "Awaiting":
           self.cursor.execute("SELECT c.id, c.priority " \
                               "FROM review_current r " \
                               "LEFT OUTER JOIN codereview c ON " \
                               "r.id=c.id and r.version=c.version " \
                               "WHERE c.status IN (" \
                               + ','.join(["%s"] * len(status_list)) + \
                               ") AND %s>=c.id AND c.id>=%s " \
                               "ORDER BY c.id DESC", \
                               status_list + [last_rev, start_rev])

        else:
            self.cursor.execute("SELECT rev FROM revision " \
                                "WHERE CAST(rev AS integer) NOT IN " \
                                "(SELECT id FROM codereview) " \
                                "AND %s>=CAST(rev AS integer) " \
                                "AND CAST(rev AS integer)>=%s " \
                                "ORDER by rev DESC", \
                                (last_rev, start_rev))


        id_cs = []
        priority_cs = {}

        if status == "Completed" or status == "Undergoing":
            for row in self.cursor:
                id_cs.append(int(row[0]))
                priority_cs[row[0]] = row[1]
            return id_cs, priority_cs
        elif status == "Awaiting":
            for row in self.cursor:
                id_cs.append(int(row[0]))
            return id_cs

    def get_codereviews_by_revisions(self, revisions, key=None, not_shown=None):
        for (rev, author, msg, prefix, ctime) in self.changeset_info(revisions):
           if not msg:
               msg = ''
           if key and not self._is_match(key, author, msg, ctime):
               continue
           if not self._is_show(not_shown, prefix, msg):
               continue
           item = {'rev':rev,
                   'prefix':prefix,
                   'author':author,
                   'msg':msg,
                   'ctime':ctime
                  }
           yield item


    def get_codereviews_by_key(self, status, start_rev=0, key=None, not_shown=None):
        codereviews_items = []
        if status != "Awaiting":
            id_cs, priority_cs = self.get_revisions_by_status(status, start_rev)
        else:
            id_cs = self.get_revisions_by_status(status, start_rev)

        for item in self.get_codereviews_by_revisions(id_cs, key, not_shown):
            if status != "Awaiting":
                item['priority'] = priority_cs[int(item['rev'])]
                item['reviewers'] = self.get_reviewers(item['rev'])
            item['rev'] = str(item['rev'])
            codereviews_items.append(item)
        if status == "Awaiting":
            codereviews_items.sort(lambda x, y: cmp(int(y['rev']), \
                                   int(x['rev'])))
        return codereviews_items

    def _is_match(self, key, author, msg, ctime):
        if not key:
            return True
        if key.has_key('author'):
            for one in key['author']:
                if one in author.strip().lower():
                    break
            else:
                return False
        if key.has_key('comment') and key['comment'] not in msg.strip().lower():
            return False
        if key.has_key('start_date') and key.has_key('end_date') and \
               (ctime < key['start_date'] or ctime > key['end_date']):
            return False
        return True

    def _is_show(self, not_shown, prefix, msg):
        if not not_shown:
            return True
        if not_shown.has_key('prefix'):
            for i in not_shown['prefix']:
                if prefix.startswith(i):
                    return False
        if not_shown.has_key('msg'):
            for i in not_shown['msg']:
                if msg.startswith(i):
                    return False
        return True
        
    def get_reviewers(self, rev):
        return CodeReview(self.env, rev).get_reviewers()


    def changeset_info(self, revisions):
        ret = []
        if self.env.config.get("trac", "database", "").lower().startswith("sqlite"):
            self.cursor.execute("SELECT r.rev, author, message, path, time " \
                                "FROM revision r LEFT OUTER JOIN rev_path p " \
                                "ON (p.rev=r.rev) ORDER BY r.rev+0 DESC ")
        else:
            self.cursor.execute("SELECT r.rev, author, message, path, time " \
                                "FROM revision r LEFT OUTER JOIN rev_path p " \
                                "ON (p.rev=r.rev) ORDER BY CAST(r.rev AS " \
                                "integer) DESC ")
        result = self.cursor.fetchall()

        for r, author, message, common_path, ctime in result:
            if int(r) not in revisions:
                continue
            if message and len(message) > 100:
                message = message[:99] + '...'
            if not common_path:
                common_path = CommitPath(self.env).get_path(int(r))

            yield (r, author or '', message, common_path, ctime)

class CodeReview(object):
    '''CodeReview class
    '''

    fields = ('id', 'author', 'status', 'time', 'text', 'version', 'priority')

    def __init__(self, env, rev, author=None):
        self.env = env
        self.db = self.env.get_db_cnx()
        self.cursor = self.db.cursor()
        self.id = rev
        self.author = author
        self.item = {}

    def __getitem__(self, key):
        if key not in self.fields:
            raise KeyError, "CodeReview has no field %s" % key
        else:
            if self.item.has_key(key):
                return self.item[key]
            elif self.is_existent():
                return self.get_item()[key]
            else:
                return None

    def __setitem__(self, key, value):
        if key not in self.fields:
            raise KeyError, "CodeReview has no field %s" % key
        else:
            self.item[key] = value
            return value

    def is_existent_rev(self):
        self.cursor.execute("SELECT rev FROM revision WHERE rev=%s", \
                            (self.id, ))
        if not self.cursor.fetchone():
            return False
        else:
            return True

    def get_current_ver(self):
        self.cursor.execute("SELECT version FROM review_current WHERE id=%s", \
                            (self.id, ))
        ver = self.cursor.fetchone()
        if ver:
            return ver[0]
        else:
            return 0

    def is_existent_ver(self, ver):
        self.cursor.execute("SELECT version FROM codereview " \
                            "WHERE id=%s AND version=%s", (self.id, ver))
        if self.cursor.fetchone():
            return True
        else:
            return False

    def is_existent(self):
        ver = self.get_current_ver()
        if ver == 0:
            return False
        else:
            return True
        
    def get_item(self, ver=None):
        if ver:
            req_ver = ver
        else:
            req_ver = self.get_current_ver()
        item = {}
        if self.is_existent():
            self.cursor.execute("SELECT status,time,text,priority,author " \
                                "FROM codereview WHERE id=%s and version=%s", \
                                (self.id, req_ver))
            item['status'], item['time'], item['text'], item['priority'], item['author'] = self.cursor.fetchone()
        else:
            item['status'] = str_status['AwaitingReview']
            item['time'] = None
            item['priority'] = None
            item['author'] = self.author
            item['text'] = None
        item['id'] = self.id
        item['version'] = req_ver
        item['reviewers'] = self.get_reviewers()
        return item

    def get_reviewers(self):
        # modify the select statement, or there will be an Error like this:
        # ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list.
        self.cursor.execute("SELECT author FROM codereview WHERE id = %s " \
                            "GROUP BY author ORDER BY MIN(version)", \
                            (self.id, ))
        return [reviewer[0] for reviewer in self.cursor if reviewer[0] and \
                reviewer[0] != 'anonymous']

    def set_item(self, item):
        for key in item.keys():
            if key in self.fields:
                self.item[key] = item[key]

    def save(self, item = None):
        if item:
            self.set_item(item)
        old_item = self.get_item()
        for field in self.fields:
            if field not in self.item.keys() and old_item[field] is not None:
                self.item[field] = old_item[field]
        self.item['time'] = round(time.mktime(time.localtime()), 2)
        self.item['version'] = self.get_current_ver() + 1
        keys = self.item.keys()
        values = [self.item[key] for key in keys]
        
        self.cursor.execute("INSERT INTO codereview (%s) VALUES (%s)" % \
                            (','.join(keys), ','.join(['%s' for key in keys])), values)
        self.db.commit()

    def delete(self):
        if not self.is_existent():
            return
        self.cursor.execute("DELETE FROM codereview WHERE id=%s " \
                            "AND version=%s", \
                            (self.id, self.get_current_ver()))
        self.db.commit()

    def set_to_critical(self):
        item = {}
        if self.get_item()['priority'] != 'critical':
            item['priority'] = 'critical'
        if self.get_item()['status'] != str_status['UndergoingReview']:
            item['status'] = str_status['UndergoingReview']
        if item:
            self.save(item)
        else:
            return

    def set_no_need_to_review(self):
        if self.get_item()['status'] != str_status['NoNeedToReview']:
            self.item['status'] = str_status['NoNeedToReview']
            self.save()
        else:
            return

    def get_all_items(self):
        self.cursor.execute("SELECT " + ','.join(self.fields) + \
                            " FROM codereview WHERE id=%s ORDER BY version", \
                            (self.id, ))
        for record in self.cursor:
            item = {}
            for i in range(len(self.fields)):
                item[self.fields[i]] = record[i]
            yield item

    def get_commit_path(self):
        return CommitPath(self.env).get_path(self.id)

    def get_all_pathes(self):
        self.cursor.execute("SELECT path FROM node_change " \
                            "WHERE rev=%s", (self.id, ))
        return [path[0] for path in self.cursor]


class CommitPath(object):
    def __init__(self, env):
        self.env = env
        self.db = self.env.get_db_cnx()
        self.cursor = self.db.cursor()

    def get_path(self, rev):
        self.cursor.execute("SELECT path FROM rev_path "
                            "WHERE rev=%s", (rev, ))
        path = self.cursor.fetchone()
        if path:
            return path[0]
        else:
            return self._render_path(rev)

    def _render_path(self, rev):
        self.cursor.execute("SELECT path FROM node_change " \
                            "WHERE rev=%s", (rev, ))
        try:
            paths = [row[0] for row in self.cursor]
            common_path = row[0]
            for path in paths:
                for index in range(len(path)):
                    if common_path[:index] != path[:index]:
                        if index:
                            common_path = common_path[:index-1]
                            continue
                        else:
                            common_path = ''
                            break
        except Exception, e:
            common_path = '/'
        if not common_path:
            common_path = '/'
        if common_path.count('/') > 2:
            common_path = common_path.split("/")[0]
        if len(common_path) >= 30:
            common_path = common_path[:30] + ' ...'
        self.cursor.execute("INSERT INTO rev_path (rev, path) " \
                            "VALUES (%s, %s)", (rev, common_path))
        self.db.commit()
        return common_path
