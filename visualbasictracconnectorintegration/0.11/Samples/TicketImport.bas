Attribute VB_Name = "TicketImport"
Sub ImportTickets()
    Dim c As TracOutlookConnector
    Set c = New TracOutlookConnector
    c.init "http://trac-hacks.org", "", "", "", "okazaki", "TracHacks"
    c.update
    
'    Dim c2 As TracOutlookConnector
'    Set c2 = New TracOutlookConnector
'    c2.init "http://192.168.1.13/trac", "Test1", "admin", "admin", "admin", "Test1"
'    c2.update
    MsgBox "complete"
End Sub
