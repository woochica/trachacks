VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ProjectConnecter"
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
Option Explicit
Dim m_pj As Project
Dim m_aTrac As Collection
Dim m_tickets As Collection
Dim m_hours As Integer
Dim m_importMode As Integer
Const SUMMARY_MS = "Milestone"
Const SUMMARY_VER = "Version"
Const SUMMARY_CMP = "Component"

Dim m_parent As String
Dim m_planStart As String
Dim m_planEnd As String
Dim m_depencencies As String

Dim m_addDepeMs As Boolean
Dim m_addDepeVer As Boolean
Dim m_addDependancyTicket As Boolean

Public Sub init(arrayTrac As Collection, importMode As Integer, _
                dependMilestone As Boolean, dependVersion As Boolean, dependTicket As Boolean, _
                hours As Integer)
    Set m_aTrac = arrayTrac
    m_hours = hours
    m_importMode = importMode
    m_addDepeMs = dependMilestone
    m_addDepeVer = dependVersion
    m_addDependancyTicket = dependTicket
    
    Call setFieldNames("summary_ticket", "baseline_start", "baseline_end")
    
    m_depencencies = "depencencies"
    
End Sub

Public Sub setFieldNames(parent As String, planStart As String, planEnd As String)
    m_parent = parent
    m_planStart = planStart
    m_planEnd = planEnd
End Sub
' ここでは親タスクを取り込む
Sub import()
    'ループを回って今あるタスクすべてを削除します。
    Set m_pj = Application.ActiveProject
    Set m_tickets = New Collection
    
    '平準化を無効にする．
    Application.AutoLevel = False
    
    If m_pj.Tasks.count > 0 Then
        If MsgBox("Do you remove tasks?", vbYesNo) <> vbYes Then
            Exit Sub
        End If
    End If
    '現在あるすべてのタスクを削除
    Do Until m_pj.Tasks.count = 0
        m_pj.Tasks(1).Delete
    Loop
    
    If m_addDepeMs = True Then 'マイルストーンを取り込む場合
        addMilestones 1, SUMMARY_MS, m_aTrac.item(1).milestone, m_aTrac.item(1).URL & "/milestone/", ""
    End If
    If m_addDepeVer = True Then 'バージョンを取り込む場合
        addMilestones 1, SUMMARY_VER, m_aTrac.item(1).version, "", ""
    End If
    If hasChildren() Then '親のカスタムフィールドがある場合
        addTickets 1, "<string>" & m_parent & "=</string>", m_aTrac.item(1)
    Else
        addTickets 1, "<string>id!=0</string>", m_aTrac.item(1)
    End If
    
    makeDependencies
    
    MsgBox "Completed"
    Exit Sub
err:
    'すべてのエラーを取る．
    MsgBox "Runtime error:" & err.Number & " " & err.description, vbExclamation, "Error"
End Sub

Public Sub addTickets(ByVal outlineLevel As Integer, query As String, trac As TracXMLRPC)
    Dim c As Collection
'queryでparentが無い場合は問題になるので次に進む
    On Error Resume Next
    Set c = New Collection
    Set c = trac.queryTicket(query)
    On Error GoTo 0
    
    Dim w As Variant
    For Each w In c
        Dim t As Collection
        Set t = w
        addTicket t, outlineLevel, trac
        DoEvents
    Next
End Sub

Public Sub addTicket(ticket As Collection, level As Integer, trac As TracXMLRPC)
    m_pj.Tasks.Add name:=ticket.item("summary")
    Dim tasknum As Long
    tasknum = m_pj.Tasks.count    'すべてのタスク数を得る
    Dim dWork As Date
    Dim t As Task
    Set t = m_pj.Tasks(tasknum)
    t.ConstraintType = pjMSO 'pjASAP:できるだけ早く,pjFNLT:指定日までに終了
    ticket.Add t, "task" 'タスクをチケットに追加
    
