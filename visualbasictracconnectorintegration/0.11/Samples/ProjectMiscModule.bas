Attribute VB_Name = "ProjectMiscModule"
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
Option Explicit

Public Function setOutlineLevel(t As Task, ByVal level As Long)
    Dim olev As Integer
    Dim i As Integer
    olev = t.outlineLevel
    If olev > level Then
        For i = 1 To olev - level
            Call t.OutlineOutdent
        Next
    ElseIf olev < level Then
        For i = 1 To level - olev
            Call t.OutlineIndent
        Next
    End If
End Function

Public Sub addNotes(t As Task, ticket As Collection, planStart As String, planEnd As String, parent As String)
    Dim memo As String
    On Error Resume Next
    
    memo = memo + "Project Name:" + ticket.Item("projectName") + ":#" + ticket.Item("id") + vbCr
    memo = memo + "" + ticket.Item("due_assign") + "-" + ticket.Item("due_close")
    memo = memo + "(" + ticket.Item("complete") + "%)"
    memo = memo + vbCr
    memo = memo + "Beseline:" + ticket.Item(planStart) + "-" + ticket.Item(planEnd) + vbCr
    memo = memo + "summary ticket:" + ticket.Item(parent) + vbCr
    memo = memo + "description:" + ticket.Item("description") + vbCr
    memo = memo + "status:" + ticket.Item("status") + vbCr
    memo = memo + "reporter:" + ticket.Item("reporter") + vbCr
    memo = memo + "cc:" + ticket.Item("cc") + vbCr
    memo = memo + "component:" + ticket.Item("component") + vbCr
    memo = memo + "priority:" + ticket.Item("priority") + vbCr
    memo = memo + "keyword:" + ticket.Item("keyword") + vbCr
    memo = memo + "version:" + ticket.Item("version") + vbCr
    memo = memo + "milestone:" + ticket.Item("milestone") + vbCr
    memo = memo + "owner:" + ticket.Item("owner") + vbCr
    memo = memo + "type:" + ticket.Item("type") + vbCr
    memo = memo + "blocking:" + ticket.Item("blocking") + vbCr
    memo = memo + "blockedby:" + ticket.Item("blockedby") + vbCr
    
    On Error GoTo 0
    t.Notes = memo
End Sub


Public Sub addSummaryTask(pj As Project, name As String, ByVal level As Integer)
    Dim t As Task
    Dim count As Long
    pj.Tasks.Add name:=name
    count = pj.Tasks.count
    Set t = pj.Tasks(count)
    t.Duration = 0
    t.Type = pjFixedDuration
    t.Estimated = False
    t.ConstraintType = pjASAP
    Call setOutlineLevel(t, level)
End Sub


