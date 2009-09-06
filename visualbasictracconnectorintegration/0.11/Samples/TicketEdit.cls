VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "TicketEdit"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
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

Dim m_URL As String
Dim m_projectName As String
Dim m_user As String
Dim m_pw As String
Dim m_sheet As Worksheet

Dim m_initialized As Boolean

Private Sub Class_Initialize()
    m_initialized = False
End Sub

Public Property Get URL() As String
    URL = m_URL & "/" & m_projectName
End Property

Public Sub init(URL As String, projectName As String, user As String, pw As String, sheetName As String)
    m_URL = URL
    m_projectName = projectName
    m_user = user
    m_pw = pw
    m_initialized = True
    Set m_sheet = ActiveWorkbook.Worksheets.Item(sheetName)
End Sub

'取得したチケットで一行データをうめます
Sub fillRow(row As Integer, ticket As Collection)
    Dim i As Integer
    i = 1
    Do
        If m_sheet.Cells(1, i).value = "" Then Exit Do
        m_sheet.Cells(row, i).value = ""
        work = m_sheet.Cells(1, i).comment.text
        Debug.Print "work=" & work
        On Error Resume Next
        m_sheet.Cells(row, i).value = ticket.Item(work)
        On Error GoTo 0
        i = i + 1
    Loop
End Sub


Sub import(query As String)
    Dim attributes As Collection
    Dim ticketId As Long
    Dim s As Worksheet
    Dim row As Integer
    Set s = m_sheet
    Dim devTrac As TracXMLRPC
    Set devTrac = New TracXMLRPC
    devTrac.init m_URL, m_projectName, m_user, m_pw
    Set fields = devTrac.field
    i = 1
    
    On Error Resume Next
    s.Cells.ClearComments
    On Error GoTo 0
    s.Cells.Delete Shift:=xlUp

    s.Cells(1, i).value = "ID"
    On Error Resume Next
    s.Cells(1, i).AddComment
    s.Cells(1, i).comment.Visible = False
    s.Cells(1, i).comment.text text:="id"
    On Error GoTo 0
    'setVaridationInteger
    setVaridationInteger s.Range(s.Cells(2, i), s.Cells(65536, i)), "1", "2000000000"
    i = i + 1
    For Each field In fields
        Debug.Print "name=" & field.Item("name")
        Debug.Print "type=" & field.Item("type")
        On Error Resume Next
        s.Cells(1, i).value = field.Item("label")
        s.Cells(1, i).AddComment
        s.Cells(1, i).comment.Visible = False
        s.Cells(1, i).comment.text text:=field.Item("name")
        On Error GoTo 0

        Select Case field.Item("type")
        Case "select"
            Debug.Print "select"
            Debug.Print "options=" & field.Item("options")
            setValidationString s.Range(s.Cells(2, i), s.Cells(65536, i)), field.Item("options")
        Case "checkbox"
            Debug.Print "checkbox"
            setValidationString s.Range(s.Cells(2, i), s.Cells(65536, i)), "0 1"
        Case "radio"
            Debug.Print "radio"
            Debug.Print "options=" & field.Item("options")
            setValidationString s.Range(s.Cells(2, i), s.Cells(65536, i)), field.Item("options")
'        Case "text"
'        Case "textarea"
        Case Else
            s.Range(s.Cells(2, i), s.Cells(65536, i)).Validation.Delete
        End Select
        i = i + 1
    Next
    Set Tickets = devTrac.queryTicket(query)
    row = 2
    For Each ticket In Tickets
        Dim cTicket As Collection
        Set cTicket = ticket
        fillRow row, cTicket
        row = row + 1
    Next
End Sub