'    m_tickets.Add ticket, ticket.Item("id") '
    '依存関係追加するときに検索するための情報を追加します
    ticket.Add trac.projectName, "projectName"
    m_tickets.Add ticket, trac.projectName & ":#" & ticket.item("id")
    
    Dim due_assign As String, due_close As String, completed As String, _
        PLAN_START As String, PLAN_END As String, version As String, _
        blocking As String, blockedby As String, milestone As String, _
        parent As String, complete As String, owner As String, _
        estimatedhours As String, totalhours As String, status As String
    On Error Resume Next
    due_assign = ticket.item("due_assign")
    due_close = ticket.item("due_close")
    complete = ticket.item("complete")
    PLAN_START = ticket.item(m_planStart)
    PLAN_END = ticket.item(m_planEnd)
    owner = ticket.item("owner")
    version = ticket.item("version")
    milestone = ticket.item("milestone")
    parent = ticket.item(m_parent)
    blocking = ticket.item("blocking")
    blockedby = ticket.item("blockedby")
    estimatedhours = ticket("estimatedhours")
    totalhours = ticket("totalhours")
    status = ticket("status")
    If estimatedhours <> "" Then
        estimatedhours = Val(estimatedhours)
    Else
        estimatedhours = 0
    End If
    
    On Error GoTo addticketerror
    
    '開始/終了日を設定
    If due_assign <> "" And due_close <> "" Then
        '平準化を行ったりすると日付がずれることがあるので , ベースラインにも設定する
        t.Start = due_assign
        t.BaselineStart = due_assign
        t.Finish = due_close
        t.BaselineFinish = due_close
        t.Estimated = False
    Else
        '親がある場合は親のタスクの開始日からとってくるなどが必要
        t.Start = Now
        t.Duration = estimatedhours / m_hours '見積もり時間から期間を設定する
        If totalhours = "" Then
            totalhours = "0"
        End If
        t.BaselineDuration = totalhours / m_hours
    End If
    
    '基準計画の開始/終了日を変更
    If PLAN_START <> "" And PLAN_END <> "" Then
        t.BaselineStart = PLAN_START
        dWork = PLAN_END
        dWork = dWork + 0.99
        t.BaselineFinish = dWork
    End If
    
    '期間固定とする
    t.Type = pjFixedDuration
    
    If complete <> "" Then
        t.PercentComplete = complete
    Else
        If status = "resolved" Or status = "closed" Then
            t.PercentComplete = "100"
        End If
    End If
    t.Type = pjFixedDuration
    t.Estimated = False
    
'    t.ConstraintType = pjASAP
    Call setOutlineLevel(t, level)
    
    addNotes t, ticket, m_planStart, m_planEnd, m_parent
    
    On Error GoTo 0
    
    'TODO:必要ならここで子タスクを追加する
    addTickets level + 1, "<string>" & m_parent & "=" & ticket.item("id") & "</string>", trac
    '#がある場合にも対応する
    addTickets level + 1, "<string>" & m_parent & "=#" & ticket.item("id") & "</string>", trac
    'InterTracリンク形式のものに対応
    'TODO:ループにする
    Dim tSub As Variant
    For Each tSub In m_aTrac
        Dim tWork As TracXMLRPC
        Set tWork = tSub
        addTickets level + 1, "<string>" & m_parent & "=" & trac.projectName & ":#" & ticket.item("id") & "</string>", tWork
    Next
    
    '子タスクがない場合は
    If tasknum = m_pj.Tasks.count Then '葉タスクの場合のみ
        t.ResourceNames = owner 'リソースを追加する
    End If
    
    Exit Sub
addticketerror:
    MsgBox "Ticket(" & ticket.item("id") & ") has any error - " & err.description & "(" & err.Number & ")"
End Sub

Public Sub addMilestones(ByVal outlineLevel As Integer, summary As String, c As Collection, href As String, query As String)
    If c Is Nothing Then Exit Sub
    If c.count = 0 Then Exit Sub
    
    addSummaryTask m_pj, summary, outlineLevel
    outlineLevel = outlineLevel + 1
    
    Dim m As Variant
    For Each m In c
        Dim msQuery As String
        Dim milestone As Collection
        Set milestone = m
        '抽出文字列になにかが入っているなら名前をついかする
        If query <> "" Then msQuery = "<string>" & query & milestone.item("name") & "</string>"
        addMilestone milestone, outlineLevel, href, msQuery
        DoEvents
    Next
End Sub

'マイルストーン（期間０のタスクの意味）を追加します．Tracならmilestoneかversion
Public Sub addMilestone(m As Collection, ByVal level As Integer, href As String, query As String)
    Dim name As String, due As String, completed As String, _
        description As String, owner As String
    Dim count As Long
    Dim memo As String
    On Error GoTo catcherror
    name = m.item("name")
    description = m.item("description")
    
    due = m.item("due")
    due = m.item("time")
    completed = m.item("completed")
    
    memo = memo + "description:" + description + vbCrLf
    memo = memo + "予定:" + due + vbCrLf
    owner = m.item("owner") 'コンポーネントのオーナは取得しておくが設定しない
    
    On Error GoTo addtaskerror
    
    m_pj.Tasks.Add name:=name
    count = m_pj.Tasks.count    'すべてのタスク数を得る
    Dim t As Task
    Set t = m_pj.Tasks(count)
    If href <> "" Then
        t.HyperlinkHREF = href & name
        t.Hyperlink = name
    End If
    t.Notes = description 'メモを設定
    m.Add t, "task"

    t.Start = Now
    If due <> "" And due <> "0" Then    '基準計画の開始日を設定
        t.Start = due
        t.BaselineStart = due
        t.BaselineDuration = 0
    End If
    
    t.Duration = 0 'あえて期間を0として気づきやすくする
    If completed <> "" And completed <> "0" Then    '開始日を設定
        t.PercentComplete = 100
        t.Start = completed
        memo = memo + "実:" + completed + vbCrLf
    End If
    t.Type = pjFixedDuration '期間固定とする,pjFixedDuration
    t.Estimated = False '期間を見積もりでなくする
    
