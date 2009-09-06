VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} TracSettingForm 
   Caption         =   "Import from Trac"
   ClientHeight    =   2715
   ClientLeft      =   45
   ClientTop       =   360
   ClientWidth     =   6210
   OleObjectBlob   =   "TracSettingForm.frx":0000
   StartUpPosition =   1  'オーナー フォームの中央
End
Attribute VB_Name = "TracSettingForm"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
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
Dim m_URL As String
Dim m_projectName As String
Dim m_user As String
Dim m_listIndex As Integer
Dim m_frames As Collection
Dim m_activePage As Integer
Dim m_aTrac As Collection

Const IMPORT_MODE_NONE = 0
Const IMPORT_MODE_MILESTONE = 1
Const IMPORT_MODE_VERSION = 2
Const IMPORT_MODE_COMPONENT = 3
Const IMPORT_MODE_PARENT = 4
Const IMPORT_MODE_MASTER_TICKETS = 5
Const IMPORT_MODE_ANOTHER_PRJ = 6

Const IMPORT_MODE_STR_NONE = "None"
Const IMPORT_MODE_STR_MILESTONE = "Milestone"
Const IMPORT_MODE_STR_VERSION = "Version"
Const IMPORT_MODE_STR_COMPONENT = "Component"
Const IMPORT_MODE_STR_PARENT = "Ticket(perent)"
Const IMPORT_MODE_STR_MASTER_TICKETS = "Blocked tickets(blocked)"
Const IMPORT_MODE_STR_ANOTHER_PRJ = "InterTrac parent(perent)"

Const PROP_NAME_URL = "TracURL"
Const PROP_NAME_PROJ = "ProjectName"
Const PROP_NAME_USER = "User"

Public Property Get URL() As String
    URL = m_URL & "/" & m_projectName
End Property

'最上位プロジェクトにマイルストーンがあるか確認します．
Private Function hasMilestone() As Boolean
    hasMilestone = False
    
    Dim trac As TracXMLRPC
    Set trac = Nothing
    If m_aTrac Is Nothing Then Exit Function
    
    Set trac = m_aTrac.Item(1)
    If Not trac.milestone Is Nothing Then
        On Error GoTo err1
        If trac.milestone.count <> 0 Then
            hasMilestone = True
        End If
    End If
err1: 'item取得時に失敗した場合はfalse
End Function

Private Function hasVersion() As Boolean
    hasVersion = False
    
    Dim trac As TracXMLRPC
    Set trac = Nothing
    If m_aTrac Is Nothing Then Exit Function
    
    Set trac = m_aTrac.Item(1)
    If Not trac.version Is Nothing Then
        On Error GoTo err1
        If trac.version.count <> 0 Then
            hasVersion = True
        End If
    End If
err1: 'item取得時に失敗した場合はfalse
End Function

Private Function hasComponent() As Boolean
    hasComponent = False
    
    Dim trac As TracXMLRPC
    Set trac = Nothing
    If m_aTrac Is Nothing Then Exit Function
    
    Set trac = m_aTrac.Item(1)
    If Not trac.component Is Nothing Then
        On Error GoTo err1
        If trac.component.count <> 0 Then
            hasComponent = True
        End If
        On Error GoTo 0
    End If
err1: 'item取得時に失敗した場合はfalse
End Function

Private Function createConnection(URL As String, projectName As String, user As String, pw As String) As Boolean
    On Error GoTo err
    Dim trac As TracXMLRPC
    Set trac = New TracXMLRPC
    trac.init URL, projectName, user, pw
    m_aTrac.Add trac
    createConnection = True
    Exit Function
err:
    NextButton.Enabled = False
    MsgBox err.description & "(" & err.Number & ")"
    createConnection = False
End Function

Private Sub CommandButton1_Click()
'    MsgBox "" & ComboBox1.ListIndex
    '接続確認を行い問題なければボタン２を有効にする
    Dim projectNames As Variant
    projectNames = Split(TextBox2.text, ",")
    Set m_aTrac = New Collection
    Dim prjName As Variant
    For Each prjName In projectNames
        Dim work As String
        work = Trim(prjName)
        If createConnection(TextBox1.text, work, TextBox3.text, TextBox5.text) = False Then
            Set m_aTrac = Nothing
            Exit Sub
        End If
    Next
    CommandButton1.Enabled = False
    CommandButton2.Enabled = True
    NextButton.Enabled = True
'二番目のページを割くじょしたことにより変更します　始め
'追加
    CheckBox5.Enabled = True
    CheckBox6.Enabled = True
    TextBox4.Enabled = False
    Label5.Enabled = True
    
    NextButton_Click
