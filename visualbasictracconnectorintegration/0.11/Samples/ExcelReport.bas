Attribute VB_Name = "ExcelReport"
'Copyright (c) 2009 Yuji OKAZAKI. All rights reserved.
'
'Redistribution and use in source and binary forms, with or without modification, are permitted provided
'that the following conditions are met:
'
' 1. Redistributions of source code must retain the above copyright notice, this list of conditions and
'   the following disclaimer.
' 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
'   and the following disclaimer in the documentation and/or other materials provided with the
'   distribution.
'
'THIS SOFTWARE IS PROVIDED BY THE FREEBSD PROJECT ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
'INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
'A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE FREEBSD PROJECT OR CONTRIBUTORS BE LIABLE
'FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
'NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
'OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
'STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
'THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Dim trac As TracXMLRPC
Dim s As Worksheet
Dim owner As String

Function initSheet(dBefore As String, dReport As String, dNext As String) As Integer
    s.Cells(1, 3).value = "作業進捗報告"
    s.Cells(1, 3).HorizontalAlignment = xlCenter
    s.Cells(2, 4).value = "報告日：" & dReport
    s.Cells(2, 4).HorizontalAlignment = xlRight
    s.Cells(3, 4).value = "期間：" & dBefore & " - " & dNext
    s.Cells(3, 4).HorizontalAlignment = xlRight
    s.Cells(4, 4).value = "報告者："
    s.Cells(4, 4).HorizontalAlignment = xlRight
    initSheet = 5
    s.Range(s.Rows(initSheet), s.Rows(65536)).Delete xlUp
End Function

Public Function importClosedTickets(row As Integer, pre As String, dStart As String) As Integer
    Dim t1 As Collection
    Dim query As String
    query = "<string>status=closed&amp;owner=" & owner & "</string>"
    Set t1 = trac.queryTicket(query)
    Dim no As Integer
    no = 1
    
    On Error Resume Next
    For Each t In t1
        due_assign = due_close = complete = ""
        due_assign = t.Item("due_assign")
        due_close = t.Item("due_close")
        complete = t.Item("complete")
        If due_close >= dStart Then
            s.Cells(row, 2).value = pre & no & ". " & t.Item("summary") & "(" & t.Item("id") & ")"
            work = due_assign & "-" & due_close
            If complete <> "" Then work = work & "(" & complete & "%)"
            s.Cells(row, 4).value = work
            s.Cells(row, 4).HorizontalAlignment = xlRight
            row = row + 1
            work = ""
            work = t.Item("description")
            work = Replace(work, "[[BR]]", vbCrLf)
            s.Cells(row, 3).value = work
            row = row + 1
            no = no + 1
        End If
    Next
    On Error GoTo 0
    importClosedTickets = row
End Function

Public Function importWorkingTickets(row As Integer, pre As String, dReport As String, dEnd As String) As Integer
    Dim t1 As Collection
    Dim query As String
    query = "<string>status!=closed&amp;owner=" & owner & "</string>"
    Set t1 = trac.queryTicket(query)
    Dim no As Integer
    no = 1
    
    On Error Resume Next
    For Each t In t1
        due_assign = due_close = complete = ""
        due_assign = t.Item("due_assign")
        due_close = t.Item("due_close")
        complete = t.Item("complete")
        If due_assign <= dReport Then
            s.Cells(row, 2).value = pre & no & ". " & t.Item("summary") & "(" & t.Item("id") & ")"
            work = due_assign & "-" & due_close
            If complete <> "" Then work = work & "(" & complete & "%)"
            s.Cells(row, 4).value = work
            s.Cells(row, 4).HorizontalAlignment = xlRight
            row = row + 1
            work = ""
            work = t.Item("description")
            work = Replace(work, "[[BR]]", vbCrLf)
            s.Cells(row, 3).value = work
            row = row + 1
            no = no + 1
        End If
    Next
    On Error GoTo 0
    importWorkingTickets = row
End Function

Public Function importDueAssignTickets(row As Integer, pre As String, dReport As String, dEnd As String) As Integer
    Dim t1 As Collection
    Dim query As String
    query = "<string>status!=closed&amp;owner=" & owner & "</string>"
    Set t1 = trac.queryTicket(query)
    Dim no As Integer
    no = 1
    
    On Error Resume Next
    For Each t In t1
        due_assign = due_close = complete = ""
        due_assign = t.Item("due_assign")
        due_close = t.Item("due_close")
        complete = t.Item("complete")
        If due_assign > dReport And due_assign <= dEnd Then
            s.Cells(row, 2).value = pre & no & ". " & t.Item("summary") & "(" & t.Item("id") & ")"
            work = due_assign & "-" & due_close
            If complete <> "" Then work = work & "(" & complete & "%)"
            s.Cells(row, 4).value = work
            s.Cells(row, 4).HorizontalAlignment = xlRight
            row = row + 1
            work = ""
            work = t.Item("description")
            work = Replace(work, "[[BR]]", vbCrLf)
            s.Cells(row, 3).value = work
            row = row + 1
            no = no + 1
        End If
    Next
    On Error GoTo 0
    importDueAssignTickets = row
End Function

Sub createReport()
    Dim user As String, pw As String, URL As String, projectName As String
    
    Dim settingSheet As Worksheet
    Set settingSheet = Sheet1
    
    URL = settingSheet.Cells(14, 3).value
    projectName = settingSheet.Cells(15, 3).value
    user = settingSheet.Cells(16, 3).value
    pw = settingSheet.Cells(17, 3).value
    owner = settingSheet.Cells(18, 3).value
    
    Set s = Application.ActiveWorkbook.Sheets.Item("Report")
    Dim dBefore As String
    Dim dReport As String
    Dim dNext As String
    Dim row As Integer
    
    dBefore = settingSheet.Cells(19, 3).value
    dReport = settingSheet.Cells(20, 3).value
    dNext = settingSheet.Cells(21, 3).value
    
    Set trac = New TracXMLRPC
    trac.init URL, projectName, user, pw
    row = initSheet(dBefore, dReport, dNext) '
    s.Cells(row, 1).value = "1. 期間内にクローズ済みのチケット"
    row = importClosedTickets(row + 1, "1.", dBefore)
    s.Cells(row, 1).value = "2. 作業中のチケット"
    row = importWorkingTickets(row + 1, "2.", dReport, dNext)
    s.Cells(row, 1).value = "3. 開始予定のチケット"
    row = importDueAssignTickets(row + 1, "3.", dReport, dNext)
    s.Cells(row + 1, 1).value = "以上"
End Sub


