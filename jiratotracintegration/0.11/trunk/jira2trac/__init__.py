#!/usr/bin/env python3.1
#
# Copyright (c) 2008-2009 The Jira2Trac Project.
# See LICENSE.txt for details.

"""
Import a Jira backup into a Trac database using XML-RPC.

@since: 2008-12-20
"""

import os
import sys
import logging as log

from io import FileIO
from stat import ST_SIZE
from xmlrpc import client
from decimal import Decimal
from datetime import datetime
from operator import itemgetter
from urllib.parse import urlparse
from socket import error as socketError
from xml.parsers.expat import ParserCreate

from jira2trac.util import create_hash
from jira2trac.util import DisplayProgress


__all__ = ['JiraDecoder', 'TracEncoder']

__version__ = (0, 2)

version = '.'.join(map(lambda x: str(x), __version__))


class JiraDecoder(object):
    """
    Parse a Jira XML backup file.
    """
    def __init__(self, input):
        if input:
            self.input = input
            self.lastComment = None
            self.lastIssue = None
            self.allItems = []
            self.comments = []
            self.issues = []
            self.data = dict()
            self.categories = ['versions', 'resolutions', 'projects', 'priorities',
                               'components', 'issueTypes', 'statuses', 'groups',
                               'issues', 'attachments', 'users', 'actions',
                               'currentSteps', 'historySteps', 'historyStepPrev']

            for c in self.categories:
                self.data[c] = []
        else:
            raise BaseException("Please specify a valid 'input' or 'config' option")

    def parse_backup_file(self):
        """
        Load Jira backup file.
        """
        if os.path.exists(self.input):
            self.size = Decimal(str(os.stat(self.input)[ST_SIZE]/(1024*1024))
                                ).quantize(Decimal('.01'))
        else:
            raise BaseException("Jira backup file not found: {}".format(self.input))

        log.info('Loading Jira backup file: {} ({} MB)'.format(self.input, self.size))
        log.info('Processing data...')

        file = FileIO(self.input, 'r').readall()
        p = ParserCreate()
        p.StartElementHandler = self._start_element
        p.EndElementHandler = self._end_element
        p.CharacterDataHandler = self._char_data
        p.Parse(file, 1)

    def show_results(self):
        """
        Display the parsed result.
        """       

        for category in self.categories:
            name = category.title()
            total = len(self.data[category])
            msg = '  {} {}...'

            if category == 'issueTypes':
                name = 'Issue Types'

            elif category == 'currentSteps' or category == 'historySteps' or \
                 category == 'historyStepPrev':
                name = 'History'
                # print a parsed category
                #for item in self.data[category]:
                #    print(item)
                #    print('%50s - %s - %s - %s' % (item['issue'], item['author'], item['type'],
                #                          item['body']))

            log.info(msg.format(total, name))

    def _add_item(self, category, data, type=None):
        if type == None:
            type = self.allItems
        
        try:
            self.data[category].append(data)
        except KeyError:
            self.data[category] = [data]

        type.append(data)
        self.category = category

    def _char_data(self, data):
        log.debug('Character data: {}'.format(repr(data)))

        if self.lastComment:
            self._update_item(data, self.lastComment)
        elif self.lastIssue:
            self._update_item(data, self.lastIssue)

    def _update_item(self, data, target):
        if (data != "'\n'") or (data[1:len(data)-1].isspace() == False):
            if target == self.lastComment:
                field = 'body'
            elif target == self.lastIssue:
                field = 'description'

            target[field] += data

    def _end_element(self, name):
        log.debug('End element: {}'.format(name))
        index = len(self.data[self.category]) - 1

        if name == 'body':
            self.data[self.category][index] = self.lastComment
            self.lastComment = None
        elif name == 'description':
            self.data[self.category][index] = self.lastIssue
            self.lastIssue = None

    def _start_element(self, name, attrs):
        log.debug('Start element: {} {}'.format(name, attrs))

        if name == 'Version':
            version = {'number':attrs['name']}
            try:
                version['description'] = attrs['description']
            except KeyError:
                version['description'] = None

            try:
                version['releasedate'] = self.to_datetime(attrs['releasedate'])
            except KeyError:
                version['releasedate'] = 0

            self._add_item('versions', version)

        elif name == 'Resolution':
            resolution = {'name': attrs['name'], 'description': attrs['description'],
                          'id': attrs['id']}
            
            self._add_item('resolutions', resolution)

        elif name == 'Status':
            status = {'id': attrs['id'], 'sequence': attrs['sequence'],
                      'name': attrs['name'], 'description': attrs['description']}

            self._add_item('statuses', status)

        elif name == 'Project':
            project = {'name': attrs['name'], 'owner': attrs['lead'],
                       'description': attrs['description'], 'id': attrs['id']}

            self._add_item('projects', project)

        elif name == 'Priority':
            priority = {'name': attrs['name'], 'description': attrs['description'],
                        'id': attrs['id']}

            self._add_item('priorities', priority)

        elif name == 'OSUser':
            user = {'name': attrs['name'], 'id': attrs['id']}
            
            try:
                user['password'] = attrs['passwordHash']
                self._add_item('users', user)
            except KeyError:
                pass

        elif name == 'OSCurrentStep':
            current_step = {'status': attrs['status'], 'date': attrs['startDate'],
                        'id': attrs['id'], 'entry_id': attrs['entryId'],
                        'action_id': attrs['actionId'], 'step_id': attrs['stepId']}

            current_step['date'] = self.to_datetime(current_step['date'])
            
            self._add_item('currentSteps', current_step)

        elif name == 'OSHistoryStep':
            hist_step = {'status': attrs['status'], 'start_date': attrs['startDate'],
                        'end_date': attrs['finishDate'], 'id': attrs['id'],
                        'entry_id': attrs['entryId'], 'caller': attrs['caller'],
                        'action_id': attrs['actionId'], 'step_id': attrs['stepId']}
        
            hist_step['start_date'] = self.to_datetime(hist_step['start_date'])
            hist_step['end_date'] = self.to_datetime(hist_step['end_date'])
            
            self._add_item('historySteps', hist_step)

        elif name == 'OSHistoryStepPrev':
            hist_step_prev = {'id': attrs['id'], 'prev_id': attrs['previousId']}           
            self._add_item('historyStepPrev', hist_step_prev)

        elif name == 'Issue':
            issue = {'project': attrs['project'], 'id': attrs['id'],
                     'reporter': attrs['reporter'], 'assignee': attrs['assignee'],
                     'type': attrs['type'], 'summary': attrs['summary'],
                     'priority': attrs['priority'], 'status': attrs['status'],
                     'votes': attrs['votes'], 'key': attrs['key']}

            issue['created'] = self.to_datetime(attrs['created'])

            try:
                issue['resolution'] = attrs['resolution']
            except KeyError:
                issue['resolution'] = 1

            try:
                issue['description'] = attrs['description']
            except:
                issue['description'] = ''

            self._add_item('issues', issue, self.issues)

        elif name == 'Component':
            component = {'project': attrs['project'], 'id': attrs['id'],
                         'name': attrs['name'], 'description': attrs['description'],
                         'owner': attrs['lead']}

            self._add_item('components', component)

        elif name == 'CustomFieldValue' and attrs['customfield'] == '10001':
            customFieldValue = {'issue': attrs['issue'], 'id': attrs['id'],
                                'value': attrs['stringvalue']}

            self._add_item('customFieldValues', customFieldValue)

        elif name == 'EventType':
            eventType = {'id': attrs['id'], 'name': attrs['name'],
                         'description': attrs['description']}

            self._add_item('eventTypes', eventType)

        elif name == 'IssueType':
            issueType = {'id': attrs['id'], 'sequence': attrs['sequence'],
                         'name': attrs['name'], 'description': attrs['description']}

            self._add_item('issueTypes', issueType)

        elif name == 'FileAttachment':
            attachment = {'id': attrs['id'], 'issue': attrs['issue'],
                         'mimetype': attrs['mimetype'], 'filename': attrs['filename'],
                         'filesize': attrs['filesize']}

            attachment['created'] = self.to_datetime(attrs['created'])

            try:
                attachment['author'] = attrs['author']
            except KeyError:
                attachment['author'] = ''

            self._add_item('attachments', attachment)

        elif name == 'OSGroup':
            group = {'id': attrs['id'], 'name': attrs['name']}

            self._add_item('groups', group)

        elif name == 'Action':
            action = {'id': attrs['id'], 'issue': attrs['issue'],
                      'author': attrs['author'], 'type': attrs['type']}

            action['created'] = self.to_datetime(attrs['created'])

            try:
                action['body'] = attrs['body']
            except KeyError:
                action['body'] = ''

            self._add_item('actions', action, self.comments)

        elif name == 'OSMembership':
            membership = {'id': attrs['id'], 'username': attrs['userName'],
                          'groupName': attrs['groupName']}

            self._add_item('memberships', membership)
        
        elif name == 'body':
            self.lastComment = self.comments[len(self.comments)-1]
            self.lastComment['body'] = ''

        elif name == 'description':
            self.lastIssue = self.issues[len(self.issues)-1]
            self.lastIssue['description'] = ''

        # Unused:
        #  - OSCurrentStep id="10905" entryId="10009" stepId="6" actionId="0"
        #                  startDate="2008-09-23 17:58:31.0" status="Closed"/>
        #  - OSCurrentStepPrev id="10009" previousId="10006"/>
        #  - OSHistoryStep id="10006" entryId="10006" stepId="1" actionId="5" startDate="2006-11-18 07:13:28.0"
        #                   finishDate="2006-11-18 12:28:34.0" status="Finished" caller="john"/>
        #  - OSHistoryStepPrev id="10574" previousId="10571"/>
        #  - OSCurrentStepPrev id="10898" previousId="10897"/>
        #  - OSPropertyEntry
        #  - OSPropertyString
        #  - OSWorkflowEntry
        #  - OSMembership id="10326" userName="user" groupName="jira-users"/> 
        #  - UserAssociation
        #  - NodeAssociation
        #  - Notification
        #  - SchemePermissions

    def to_datetime(self, timestamp):
        """
        Turn timestamp string into C{datetime.datetime} object.
        """
        return datetime.strptime(timestamp[:-2], '%Y-%m-%d %H:%M:%S')


