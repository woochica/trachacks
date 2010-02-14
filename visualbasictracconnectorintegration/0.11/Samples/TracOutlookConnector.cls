VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "TracOutlookConnector"
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

Dim Trac As TracXMLRPC
Dim prjID As String
Dim owner As String

Private Sub Class_Initialize()
End Sub

Public Function init(URL As String, projectName As String, user As String, pw As String, ownerName As String, projectID As String)
    Set Trac = New TracXMLRPC
    Trac.init URL, projectName, user, pw
    prjID = projectID
    owner = ownerName
End Function

Sub update()
    Dim addr As String
    Dim i As TaskItem
    Dim tracItem As TaskItem
    addr = Trac.URL & "/ticket/"
    
    Set objNamespace = Application.GetNamespace("MAPI")
    Dim objFolder As MAPIFolder
    Set objFolder = objNamespace.GetDefaultFolder(olFolderTasks)
    Set colTasks = objFolder.Items
    
    Dim c As Collection
'    Set c = trac.queryTicket("<string>status!=closed&amp;owner=" & owner & "</string>")
    Set c = Trac.queryTicket("<string>owner=" & owner & "</string>")
    Set fields = Trac.field()
    If Not c Is Nothing Then
        '取得できたチケットについて情報を更新する
        For Each t In c
            Dim f As Boolean
            Dim tId As String
            'チケットとTaskが一致するかを比較するための文字列を作る．
            tId = prjID & ":#" & t.Item("id") & " " 'スペースを入れておかないと前方一致で引っかかることがある．
            f = False
            
            For j = 1 To colTasks.Count
                Set i = colTasks.Item(j)
                If InStr(1, i.Subject, tId) = 1 Then
                    Set tracItem = i
                    f = True
                    Exit For
                End If
            Next
            If f = False Then
                Set tracItem = Application.CreateItem(olTaskItem)
            End If
            On Error Resume Next
            tracItem.StartDate = t.Item("due_assign")
            tracItem.DueDate = t.Item("due_close")
            On Error GoTo 0
            
            If tracItem.StartDate <> #1/1/4501# And tracItem.StartDate <> #1/1/4501# Then
                tracItem.Subject = tId & _
                            Format(tracItem.StartDate, " MM/DD-") & _
                            Format(tracItem.DueDate, "MM/DD ") & _
                            t.Item("summary")
            Else
                tracItem.Subject = tId & " " & t.Item("summary")
            End If
            
            tracItem.Body = addr & t.Item("id") & vbCrLf & _
                            "Do not edit this task item." & vbCrLf & _
                            t.Item("description")
            
            If t.Item("status") = "closed" Then
                tracItem.PercentComplete = 100
            Else
                tracItem.PercentComplete = 0
                On Error Resume Next
                tracItem.PercentComplete = t.Item("complete")
                On Error GoTo 0
            End If
            tracItem.Save
        Next
    End If
    
End Sub




