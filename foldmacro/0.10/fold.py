"""
A TRAC macro for creating foldable tree-like tables.

Homepage:       http://trac-hacks.org/wiki/FoldMacro

Based on:  Folding macro by Thorsten Ott (wanagi at web-helfer.de)

Authors:   Sven Matner (shivoc $at$ rise-world *dot* com)
           Peter Molnar (pm $at$ rise-world *dot* com) 
"""

from trac import util
from trac.wiki.formatter import wiki_to_oneliner
from StringIO import StringIO
import os
import urllib
import re
import random

class Fold:

	re_start = re.compile('^ *<{3} *$')
	re_mid = re.compile('^ *[-=]{3} *$')
	re_end = re.compile('^ *>{3} *$')
	re_spaces = re.compile('^ *$')

	(NORMAL, VISIBLE, HIDDEN) = range(3)

	def __init__(self, hdf, args, env):
		self.state = self.NORMAL
		self.id = int(random.random() * 100000)
		self.out = StringIO()
		self.gid_counter = self.id

		self.gid = 0
		self.marker = ""

		self.stack = []
		self.gids = []
		self.visibility = []

		self.args = args
		self.env = env

	def create_marker(self, label):
		indent = self.depth() * 10;
		return "<span style=\"padding-left: %dpx;\" onclick=\"javascript:switchContent_%d('%d');\">%s</span>" % \
			(indent, self.id, self.gid, label)

	def depth(self):
		return len(self.stack) - 1

	def enter_visible(self):
		self.stack.append((self.gid, self.state))
		self.gid_counter += 1
		self.gid = self.gid_counter
		self.state = self.VISIBLE
		self.marker = self.create_marker('+')
		self.gids.append(str(self.gid))
		self.visibility.append('1')

	def enter_hidden(self):
		self.state = self.HIDDEN
		self.marker = self.create_marker('-')
		self.visibility[-1] = '0'

	def enter_normal(self):
		(self.gid, self.state) = self.stack[-1]
		self.stack = self.stack[:-1]
		self.gids = self.gids[:-1]
		self.visibility = self.visibility[:-1]

	def __call__(self):
		lines = self.args.split('\n')

		print >> self.out
		print >> self.out, "<table class=\"wiki\">"

		for line in lines:
			if self.re_start.match(line):
				self.enter_visible()
			elif self.re_mid.match(line):
				self.enter_hidden()
			elif self.re_end.match(line):
				self.enter_normal()
			elif self.re_spaces.match(line):
				pass
			else:
				self.output_line(line)
				self.marker = ""

		print >> self.out, "</table>"

		self.output_js()

		return self.out.getvalue()

	def output_line(self, line):
		print >> self.out, "\t<tr gid=\"%s\" vis=\"%s\">" % \
			(",".join(self.gids), ",".join(self.visibility))

		cells = re.split(' *\|\| *', line)[1:-1]

		print >> self.out, "\t\t<td>%s</td>" % self.marker
			
		for cell in cells:
			print >> self.out, "\t\t<td>%s</td>" % wiki_to_oneliner(cell, self.env, None)

		print >> self.out, "\t</tr>"

	def output_js(self):
		print >> self.out, """
		<script type='text/javascript'>
		function switchContent_%d(toggleObj) {

			var allTrs = document.getElementsByTagName('tr');
			for (var i = 0; i < allTrs.length; ++i) {
				objName=allTrs[i].getAttribute('gid');
				if (objName) {
					gids = objName.split(",");
					var toggleIndex = -1;
					for (var j = 0; j < gids.length; ++j) {
						if (gids[j] == toggleObj)
							toggleIndex = j;
					}
					if (toggleIndex != -1) {
						var old = allTrs[i].getAttribute('vis').split(",");
						if (old[toggleIndex] == '0') 
							old[toggleIndex] = '1';
						else old[toggleIndex] = '0';
						allTrs[i].setAttribute('vis', old.join(","));
						if (allTrs[i].getAttribute('vis').indexOf('0') != -1)
							allTrs[i].style.display = 'none';
						else
							allTrs[i].style.display = '';
					}
				}
			}
		}

		function switchInitial_%d() {
			var allTrs = document.getElementsByTagName('tr');
			for (var i=0; i<allTrs.length; ++i) {
				target = allTrs[i].getAttribute('vis');
				if (target && target.indexOf('0') != -1)
					allTrs[i].style.display = 'none';
			}
		}

		switchInitial_%d();
		</script>

		""" % (self.id, self.id, self.id)


def execute(hdf, args, env):
	f = Fold(hdf, args, env)
	return f()


# vim:syntax=on:tabstop=4