class TracEncoder(object):
    """
    Import data into remote Trac database using XML-RPC.
    """
    def __init__(self, jira_data, username, password, url, attachments, auth):
        if url:
            self.jiraData = jira_data
            self.username = username
            self.password = password
            self.attachments = attachments
            self.authentication = auth

            cred = ''
            if username is not None and password is not None:
                cred = '{}:{}@'.format(username, password)

            trac_url = urlparse(url)
            self.location = '{}://{}{}{}/login/xmlrpc'.format(trac_url.scheme,
                                                      cred, trac_url.netloc,
                                                      trac_url.path.rstrip('/'))
            
            log.info('{}...'.format(self.__doc__.strip()))
        else:
            raise ValueError("Please specify a value for the 'url' option")

    def import_data(self):
        """
        Save all data to the Trac database.
        """
        log.info('Connecting to: {}'.format(self.location))
        log.info('Attachments location: {}'.format(self.attachments))
        log.info('Credentials type: {}'.format(self.authentication))

        self.proxy = client.ServerProxy(self.location, use_datetime=True)

        log.info('Importing data...')
        self._call(self._import_versions)
        self._call(self._import_resolutions)
        self._call(self._import_priorities)
        self._call(self._import_issue_types)
        self._call(self._import_milestones)
        self._call(self._import_components)
        self._call(self._import_statuses)
        self._call(self._import_issues)

    def import_users(self):
        """
        Store imported users in a new .htpasswd style file.
        """
        log.info('  {} Users...'.format(len(self.jiraData['users'])))

        line = '{}:{}\n'
        output = FileIO(self.authentication, 'w')
        output.write(line.format(self.username, create_hash(self.password)))
        
        for user in self.jiraData['users']:
            output.write(line.format(user['name'], user['password']))

        output.close()

    def _call(self, func):
        """
        Invoke a method and handle exceptions.
        """
        try:
            func()

        except client.ProtocolError as err:
            log.error("A protocol error occurred!")
            log.error("URL: {}".format(err.url))
            log.error("HTTP/HTTPS headers: {}".format(err.headers))
            log.error("Error: {} - {}".format(err.errcode, err.errmsg))
            exit()

        except client.Fault as err:
            log.error("A fault occurred!")
            log.error("Fault code: {}".format(err.faultCode))
            log.error("Fault string: {}".format(err.faultString))

        except socketError as err:
            log.error("A socket error occurred!")
            log.error("Error while connecting: {}".format(err))
            exit()

    def _import_versions(self):
        # get existing versions from trac
        versions = self.proxy.ticket.version.getAll()

        # remove existing versions from trac if necessary
        if len(versions) > 0:
            for version in versions:
                self.proxy.ticket.version.delete(version)

        # show progress bar
        progress = DisplayProgress(len(self.jiraData['versions']),
                                   'Versions')
        
        # import new versions into trac
        for version in self.jiraData['versions']:
            # exclude trailing 'v' from version number
            nr = version['number'][1:]
            desc = version['description']
            date = version['releasedate']
            attr = {'name': nr, 'time': date, 'description': desc}
            self.proxy.ticket.version.create(nr, attr)
            progress.update()

    def _import_resolutions(self):
        # get existing resolutions from trac
        resolutions = self.proxy.ticket.resolution.getAll()

        # remove existing resolutions from trac if necessary
        if len(resolutions) > 0:
            for resolution in resolutions:
                self.proxy.ticket.resolution.delete(resolution)

        # show progress bar
        progress = DisplayProgress(len(self.jiraData['resolutions']),
                                    'Resolutions')

        # import new resolutions into trac
        order = 1
        for resolution in self.jiraData['resolutions']:
            name = resolution['name']
            self.proxy.ticket.resolution.create(name, order)
            order += 1
            progress.update()

    def _import_priorities(self):
        # get existing priorities from trac
        priorities = self.proxy.ticket.priority.getAll()

        # remove existing priorities from trac if necessary
        if len(priorities) > 0:
            for priority in priorities:
                self.proxy.ticket.priority.delete(priority)

        # show progress bar
        progress = DisplayProgress(len(self.jiraData['priorities']),
                                   'Priorities')

        # import new priorities into trac
        order = 1
        for priority in self.jiraData['priorities']:
            name = priority['name']
            self.proxy.ticket.priority.create(name, order)
            order += 1
            progress.update()

    def _import_issue_types(self):
        # get existing issue types from trac
        issueTypes = self.proxy.ticket.type.getAll()

        # remove existing issue types from trac if necessary
        if len(issueTypes) > 0:
            for issueType in issueTypes:
                self.proxy.ticket.type.delete(issueType)

        # show progress bar
        progress = DisplayProgress(len(self.jiraData['issueTypes']),
                                   'Issue Types')

        # import new issue types into trac
        for issueType in self.jiraData['issueTypes']:
            name = issueType['name']
            order = issueType['sequence']
            self.proxy.ticket.type.create(name, order)
            progress.update()

    def _import_milestones(self):
        # get existing milestones from trac
        milestones = self.proxy.ticket.milestone.getAll()

        # seems Jira doesn't support milestones or we never used them
        # so remove all existing milestones from trac
        if len(milestones) > 0:
            for milestone in milestones:
                self.proxy.ticket.milestone.delete(milestone)

    def _import_components(self):
        # get existing components from trac
        components = self.proxy.ticket.component.getAll()

        # remove existing components from trac if necessary
        if len(components) > 0:
            for component in components:
                self.proxy.ticket.component.delete(component)

        # show progress bar
        progress = DisplayProgress(len(self.jiraData['projects']),
                                   'Components')

        # import new components into trac
        # note: we import jira's projects as components into trac because
        # components in jira are children of projects, and trac doesn't
        # support this type of hierarchy
        for component in self.jiraData['projects']:
            name = component['name']
            owner = component['owner']
            desc = component['description']
            attr = {'name': name, 'owner': owner, 'description': desc}
            self.proxy.ticket.component.create(name, attr)
            progress.update()

    def _import_statuses(self):
        # get existing statuses from trac
        statuses = self.proxy.ticket.status.getAll()

        # Note: ticket.status.delete() and ticket.status.update() aren't working
        # due to a bug in the XML-RPC plugin for Trac, see this link for more
        # information: http://trac-hacks.org/ticket/5268
        # For that reason it's not possible to delete the default Trac statuses
        # so we hardcode and manually map the statuses
        self.jiraData['statuses'][0]['name'] = statuses[3] # open/new
        self.jiraData['statuses'][1]['name'] = statuses[0] # in progress/accepted
        self.jiraData['statuses'][2]['name'] = statuses[4] # reopened/reopened
        self.jiraData['statuses'][3]['name'] = statuses[2] # resolved/closed
        self.jiraData['statuses'][4]['name'] = statuses[2] # closed/closed

        log.info('  {} Statuses...'.format(len(self.jiraData['statuses'])))

    def _import_issues(self):
        # show progress bar
        progress = DisplayProgress(len(self.jiraData['issues']),
                                   'Issues')
        
        # import new issues into trac
        for issue in self.jiraData['issues']:
            # TODO: version
            description = issue['description']            
            reporter = issue['reporter']
            owner = issue['assignee']
            summary = issue['summary']
            time = issue['created']
            status = self._get_item(issue['status'], 'statuses')
            component = self._get_item(issue['project'], 'projects')
            resolution = self._get_item(issue['resolution'], 'resolutions')
            type = self._get_item(issue['type'], 'issueTypes')
            priority = self._get_item(issue['priority'], 'priorities')
            comments = self._get_comments(issue['id'])
            attachments = self._get_attachments(issue['id'])

            attr = {'reporter': reporter, 'owner': owner, 'component': component,
                    'type': type, 'priority': priority, 'status': status}

            if resolution is not None:
                attr['resolution'] = resolution

            # import issue in trac
            id = self.proxy.ticket.create(summary, description, time, attr)

            # import associated comments for issue in trac
            cnum = 0
            for comment in comments:
                cnum += 1
                self.proxy.ticket.update(id, comment['body'], comment['created'],
                                         comment['author'], cnum+1)

            # import associated attachments for issue in trac
            for attachment in attachments:
                author = attachment['author']
                description = ''
                key = issue['key']
                created = attachment['created']
                filename = attachment['filename']
                path = self._get_attachment_path(attachment['attachmentId'], key,
                                               filename)
                if os.path.exists(path):
                    file = open(path, 'rb').read()
                    data = client.Binary(file)
                    self.proxy.ticket.putAttachment(id, filename, description,
                                            data, author, created, False)
            progress.update()

        log.info('  {} Actions'.format(len(self.jiraData['actions'])))
        log.info('  {} Attachments'.format(len(self.jiraData['attachments'])))

    def _get_attachment_path(self, id, key, filename):
        project = key.rsplit('-')[0]
        file = '{}_{}'.format(id, filename)
        path = os.path.join(self.attachments, project, key, file)
        return path

    def _get_item(self, id, target, field='name'):
        for d in self.jiraData[target]:
            if d['id'] == id:
                return d[field]

    def _get_comments(self, id):
        # grab associated comments for issue
        comments = []
        for action in self.jiraData['actions']:
            if action['issue'] == id:
                body = action['body']
                created = action['created']
                author = action['author']
                comment = {'id': action['issue'], 'body': body,
                           'created': created, 'author': author,
                           'commentId': int(action['id'])}
                comments.append(comment)

        # sort comments with oldest id first
        return sorted(comments, key=itemgetter('commentId'), reverse=True)

    def _get_attachments(self, id):
        # grab associated attachments for issue
        attachments = []
        for attachment in self.jiraData['attachments']:
            if attachment['issue'] == id:
                mimetype = attachment['mimetype']
                created = attachment['created']
                author = attachment['author']
                filename = attachment['filename']
                filesize = attachment['filesize']
                att = {'id': attachment['issue'], 'mimetype': mimetype,
                        'created': created, 'author': author,
                        'attachmentId': int(attachment['id']),
                        'filename': filename, 'filesize': filesize}
                attachments.append(att)

        # sort attachments with oldest id first
        return sorted(attachments, key=itemgetter('attachmentId'), reverse=False)


if __name__ == "__main__":
    from jira2trac.scripts import run
    run()
