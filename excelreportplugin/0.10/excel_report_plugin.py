""" Report renderer for Excel .xls format """

from trac.core import *
from trac.ticket.report import ITicketReportRenderer
from trac.ticket.web_ui import TicketModule
from trac.ticket.query import QueryModule
from pyExcelerator import * 
from datetime import datetime 
import copy
import types

class XlsDoc(CompoundDoc.XlsDoc): 
    def get(self, stream): 
        padding = '\x00' * (0x1000 - (len(stream) % 0x1000)) 
        self.book_stream_len = len(stream) + len(padding) 
        self.__build_directory() 
        self.__build_sat() 
        self.__build_header() 
        return '%s%s%s%s%s%s%s' % ( 
            self.header, 
            self.packed_MSAT_1st, 
            stream, 
            padding, 
            self.packed_MSAT_2nd, 
            self.packed_SAT, 
            self.dir_stream) 

class Workbook(Workbook): 
    def get(self): 
       doc = XlsDoc() 
       return doc.get(self.get_biff_data()) 


class ReportToExcel(Component):
	implements (ITicketReportRenderer)
	
	# ITicketRerportRenderer
	def get_report_format(self):
		return 'xls'
		
	def get_report_mimetype(self):
		return 'application/vnd.ms-excel'
		
	def get_report_linkname(self):
		return 'Excel'
		  
	def get_report_linkclass(self):
		return None #'xls'
					
	def render(self, req, cols, rows): 
		
	        req.send_response(200) 
	        req.send_header('Content-Type', self.get_report_mimetype()) 
	        req.send_header('Content-Disposition', 
	                        'filename=Report%s.xls' % req.hdf['report.id']) 
	        req.end_headers() 
	 
	        wb = Workbook() 
	        sheetname = "%s - %s" % (req.hdf['report.title'], 
	                                 req.hdf['project.name']) 
	       
		
	        ws = wb.add_sheet(self.convertSheetName(sheetname)) 
	        
		ws.panes_frozen = True 
	        ro = 1 
	        ws.horz_split_pos = ro 
	        
	        
	        font0 = Font() 
	        font0.charset = font0.CHARSET_SYS_DEFAULT 
	        font0.name = 'MS UI Gothic' 
	        font1 = copy.copy(font0) 
	        font1.bold = True 
	        font2 = copy.copy(font0) 
	        font2.height = 0x00A0 
	        align0 = Alignment() 
	        align1 = copy.copy(align0) 
	        align1.vert = align1.VERT_TOP 
	        align2 = copy.copy(align1) 
	        align2.wrap = align2.WRAP_AT_RIGHT 
	 
	        self.style0 = XFStyle() 
	        self.style0.font = font0 
	        self.style0.alignment = align1 
	        self.style0.num_format_str = 'general' 
	        self.style_colheader = copy.copy(self.style0) 
	        self.style_colheader.num_format_str = '@' 
	        self.style_colheader.font = font1 
	        self.style_num = copy.copy(self.style0) 
	        self.style_str = copy.copy(self.style0) 
	        self.style_str.num_format_str = '@' 
	        self.style_wrap_str = copy.copy(self.style0) 
	        self.style_wrap_str.alignment = align2 
	        self.style_wrap_str.font = font2 
	        self.style_date = copy.copy(self.style0) 
	        self.style_date.num_format_str = 'yyyy/mm/dd' 
	 
	        for col, cx in map(lambda x, y: [x, y], cols, range(len(cols))): 
	           
		    name = str(col).replace('_','') 
	            ws.write(ro-1, cx, name.decode('utf-8'), self.style_colheader) 
	           
	            conv = self.convertComments
	
	            style = self.style_str 
	            
	            if name in ['time', 'date','changetime', 'created', 'modified',
	            		'hora', 'fecha','cambio'   ,'creado'  ,'modificado']: 
	                ws.col(cx).width = 0xb00 
	                conv = self.convertTimeStamp
	                style = self.style_date 
	                
	            elif name in ['summary','resumen']:
	            	ws.col(cx).width = 0x1a00 
	                style = self.style_wrap_str 
	                
	            elif name in ['description','descripcion']:
	                ws.col(cx).width = 0x7000 
	                style = self.style_wrap_str 
	                
	            elif name in ['color', 'ticket', 'id']: 
	                if name in ['color']: 
	                    ws.col(cx).hidden = 1 
	                conv = self.convertInteger 
	                style = self.style_num 
	            elif name in ['style']: 
	                ws.col(cx).hidden = 1 
	            elif name == "component":
			ws.col(cx).width = 0x1a00 
			
			
		    for value, rx in map(lambda x, y: [conv(x[cx]), ro + y], \
	                                 rows, range(len(rows))): 
	           	if type(value) is int:
	           		ws.write(rx, cx, value, self.style_num) 
	           	elif type(value) is datetime:
	           		ws.write(rx, cx, value, self.style_date) 
	           	elif type(value) is types.NoneType:
	           		ws.write(rx, cx, '-',self.style_str)
	           	else:
	           		ws.write(rx, cx, value, style) 
	           	
	           	
	           		
	           
	        req.write(wb.get())     

	def convertComments(self, x):
		try:	
			if type(x) is types.NoneType:
				return x
			else:
				return str(x).replace('\r','').rstrip('\r\n').decode('utf-8') 
	    	except:
			return x.replace('\r','').rstrip('\r\n')
		
	
	def convertTimeStamp(self,timestamp):
		
		try:
			return datetime.fromtimestamp(float(timestamp)) 
		except:
			return timestamp
		
	def convertInteger(self,value):
		try:
			return int(value)
		except:
			return value
			
	def convertSheetName(self, sheetname):
		
		sheetname = sheetname.replace('/','-') 
		
		try:
			return sheetname.decode('utf-8')
		except:
			return sheetname
			
		  
			
		