End Sub

Private Sub CommandButton2_Click()
    Dim pc As ProjectConnecter
    Set pc = New ProjectConnecter
    pc.init m_aTrac, m_listIndex, CheckBox5.value, CheckBox6.value, CheckBox7.value, 8
    pc.import
    CommandButton3_Click
End Sub

Private Sub CommandButton3_Click()
    addCustomDocumentProperty PROP_NAME_URL, msoPropertyTypeString, TextBox1.text
    addCustomDocumentProperty PROP_NAME_PROJ, msoPropertyTypeString, TextBox2.text
    addCustomDocumentProperty PROP_NAME_USER, msoPropertyTypeString, TextBox3.text
    Unload Me
End Sub

Private Sub Label2_Click()

End Sub

Private Sub NextButton_Click()
    changeActivePage m_activePage + 1
End Sub

Private Sub PrevButton_Click()
    CommandButton1.Enabled = True
    CommandButton2.Enabled = False
    Set m_aTrac = Nothing
    
    changeActivePage m_activePage - 1
End Sub

Private Sub TextBox1_Change()
    'textに変化があれば
    CommandButton1.Enabled = True
    CommandButton2.Enabled = False
    Set m_aTrac = Nothing
End Sub

Private Sub TextBox2_Change()
    CommandButton1.Enabled = True
    CommandButton2.Enabled = False
    Set m_aTrac = Nothing
End Sub

Private Sub TextBox3_Change()
    CommandButton1.Enabled = True
    CommandButton2.Enabled = False
    Set m_aTrac = Nothing
End Sub

Private Sub changeActivePage(page As Integer)
    m_activePage = page
    If m_activePage = 0 Then m_activePage = 1
    If m_activePage = 3 Then m_activePage = 2
    Select Case m_activePage
    Case 1
        TracFrame.Visible = True
        DetailFrame.Visible = False
        PrevButton.Enabled = False
        If m_aTrac Is Nothing Then
            NextButton.Enabled = False
        Else
            NextButton.Enabled = m_aTrac.Item(1).initialized
        End If
    Case 2
'        TracFrame.Visible = False
'        DetailFrame.Visible = False
'        PrevButton.Enabled = True
'        NextButton.Enabled = True
'    Case 3
        TracFrame.Visible = False
        DetailFrame.Visible = True
        PrevButton.Enabled = True
        NextButton.Enabled = False
    End Select
End Sub

Private Sub TracFrame_Click()

End Sub

Private Sub UserForm_Initialize()
    Dim properties As Variant
    Set properties = Application.ActiveProject.CustomDocumentProperties
    CommandButton2.Enabled = False
'    ComboBox1.AddItem IMPORT_MODE_STR_NONE
    m_listIndex = 0
'    ComboBox1.ListIndex = m_listIndex
    
    Set m_aTrac = Nothing
    
    changeActivePage 1
    
    Set properties = Application.ActiveProject.CustomDocumentProperties
    TextBox1.text = properties(PROP_NAME_URL).value
    TextBox2.text = properties(PROP_NAME_PROJ).value
    TextBox3.text = properties(PROP_NAME_USER).value
End Sub

Private Sub DisplayCustomDocumentProperties()
    Dim properties As Variant
    addCustomDocumentProperty PROP_NAME_URL, msoPropertyTypeString, "http://localhost/trac"
    addCustomDocumentProperty PROP_NAME_PROJ, msoPropertyTypeString, "SampleProject"
    addCustomDocumentProperty PROP_NAME_USER, msoPropertyTypeString, "admin"
    Set properties = Application.ActiveProject.CustomDocumentProperties
    Dim i As Integer
    For i = 1 To properties.count
        Dim prop As Variant
        Set prop = properties(i)
        Debug.Print properties(i).name
    Next i
End Sub

Private Sub addCustomDocumentProperty(name As String, propertyType As Integer, value As Variant)
    Dim properties As Variant
    Set properties = Application.ActiveProject.CustomDocumentProperties
    On Error GoTo catcherr
    properties.Add _
        name:=name, _
        LinkToContent:=False, _
        Type:=propertyType, _
        value:=value, _
        LinkSource:=False
    Exit Sub
catcherr: '存在した場合は追加できない
    On Error GoTo 0
    properties(name).Delete 'まず削除して追加する
    properties.Add _
        name:=name, _
        LinkToContent:=False, _
        Type:=propertyType, _
        value:=value, _
        LinkSource:=False
End Sub


