# vim: expandtab tabstop=4
import re
import neo_util
import pickle
from os import mkdir
from binascii import crc32

# Set this to where you want the poll state to be stored
polldir = "/var/state/trac/polls"

def title2label(title):
	return hex(crc32(title))[2:]

class Poll:
    def __init__(self, path, title, options):
        self.path = path
        self.label = title2label(title)
        self.title = title
        self.options = []
        # Set defaults
        for option in options:
            self.options.append([option, {}])

        # Restore on-disk representation first
        try:
            merge = pickle.load(open(self.path, "r"))
            for i, option in enumerate(merge):
                self.options[i][1] = merge[i][1]
        except:
            pass
        # Then "overwrite"
        for i, option in enumerate(options):
            self.options[i][0] = option

    def render(self, hdf):
        commit = 0
        html = "<form action='#%s' method='get'>\n" % self.label
        html += "<a name='%s'></a>" % self.label
        html += "<fieldset>\n<legend>%s</legend>\n" % self.title
        html += "<input type='hidden' name='poll' value='%s'>\n" % self.label

        user = hdf.getValue("trac.authname", "")

        error = ""

        # Check for existing vote
        if hdf.getValue("args.poll", "") == self.label:
            for i, option in enumerate(self.options):
                if hdf.getValue("trac.authname", "") in option[1] and int(hdf.getValue("args.pollvalue", "")) != i:
                    error = "<div class='system-message'><strong>Changed your vote.</strong></div>\n"
                    del(self.options[i][1][user])
                    commit = 1

        for i, option in enumerate(self.options):
            label = title2label(option[0])
            checked = ""
            if hdf.getValue("args.poll", "") == self.label and int(hdf.getValue("args.pollvalue", "")) == i:
                self.options[i][1][user] = 1
                commit = 1
            if hdf.getValue("trac.authname", "") in self.options[i][1]:
                checked = "checked"
            voters = ""
            if len(option[1]):
                voters = " <strong>(%s)</strong>" % ", ".join(option[1].keys())
            html += "<input type='radio' name='pollvalue' value='%i'%s> %s%s<br>\n" % (i, checked, option[0], voters)
        html += "<input type='submit' value='Vote'>\n"
        html += error
        html += "</fieldset>\n"
        html += "</form>\n"

        if commit:
            try:
                pickle.dump(self.options, open(self.path, "w"))
            except:
                pass
        return html

def execute(hdf, txt, env):
    args = re.split('\s*;\s*', txt)
    path = "%s/%s" % (polldir, title2label(hdf.getValue("project.name.encoded", "default")))
    try:
        mkdir(path)
    except:
        pass
    path += "/%s.p" % title2label(args[0])
    poll = Poll(path, args.pop(0), args)
    return poll.render(hdf)# + "<pre>" + hdf.dump() + "</pre>"
