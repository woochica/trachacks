Attribute VB_Name = "MultiPrjTicketEdit"
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

Sub import()
    Dim user As String, pw As String, URL As String, projectNames As String, projectName As String, query As String
    
    Dim settingSheet As Worksheet
    Set settingSheet = Sheet1
    
    URL = settingSheet.Cells(2, 3).value
    If settingSheet.Cells(5, 3).value = True Then
        Dim frm As PwDlg
        Set frm = New PwDlg
        frm.Show
        user = frm.TextBox1.value
        pw = frm.TextBox2.value
        Unload frm
    Else
        user = settingSheet.Cells(6, 3).value
        pw = settingSheet.Cells(7, 3).value
    End If
    projectNames = settingSheet.Cells(3, 3).value
    query = settingSheet.Cells(4, 3).value

    Dim te As TicketEdit
    Dim name As Variant
    projects = Split(projectNames, ",")
    For Each name In projects
        projectName = Trim(name)
        Set te = New TicketEdit
        On Error GoTo notExistSheet
        Set s = ActiveWorkbook.Worksheets.Item(projectName)
        On Error GoTo 0
        te.init URL, projectName, user, pw, projectName
        If query <> "" Then
            te.import ("<value><string>" & query & "</string></value>")
        Else
            te.import ("")
        End If
    Next
    MsgBox "Complete"
    Exit Sub
notExistSheet:
    MsgBox projectName & " sheet does not exist."
End Sub

Sub check()
    Dim user As String, pw As String, URL As String, projectNames As String, projectName As String
    
    Dim settingSheet As Worksheet
    Set settingSheet = Sheet1
    
    URL = settingSheet.Cells(2, 3).value
    If settingSheet.Cells(5, 3).value = True Then
        Dim frm As PwDlg
        Set frm = New PwDlg
        frm.Show
        user = frm.TextBox1.value
        pw = frm.TextBox2.value
        Unload frm
    Else
        user = settingSheet.Cells(6, 3).value
        pw = settingSheet.Cells(7, 3).value
    End If
    projectNames = settingSheet.Cells(3, 3).value

    Dim te As TicketEdit
    Dim name As Variant
    projects = Split(projectNames, ",")
    For Each name In projects
        projectName = Trim(name)
        Set te = New TicketEdit
        On Error GoTo notExistSheet
        Set s = ActiveWorkbook.Worksheets.Item(projectName)
        On Error GoTo 0
        te.init URL, projectName, user, pw, projectName
        te.check
    Next
    MsgBox "Complete"
    Exit Sub
notExistSheet:
    MsgBox projectName & " sheet does not exist."
End Sub

Sub update()
    Dim user As String, pw As String, URL As String, projectNames As String, projectName As String
    
    Dim settingSheet As Worksheet
    Set settingSheet = Sheet1
    
    URL = settingSheet.Cells(2, 3).value
    If settingSheet.Cells(5, 3).value = True Then
        Dim frm As PasswordDlg
        Set frm = New PasswordDlg
        frm.Show
        user = frm.TextBox1.value
        pw = frm.TextBox2.value
        Unload frm
    Else
        user = settingSheet.Cells(6, 3).value
        pw = settingSheet.Cells(7, 3).value
    End If
    projectNames = settingSheet.Cells(3, 3).value

    Dim te As TicketEdit
    Dim name As Variant
    projects = Split(projectNames, ",")
    For Each name In projects
        projectName = Trim(name)
        Set te = New TicketEdit
        On Error GoTo notExistSheet
        Set s = ActiveWorkbook.Worksheets.Item(projectName)
        On Error GoTo 0
        te.init URL, projectName, user, pw, projectName
        te.update
    Next
    MsgBox "Complete"
    Exit Sub
notExistSheet:
    MsgBox projectName & " sheet does not exist."
End Sub

