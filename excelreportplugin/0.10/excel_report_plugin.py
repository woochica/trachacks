""" Report renderer for Excel .xls format """

from trac.core import *
from trac.ticket.report import ITicketReportRenderer
from trac.ticket.web_ui import TicketModule
from trac.ticket.query import QueryModule
from pyExcelerator import * 

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
	       
		sheetname = sheetname.replace('/','-') 
		try:
		    ws = wb.add_sheet(sheetname.decode('utf-8')) 
	        except: 
	            ws = wb.add_sheet(sheetname) 
		ws.panes_frozen = True 
	        ro = 1 
	        ws.horz_split_pos = ro 
	 
	        import copy 
	 
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
	 
	        style0 = XFStyle() 
	        style0.font = font0 
	        style0.alignment = align1 
	        style0.num_format_str = 'general' 
	        style_colheader = copy.copy(style0) 
	        style_colheader.num_format_str = '@' 
	        style_colheader.font = font1 
	        style_num = copy.copy(style0) 
	        style_str = copy.copy(style0) 
	        style_str.num_format_str = '@' 
	        style_wrap_str = copy.copy(style0) 
	        style_wrap_str.alignment = align2 
	        style_wrap_str.font = font2 
	        style_date = copy.copy(style0) 
	        style_date.num_format_str = 'yyyy/mm/dd' 
	 
	        for col, cx in map(lambda x, y: [x, y], cols, range(len(cols))): 
	           
		    name = str(col).replace('_','') 
	            ws.write(ro-1, cx, name.decode('utf-8'), style_colheader) 
	           
	            def conv(x):
		        try:	
			    a = str(x).replace('\r','').rstrip('\r\n').decode('utf-8') 
	                except:
	                    return x.replace('\r','').rstrip('\r\n')
			return a
	
	            style = style_str 
	            if name in ['time', 'date','changetime', 'created', 'modified']: 
	                ws.col(cx).width = 0xb00 
	                from datetime import datetime 
	                conv = lambda x: datetime.fromtimestamp(float(x)) 
	                style = style_date 
	            elif name in ['summary', 'description']: 
	                if name == 'description': 
	                    ws.col(cx).width = 0x7000 
	                else: 
	                    ws.col(cx).width = 0x1a00 
	                style = style_wrap_str 
	            elif name in ['color', 'ticket', 'id']: 
	                if name in ['color']: 
	                    ws.col(cx).hidden = 1 
	                conv = lambda x: int(x) 
	                style = style_num 
	            elif name in ['style']: 
	                ws.col(cx).hidden = 1 
	            elif name == "component":
			ws.col(cx).width = 0x1a00 
		    for value, rx in map(lambda x, y: [conv(x[cx]), ro + y], \
	                                 rows, range(len(rows))): 
	                ws.write(rx, cx, value, style) 
	        req.write(wb.get())     

		
			
		