Sub check()
    Dim row As Integer
    Dim attributes As Collection
    Dim ticketId As Long
    Dim id As String
    Dim s As Worksheet
    Set s = m_sheet
    
    Dim devTrac As TracXMLRPC
    Set devTrac = New TracXMLRPC
    devTrac.init m_URL, m_projectName, m_user, m_pw
    
    Set attributes = New Collection
    
    On Error GoTo err_sheet_format
    i = 1
    Do
        If s.Cells(1, i).value = "" Then Exit Do
        If s.Cells(1, i).comment.text = "" Then
            MsgBox "The label, " & s.Cells(1, i).value & " has no field name."
            Exit Sub
        End If
        i = i + 1
        'setColor
    Loop
    If s.Cells(1, 1).comment.text <> "id" Then
        MsgBox "Cell A1' comment is not id.'"
        Exit Sub
    End If
    If s.Cells(1, 2).comment.text <> "summary" Then
        MsgBox "B1のコメントがsummaryではありません．"
        Exit Sub
    End If
    i = 1
    row = 2
    Do
        id = s.Cells(row, 1).value
        If s.Cells(row, 2).value = "" Then Exit Do
        If id <> "" Then
            Set attributes = devTrac.getTicket(id)
            i = 2
            Do
                Debug.Print "loop:" & i
                If s.Cells(1, i).value = "" Then Exit Do
                fieldName = s.Cells(1, i).comment.text
                Dim v As String, fieldValue As String
                v = s.Cells(row, i).value
                On Error Resume Next
                clearColor s.Cells(row, i)
                fieldValue = ""
                fieldValue = attributes.Item(fieldName)
                If v <> fieldValue Then
                    setColor s.Cells(row, i)
                End If
                On Error GoTo 0
                i = i + 1
            Loop
        Else
            '一行丸ごと
            i = 2
            Do
                If s.Cells(1, i).value = "" Then Exit Do
                v = s.Cells(row, i).value
                If v <> "" Then
                    setColor s.Cells(row, i)
                End If
                i = i + 1
            Loop
        End If
        row = row + 1
    Loop
    Exit Sub
err_sheet_format:
    MsgBox "先頭行のフォーマットに誤りがあります"
End Sub

Sub update()
    Dim row As Integer
    Dim attributes As Collection
    Dim ticketId As Long
    Dim id As String, summary As String, description As String
    
    Dim s As Worksheet
    Set s = m_sheet
    
    Dim devTrac As TracXMLRPC
    Set devTrac = New TracXMLRPC
    devTrac.init m_URL, m_projectName, m_user, m_pw
    
    Set attributes = New Collection
    
    On Error GoTo err_sheet_format
    i = 1
    Do '先頭の行で何か値が入っている場所にコメントがあるか確認する
        If s.Cells(1, i).value = "" Then Exit Do
        If s.Cells(1, i).comment.text = "" Then
            MsgBox "The label, " & s.Cells(1, i).value & " has no field name."
            Exit Sub
        End If
        i = i + 1
        'setColor
    Loop
    If s.Cells(1, 1).comment.text <> "id" Then
        MsgBox "A1のコメントがidではありません．"
        Exit Sub
    End If
    If s.Cells(1, 2).comment.text <> "summary" Then
        MsgBox "B1のコメントがsummaryではありません．"
        Exit Sub
    End If
    i = 1
    row = 2
    Do
        id = s.Cells(row, 1).value
        If s.Cells(row, 2).value = "" Then Exit Do
        If id <> "" Then
            Dim newAttributes As Collection
            Set attributes = devTrac.getTicket(id)
            Set newAttributes = New Collection
            i = 2
            Do
                Debug.Print "loop:" & i
                If s.Cells(1, i).value = "" Then Exit Do
                fieldName = s.Cells(1, i).comment.text
                Dim v As String, fieldValue As String
                v = s.Cells(row, i).value
                On Error Resume Next
                clearColor s.Cells(row, i)
                fieldValue = ""
                fieldValue = attributes.Item(fieldName)
                If v <> fieldValue Then
                    setColor s.Cells(row, i)
                    newAttributes.Add v, fieldName
                End If
                On Error GoTo 0
                i = i + 1
            Loop
            If newAttributes.Count > 0 Then
                Set newAttributes = devTrac.updateTicket(CLng(id), "Excelより自動追加", newAttributes, False)
                newAttributes.Add id, "id"
                fillRow row, newAttributes
            End If
        Else
            '一行丸ごと
            Set attributes = New Collection
            i = 2
            Do
                If s.Cells(1, i).value = "" Then Exit Do
                fieldName = s.Cells(1, i).comment.text
                v = s.Cells(row, i).value
                clearColor s.Cells(row, i)
                If v <> "" Then
                    attributes.Add v, fieldName
                End If
                i = i + 1
            Loop
            On Error Resume Next
            description = ""
            description = attributes.Item("description")
            attributes.Remove "description"
            summary = ""
            summary = attributes.Item("summary")
            attributes.Remove "summary"
            On Error GoTo 0
            ticketId = devTrac.createTicket(summary, description, attributes, True)
            fillRow row, devTrac.getTicket(CStr(ticketId))
        End If
        row = row + 1
    Loop
    Exit Sub
err_sheet_format:
    MsgBox "先頭行のフォーマットに誤りがあります"
End Sub