'    t.ConstraintType = pjFNLT 'pjASAP:できるだけ早く,pjFNLT:指定日までに終了
'   アウトラインレベルを調整する
    Call setOutlineLevel(t, level)
    memo = memo + "実:" + completed + vbCrLf
    t.Notes = memo
    On Error GoTo 0
    
    Exit Sub
catcherror:
    Resume Next
addtaskerror:
    MsgBox "Ticket(" & name & ") has any error - " & err.description & "(" & err.Number & ")"
End Sub

'保存されたチケットのコレクションに依存関係を追加していきます
Private Sub makeDependencies()
    Dim ticket As Collection
    Dim task1 As Task, task2 As Task
    Dim projectName As String
    Dim milestone As String, version As String, blocking As String
    Dim blockingTickets As Variant
    Dim blockingTicket As Collection 'あってる？？
    Dim blockingTask As Task
    Dim i As Integer
    For Each ticket In m_tickets
        On Error GoTo dependerr
        projectName = ticket.item("projectName")
        Set task1 = ticket.item("task")
        If m_addDependancyTicket = True Then
            blocking = ""
            On Error Resume Next
            'MasterTickets
            blocking = ticket.item("blocking")
            If blocking <> "" Then
                blockingTickets = Split(blocking, ",")
                Dim id As Variant
                For Each id In blockingTickets
                    Set blockingTicket = m_tickets.item(projectName & ":#" & Trim(id))
                    Set blockingTask = blockingTicket.item("task")
                    blockingTask.TaskDependencies.Add task1, pjFinishToFinish
                Next
            End If
            'MasterTickets
            blocking = ""
            blocking = ticket.item("dependencies")
            If blocking <> "" Then
                blockingTickets = Split(blocking, ",")
                Dim depType As Long
                For Each id In blockingTickets
                    Dim pos As Integer
                    id = Trim(id) ' まず余計なスペースをとる
                    pos = InStr(id, "(")
                    If pos > 0 Then '(が存在した
                        Select Case Right(id, 3)
                        Case "SS)"
                            depType = pjStartToStart '
                        Case "FS)"
                            depType = pjFinishToStart '
                        Case "SF)"
                            depType = pjStartToFinish '
                        Case "FF)"
                            depType = pjFinishToFinish '
                        Case Else
                            Debug.Print "Unknown dependency type"
                            depType = pjFinishToStart '
                        End Select
                        id = Left(id, pos - 1)
                    Else
                        depType = pjFinishToStart '
                    End If
                    pos = InStr(id, ":#")
                    If pos <= 0 Then ':#が存在しない
                        pos = InStr(id, "#")
                        If pos <= 0 Then '#が存在しない
                            id = "#" & id
                        End If
                        id = projectName & ":" & id
                    End If
'                    Debug.Print "id = " & id & " (" & depType & ")"
                    Set blockingTicket = m_tickets.item(id)
                    Set blockingTask = blockingTicket.item("task")
                    task1.TaskDependencies.Add blockingTask, depType
                Next
            End If
        End If
        
        milestone = ""
        version = ""
        On Error Resume Next
        milestone = ticket.item("milestone")
        version = ticket.item("version")
        On Error GoTo 0
        If m_addDepeMs = True And milestone <> "" Then 'マイルストーンに依存を追加します
            checkParentAndAddDep task1, m_aTrac.item(1).milestone.item(milestone).item("task")
        End If
        If m_addDepeVer = True And version <> "" Then 'バージョンに依存を追加します
            checkParentAndAddDep task1, m_aTrac.item(1).version.item(version).item("task")
        End If
    Next
    Exit Sub
dependerr:
    'フィールドに値がない場合とか，親タスクに対してリンクを張ったとかのエラーが発生する．
    'チケット登録後にフィールドを追加した場合もえらーになるため，
    Debug.Print err.description
    Resume Next
End Sub

'タスクを親の方向に上っていき同じマイルストーンに依存していない場合のみ依存を追加します．
Sub checkParentAndAddDep(t As Task, dependency As Task)
    Dim parentTask As Task
    Set parentTask = t
'    On Error GoTo dependerr
    If parentTask.id <> 0 Then
        Do
            Set parentTask = parentTask.OutlineParent
            If parentTask.id = 0 Then
                dependency.TaskDependencies.Add t
                Exit Do
            End If
            Dim dep As Variant
            For Each dep In parentTask.TaskDependencies
                Dim TaskDep As TaskDependency
                Set TaskDep = dep
                If TaskDep.To = dependency Then
                    '親が依存するものと一致した
                    Exit Do
                End If
            Next
        Loop
    End If
End Sub

Public Function hasChildren() As Boolean
    Dim parent As Variant
    Set parent = Nothing
    On Error Resume Next
    Set parent = m_aTrac.item(1).field.item(m_parent)
    On Error GoTo 0
    hasChildren = Not parent Is Nothing
End Function

