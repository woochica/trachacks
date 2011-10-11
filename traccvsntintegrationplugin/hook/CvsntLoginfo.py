# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import time

class CvsntLoginfo():
    def __init__(self, repos):
        self.repos = repos
        self.path = ''
        self.user = ''
        self.datetime = 0.0
        self.nfiles = 0
        self.filenames = []
        self.newrevs = []
        self.oldrevs = []
        self.log_message = ''

    def get_loginfo_from_argv(self, argv):
        self.datetime = time.time()
        self.user = argv[2]
        #argv[1] contains the folder relative to the folder followed by triplets filename,revision_new,revision_old
        argv1split = argv[1].split() 
        #handle whitespaces in file names 
        _argv1split = []
        _argv1split_tmp = ''
        for i in range(0, len(argv1split)):
            _argv1split_tmp = _argv1split_tmp + argv1split[i]
            if _argv1split_tmp.endswith('\\'):
                l = len(_argv1split_tmp)
                _argv1split_tmp = _argv1split_tmp[:l-1] + ' '
            else:
                _argv1split.append(_argv1split_tmp)
                _argv1split_tmp = ''
        self.nfiles = len(_argv1split)-1
        self.files = []
        self.newrevs = []
        self.oldrevs = []
        for i in range(1, self.nfiles+1):
            s = _argv1split[i].rsplit(',',2)
            self.files.append(s[0]) 
            self.newrevs.append(s[1])
            self.oldrevs.append(s[2])

    class ParseState:
        GET_PATH=0
        SKIP_DIRECTORY=1
        SKIP_FILES=2
        GET_LOG_MESSAGE=3

    def get_loginfo_from_stdin(self):
        state = self.ParseState.GET_PATH
        while True: 
            try: 
                nextline = raw_input() 

                strUpdateOfRepos = 'Update of ' + self.repos + '/';

                if state == self.ParseState.GET_PATH and nextline.find(strUpdateOfRepos) == 0:
                    self.path = nextline.lstrip(strUpdateOfRepos)
                    state = self.ParseState.SKIP_DIRECTORY
                elif state == self.ParseState.SKIP_DIRECTORY and nextline.find('Modified Files:') == 0:
                    state = self.ParseState.SKIP_FILES
                elif state == self.ParseState.SKIP_FILES:
                    if nextline.find('Log Message:') == 0:
                        state = self.ParseState.GET_LOG_MESSAGE
                elif state == self.ParseState.GET_LOG_MESSAGE:
                   if self.log_message != '':
                       self.log_message += '\n'
                   self.log_message += nextline               
            except EOFError: 
                break
