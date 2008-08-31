# This file is part of TracTicketDepgraph.
#
# TracTicketDepgraph is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# TracTicketDepgraph is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Felix Tiede

__all__ = ['get_color', ]

def get_color(priority):
	"""Set up background and border color for given priority"""
	if priority == "blocker" or priority == "P1":
		bgcolor = "#ffddcc"
		border  = "#ee8888"
	elif priority == "critical" or priority == "P2":
		bgcolor = "#ffffbb"
		border  = "#eeeeaa"
	elif priority == "major" or priority == "P3":
		bgcolor = "#f6f6f6"
		border  = "#cccccc"
	elif priority == "minor" or priority == "P4":
		bgcolor = "#ddffff"
		border  = "#bbeeee"
	elif priority == "trivial" or priority == "P5":
		bgcolor = "#dde7ff"
		border  = "#ccddee"
	else:
		bgcolor = "#f6f6f6"
		border  = "#cccccc"
	return [bgcolor, border]
