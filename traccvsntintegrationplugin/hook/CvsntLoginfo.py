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
        self.nfiles = len(argv1split)-1
        files = ''
        newrevs = ''
        oldrevs = ''
        for i in range(1, self.nfiles+1):
            s = argv1split[i].rsplit(',',2)
            if i != 1:
                files += ' '
                newrevs += ' '
                oldrevs += ' '
            files += s[0] 
            newrevs += s[1] 
            oldrevs += s[2] 
        self.files = files.split()
        self.newrevs = newrevs.split()
        self.oldrevs = oldrevs.split()

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
