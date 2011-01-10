## -*- coding: utf-8 -*-
#Open Flash Chart - Python libraries. These help create data files for Open Flash Chart.
#Copyright (C) 2007 John Glazebrook, Guenther Harrasser
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#Slightly modified to allow relative width and/or height.
from trac.util.html import Markup
class graph_object:
	def render( self, width, height, url, ofc_base_url="/", ofc_swf="open-flash-chart.swf", ofc_id="open-flash-chart" ):
		return Markup("""<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://fpdownload.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=8,0,0,0" width="%(width)s" height="%(height)s" id="%(ofc_id)s" align="middle">
<param name="allowScriptAccess" value="sameDomain" />
<param name="movie" value="%(ofc_base_url)s%(ofc_swf)s?width=%(width)s&height=%(height)s&data=%(url)s" />
<param name="quality" value="high" /><param name="bgcolor" value="#FFFFFF" />
<embed src="%(ofc_base_url)s%(ofc_swf)s?width=%(width)s&height=%(height)s&data=%(url)s" quality="high" bgcolor="#FFFFFF" width="%(width)s" height="%(height)s" name="%(ofc_id)s" align="middle" allowScriptAccess="sameDomain" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" />
</object>""" % locals())

class graph:
	def __init__(self):
		self.data = []
		self.x_labels = []
		self.y_min = 0
		self.y_max = 20
		self.y_steps = 5
		self.title_text = ''
		self.title_size = 30
		
		self.x_tick_size = -1

		# GRID styles:
		self.x_axis_colour = ''
		self.x_grid_colour = ''

		self.y_axis_colour = ''
		self.y_grid_colour = ''
		self.x_axis_steps = 1


		# AXIS LABEL styles:         
		self.x_label_style_size = -1
		self.x_label_style_colour = '#000000'
		self.x_label_style_orientation = 0
		self.x_label_style_step = 1

		self.y_label_style_size = -1
		self.y_label_style_colour = '#000000'
		

		# AXIS LEGEND styles:
		self.x_legend = ''
		self.x_legend_size = 20
		self.x_legend_colour = '#000000'

		self.y_legend = ''
		self.y_legend_size = 20
		self.y_legend_colour = '#000000'
		
		self.lines = []
		self.line_default = '&line=3,#87421F&' + "\r\n"
		
		self.bg_colour = ''
		self.bg_image = ''

		self.inner_bg_colour = ''
		self.inner_bg_colour_2 = ''
		self.inner_bg_angle = ''

	def set_data( self, a ):
		if( len( self.data ) == 0 ):
			self.data.append( '&values=%s&\r\n' % ','.join([str(v) for v in a]) )
		else:
			self.data.append( '&values_%s=%s&\r\n' % (len(self.data)+1, ','.join([str(v) for v in a])) )
    
	def set_x_labels( self, a ):
		self.x_labels = a
    
	def set_x_label_style( self, size, colour='', orientation=0, step=-1 ):
		self.x_label_style_size = size

		if( len( colour ) > 0 ):
			self.x_label_style_colour = colour

		if( orientation > 0 ):
			self.x_label_style_orientation = orientation

		if( step > 0 ):
			self.x_label_style_step = step

	def set_bg_colour( self, colour ):
		self.bg_colour = colour

	def set_bg_image( self, url, x='center', y='center' ):
		self.bg_image = url
		self.bg_image_x = x
		self.bg_image_y = y

	def set_inner_background( self, col, col2='', angle=-1 ):
		self.inner_bg_colour = col

		if( len(col2) > 0 ):
			self.inner_bg_colour_2 = col2

		if( angle != -1 ):
			self.inner_bg_angle = angle

	def set_y_label_style( self, size, colour='' ):
		self.y_label_style_size = size

		if( len( colour ) > 0 ):
			self.y_label_style_colour = colour

	def set_y_max( self, max ):
 		self.y_max = int( max )

	def set_y_min( self, min ):
		self.y_min = int( min )
    
	def y_label_steps( self, val ):
		self.y_steps = int( val )
    
	def title( self, title, size=-1, colour='#000000' ):
		self.title_text = title
		if( size > 0 ):
			self.title_size = size
		if( len( colour ) > 0 ):
			self.title_colour = colour
    
	def set_x_legend( self, text, size=-1, colour='' ):
		self.x_legend = text
		if( size > -1 ):
			self.x_legend_size = size
                
		if( len( colour )>0 ):
			self.x_legend_colour = colour
    
	def set_x_tick_size( self, size ):
		if( size > 0 ):
			self.x_tick_size = size

	def set_x_axis_steps( self, steps ):
		if ( steps > 0 ):
			self.x_axis_steps = steps

	def set_y_legend( self, text, size=-1, colour='' ):
		self.y_legend = text
		if( size > -1 ):
			self.y_legend_size = size

		if( len( colour )>0 ):
			self.y_legend_colour = colour
    
	def line( self, width, colour='', text='', size=-1, circles=-1 ):
		tmp = '&line'
		
		if( len( self.lines ) > 0 ):
			tmp += '_%s' % (len( self.lines )+1)
				
		tmp += '='
		
		if( width > 0 ):
			tmp += "%s,%s" % (width, colour)
							
		if( len( text ) > 0 ):
			tmp += ',%s,%s' % (text,size)
			
		if( circles > 0 ):
			tmp += ',%s' % circles
			
		tmp += "&\r\n"
		self.lines.append( tmp )

	def line_dot( self, width, dot_size, colour, text='', font_size=0 ):
		tmp = '&line_dot'
		
		if( len( self.lines ) > 0 ):
				tmp += '_%s' % (len( self.lines )+1)
				
		tmp += "=%s,%s,%s" % (width,colour,text)

		if( font_size > 0 ):
			tmp += ",%s,%s" % (font_size,dot_size)
			
		tmp += "&\r\n"
			
		self.lines.append( tmp )

	def line_hollow( self, width, dot_size, colour, text='', font_size=0 ):
		tmp = '&line_hollow'
		
		if( len( self.lines ) > 0 ):
			tmp += '_%s' % (len( self.lines )+1)
				
		tmp += "=%s,%s,%s" % (width,colour,text)

		if( font_size > 0 ):
			tmp += ",%s,%s" % (font_size,dot_size)
			
		tmp += "&\r\n"
		self.lines.append( tmp )

	def area_hollow( self, width, dot_size, colour, alpha, text='', font_size=0 ):
		tmp = '&area_hollow'
		
		if( len( self.lines ) > 0 ):
				tmp += '_%s' % (len( self.lines )+1)
				
		tmp += "=%s,%s,%s" % (width,dot_size,colour,alpha)

		if( len( text ) > 0 ):
			tmp += ",%s,%s" % (text,font_size)

		tmp += "&\r\n"
		self.lines.append( tmp )

	def bar( self, alpha, colour='', text='', size=-1 ):
		tmp = '&bar'
		
		if( len( self.lines ) > 0 ):
				tmp += '_%s' % (len( self.lines )+1)
				
		tmp += '='
		tmp += "%s,%s,%s,%s" % (alpha,colour,text,size)
		tmp += "&\r\n"
			
		self.lines.append( tmp )

	def bar_filled( self, alpha, colour, colour_outline, text='', size=-1 ):
		tmp = '&filled_bar'
		
		if( len( self.lines ) > 0 ):
				tmp += '_%s' % (len( self.lines )+1)
				
		tmp += "=%s,%s,%s,%s,%s&\r\n" % (alpha,colour,colour_outline,text,size)
			
		self.lines.append( tmp )

	def x_axis_colour( self, axis, grid='' ):
		self.x_axis_colour = axis
		self.x_grid_colour = grid

	def y_axis_colour( self, axis, grid='' ):
		self.y_axis_colour = axis
		self.y_grid_colour = grid

	def render( self,):
		#tmp = "&padding=70,5,50,40&\r\n"
		tmp = ''
		
		if( len( self.title_text ) > 0 ):
			tmp += '&title=%s,%s,%s&\r\n' % (self.title_text,self.title_size,self.title_colour)
		
		if( len( self.x_legend ) > 0 ):
			tmp += '&x_legend=%s,%s,%s\r\n' % (self.x_legend,self.x_legend_size,self.x_legend_colour)
		
		if( self.x_label_style_size > 0 ):
			tmp += '&x_label_style=%s,%s,%s,%s&\r\n' % (self.x_label_style_size,self.x_label_style_colour,self.x_label_style_orientation,self.x_label_style_step)
		
		if( self.x_tick_size > 0 ):
			tmp += "&x_ticks=%s&\r\n" % self.x_tick_size

		if( self.x_axis_steps > 0 ):
			tmp += "&x_axis_steps=%s&\r\n" % self.x_axis_steps

		if( len( self.y_legend ) > 0 ):
			tmp += '&y_legend=%s,%s,%s&\r\n' % (self.y_legend,self.y_legend_size,self.y_legend_colour)

		if( self.y_label_style_size > 0 ):
			tmp += "&y_label_style=%s,%s&\r\n" % (self.y_label_style_size,self.y_label_style_colour)

		tmp += '&y_ticks=5,10,%s&\r\n' % self.y_steps
		
		if( len( self.lines ) == 0 ):
			tmp += self.line_default
		else:
			for line in self.lines:
				tmp += line

		for data in self.data:
			tmp += data
		
		if( len( self.x_labels ) > 0 ):
			tmp += '&x_labels=%s&\r\n' % ",".join(self.x_labels)
						
		tmp += '&y_min=%s&\r\n' % self.y_min
		tmp += '&y_max=%s&\r\n' % self.y_max
		
		if( len( self.bg_colour ) > 0 ):
			tmp += '&bg_colour=%s&\r\n' % self.bg_colour

		if( len( self.bg_image ) > 0 ):
			tmp += '&bg_image=%s&\r\n' % self.bg_image
			tmp += '&bg_image_x=%s&\r\n' % self.bg_image_x
			tmp += '&bg_image_y=%s&\r\n' % self.bg_image_y

		if( len( self.x_axis_colour ) > 0 ):
			tmp += '&x_axis_colour=%s&\r\n' % self.x_axis_colour
			tmp += '&x_grid_colour=%s&\r\n' % self.x_grid_colour

		if( len( self.y_axis_colour ) > 0 ):
			tmp += '&y_axis_colour=%s&\r\n' % self.y_axis_colour
			tmp += '&y_grid_colour=%s&\r\n' % self.y_grid_colour

		if( len( self.inner_bg_colour ) > 0 ):
			tmp += '&inner_background=%s' % self.inner_bg_colour
			if( len( self.inner_bg_colour_2 ) > 0 ):
				tmp += ',%s,%s' % ( self.inner_bg_colour_2, self.inner_bg_angle )
			tmp += "&\r\n"

		return tmp
	

