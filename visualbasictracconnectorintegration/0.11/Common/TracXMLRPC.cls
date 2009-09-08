VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "TracXMLRPC"
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

Dim m_milestone As Collection
Dim m_status As Collection
Dim m_version As Collection
Dim m_component As Collection
Dim m_priority As Collection
Dim m_resolution As Collection
Dim m_severity As Collection
Dim m_type As Collection
Dim m_fieldN As Collection
Dim m_fieldL As Collection
Dim m_initialized As Boolean

Dim m_timeDifference As Double

Private Sub Class_Initialize()
    m_timeDifference = 9#
    m_initialized = False
End Sub

'クラスを初期化します．各引数は次のように指定してください
'接続できない場合とかはここでエラーが発生します．
'URL:http://localhost/trac
'projectName:SampleProject
'user:admin
'pw:admin
Public Sub init(URL As String, projectName As String, user As String, pw As String)
    m_URL = URL
    m_projectName = projectName
    m_user = user
    m_pw = pw
    getStringArray m_type, "type"
    getStringArray m_status, "status"
    getStructArray m_resolution, "resolution"
    getStructArray m_milestone, "milestone"
    getStructArray m_version, "version"
    getStructArray m_component, "component"
    getStringArray m_priority, "priority"
    getStringArray m_severity, "severity"
    getTicketFields m_fieldN, m_fieldL, "field", "ticket.getTicketFields"
    m_initialized = True
End Sub

'IDを指定してチケットの情報を取得します
Public Function getTicket(id As String) As Collection
    Set getTicket = getStruct("ticket.get", id, "int")
    getTicket.Add id, "id"
End Function

Private Function getStruct_sub(method As String, params As String) As Collection
    Dim d As Collection
    Set Members = getMember(method, params, "member")
    If Members Is Nothing Or Members.Length = 0 Then '何も戻ってこなかったら
        Set getStruct_sub = Nothing
        Exit Function
    End If
    Set d = New Collection
    Dim n As String, v As String
    For i = 0 To Members.Length - 1
        Set oNodeList = Members.Item(i).ChildNodes
        If oNodeList.Length = 2 Then
            n = oNodeList(0).text '名
            v = oNodeList(1).text '値
            nn = oNodeList(1).ChildNodes(0).nodeName 'ノード名
            If nn = "dateTime.iso8601" Then
                '日付でも値が入ってない場合はここに入ってこないうえに値に０が入ってる
                v = convertDate(v) '日付を修正
            End If
            d.Add v, n 'コレクションに値を追加
'            Debug.Print "    " & n & "=" & v
        End If
        yield
    Next
    Set getStruct_sub = d
End Function

'TODO:publiv->privateに変更したが問題無いか確認
Private Function getStruct(method As String, name As String, dataType As String) As Collection
    Dim params As String
    params = "<param><value><" & dataType & ">" & name & "</" & dataType & "></value></param>"
    Set getStruct = getStruct_sub(method, params)
End Function

'milestone等の情報を取得します.指定できるのは次のものです．
'"resolution","milestone","version","component","priority","severity"
Private Sub getStructArray(ByRef d As Collection, typeName As String)
    getStructArray_Sub d, typeName, "ticket." & typeName & ".getAll"
End Sub

Private Sub getStructArray_Sub(ByRef d As Collection, typeName As String, method As String)
    Dim name As String
    Set d = New Collection
    Set Members = getMember(method, "", "string")
    If Members Is Nothing Or Members.Length = 0 Then
        Exit Sub
    End If
    For i = 0 To Members.Length - 1
        name = Members.Item(i).ChildNodes(0).text
        Dim c As Collection
'        Debug.Print "s--" & name & "(" & typeName & ")"
        Set c = getStruct("ticket." & typeName & ".get", name, "string") 'なにも得られなかった場合はnameがそのまま戻ってくる
        If c Is Nothing Then
            d.Add name, name
        Else
            d.Add c, name
        End If
'        Debug.Print "e--" & name
        yield
    Next
End Sub

'文字列コレクションを返します．typeNameに指定できるのは次のものです．
'"type","status"
Private Sub getStringArray(ByRef d As Collection, typeName As String)
    getStringArray_Sub d, typeName, "ticket." & typeName & ".getAll"
End Sub

Private Sub getStringArray_Sub(ByRef d As Collection, typeName As String, method As String)
    Dim name As String
    Set d = New Collection
    Set Members = getMember(method, "", "string")
    If Members Is Nothing Then
        Exit Sub
    End If
    If Members.Length = 0 Then
        Exit Sub
    End If
    For i = 0 To Members.Length - 1
        Set Item = Members.Item(i)
        name = Item.text
        d.Add name
'        Debug.Print "-" & name & "(" & typeName & ")"
        yield
    Next
End Sub

'ticket.getTicketFields()でTicketFieldを取得するために使用します．
Private Sub getTicketFields(ByRef d As Collection, ByRef e As Collection, typeName As String, method As String)
    Set d = New Collection
    Set e = New Collection
    Set Members = getMember(method, "", "struct")
    If Members Is Nothing Then
        Exit Sub
    End If
    If Members.Length = 0 Then
        Exit Sub
    End If
    Dim c As Collection
    
    Set c = New Collection
    
    For i = 0 To Members.Length - 1
        Dim n As String, v As String
        
        Set c = New Collection
        Set oNodeList = Members.Item(i).ChildNodes 'member
        
        For j = 0 To oNodeList.Length - 1
            Set oNodeList2 = oNodeList.Item(j).ChildNodes
            If oNodeList2.Length = 2 Then
                n = oNodeList2(0).text '名
                v = oNodeList2(1).text '値
                c.Add v, n 'コレクションに値を追加
'                Debug.Print "    " & n & "=" & v
            End If
            yield
        Next
'        Debug.Print "=== name=" & c.Item("name") & " label=" & c.Item("label")
        d.Add c, c.Item("name")
        e.Add c, c.Item("label")
        yield
    Next
End Sub

'XMLRPCでのstructをVBのCollectionから作成します．
Public Function createStruct(arrayMember As Collection) As String
    Dim structString As String
    Dim name As Variant
    If arrayMember Is Nothing Then
        Exit Function
    End If
    structString = "<struct>" + vbCrLf
    
    On Error Resume Next
    For Each name In m_fieldN
        Dim fieldName As String, value As String
        fieldName = name.Item("name")
'        If fieldName <> "id" Then
            structString = structString + _
                "<member>" + _
                    "<name>" + fieldName + "</name>" + _
                    "<value>" + arrayMember.Item(fieldName) + "</value>" + _
                "</member>" + vbCrLf
'        End If
    Next
    If structString = "<struct>" Then
        structString = ""
    Else
        structString = structString + "</struct>"
    End If
'    Debug.Print structString
    createStruct = structString
End Function

Public Function createTicket(summary As String, description As String, attributes As Collection, notify As Boolean) As Long
'int ticket.create(string summary, string description, struct attributes={}, boolean notify=False)
'Create a new ticket, returning the ticket ID.
    Dim funcName As String, params As String, dataType As String
    funcName = "ticket.create"
    dataType = "int"
    createTicket = 0
    Do
        params = _
            "<param><value><string>" & summary & "</string></value></param>" & vbCrLf & _
            "<param><value><string>" & description & "</string></value></param>" & vbCrLf & _
            "<param><value>" & vbCrLf & _
                createStruct(attributes) & vbCrLf & _
            "</value></param>" & vbCrLf & _
            "<param><value><boolean>" & CStr(Abs(CInt(notify))) & "</boolean></value></param>"
'        Debug.Print params
        Set Members = getMember(funcName, params, dataType)
        For i = 0 To Members.Length - 1
            Set oNodeList = Members.Item(i).ChildNodes
            createTicket = CLng(oNodeList(0).text)
            yield
        Next
        Exit Do
    Loop
End Function

Public Function updateTicket(id As Long, comment As String, attributes As Collection, notify As Boolean) As Collection
'array ticket.update(int id, string comment, struct attributes={}, boolean notify=False)
'Update a ticket, returning the new ticket in the same form as getTicket().
    Dim funcName As String, params As String, dataType As String
    funcName = "ticket.update"
    params = _
            "<param><value><i4>" & id & "</i4></value></param>" & vbCrLf & _
            "<param><value><string>" & comment & "</string></value></param>" & vbCrLf & _
            "<param><value>" & vbCrLf & _
                createStruct(attributes) & vbCrLf & _
            "</value></param>" & vbCrLf & _
            "<param><value><boolean>" & CStr(Abs(CInt(notify))) & "</boolean></value></param>"
'    Debug.Print params
    Set updateTicket = getStruct_sub(funcName, params)
End Function

'チケット（Collection）のCollectionを返します．
'第二引数を削除した．
'Public Function queryTicket(query As String, enableTree As Boolean) As Collection
Public Function queryTicket(query As String) As Collection
    Dim funcName As String, queryString As String, dataType As String
    funcName = "ticket.query"
    dataType = "int"
    Set queryTicket = New Collection
    Dim ticketId As String
    ticketId = "0"
    Do
        If query = "" Then
            queryString = ""
        Else
            queryString = "<param>" & query & "</param>"
        End If
        Set Members = getMember(funcName, queryString, dataType)
        For i = 0 To Members.Length - 1
            Set oNodeList = Members.Item(i).ChildNodes
            ticketId = oNodeList(0).text
            Set ti = getTicket(ticketId)
            queryTicket.Add ti, ticketId
            yield
        Next
        Exit Do
    Loop
End Function

'Tracに接続してレスポンスを得て，指定したタグの一覧を返します．
Private Function getMember(method As String, params As String, tag As String) As Variant
'    Dim xmlSv As MSXML2.xmlHttp
'    Set xmlSv = New MSXML2.xmlHttp
'参照設定が無くても使えるようにする
    Dim xmlSv As Variant
    Set xmlSv = CreateObject("MSXML2.XMLHTTP")
    Dim addr As String
    
    addr = m_URL & "/" & m_projectName & "/login/xmlrpc"
    
    xmlSv.Open "POST", addr, False, m_user, m_pw
    xmlSv.setRequestHeader "Method", "POST " & addr & " HTTP/1.1"
    xmlSv.setRequestHeader "Content-Type", "text/xml"
    
    On Error GoTo conerr
    
    If method <> "" Then
        param = "<?xml version='1.0' encoding='utf-8'?>" & vbNewLine & _
            "<methodCall>" & _
            "   <methodName>" & method & "</methodName>" & _
            "   <params>" & params & "</params>" & _
            "</methodCall>"
        Call xmlSv.send(param)
        '"fault"
    End If
    On Error GoTo 0
'    Debug.Print xmlSv.responseText
    If checkError(xmlSv) = False Then
        Set getMember = Nothing
        Exit Function
    End If
    Set getMember = xmlSv.responseXML.getElementsByTagName(tag)
    Exit Function
conerr:
    err.Raise vbObjectError + 516, , "サーバに接続できませんでした"
End Function

'Responseがエラーかどうかを判断します。
'TODO:確認
Private Function checkError(xmlSv As Variant) As Boolean
    checkError = False
    Set Members = xmlSv.responseXML.getElementsByTagName("fault")
    Dim errorMessage As String
    errorMessage = ""
    checkError = False
    If xmlSv.status <= 100 Or xmlSv.status > 200 Then
        '認証に失敗したとかHTTPにアクセスするときまでの問題の処理
        err.Raise vbObjectError + 513, , "サーバから次のエラーが返されました．" & _
            xmlSv.statusText & "(" & xmlSv.status & ")"
    ElseIf Members.Length = 0 Then
        'faultが無かった場合はちゃんとXMLでレスポンスがあったか確認します．
        If xmlSv.responseXML.getElementsByTagName("methodResponse").Length > 0 Then
            checkError = True
            Exit Function
        End If
        err.Raise vbObjectError + 514, , "XMLでの応答がありませんでした"
    Else
        'faultがあった場合エラーメッセージをまとめます
        Set Members = xmlSv.responseXML.getElementsByTagName("member")
        For i = 0 To Members.Length - 1
            Set oNodeList = Members.Item(i).ChildNodes
            If oNodeList.Item(0).text = "faultCode" Then
                errorMessage = errorMessage & "Code=" & oNodeList.Item(1).text
            End If
            If oNodeList.Item(0).text = "faultString" Then
                errorMessage = errorMessage & ":" & oNodeList.Item(1).text
            End If
            yield
        Next
    End If
    If errorMessage <> "" Then
'        MsgBox errorMessage
        err.Raise vbObjectError + 515, , errorMessage
    End If
End Function

'時間を文字列の時間に変換します
'TODO:時差は9時間を固定で入れているのでシステムの設定からとる
Private Function convertDate(text As String) As String
'20090317T16:10:12  なので+9Hしないとだめ
    Dim d As Date
    If text = "0" Then '終了日が入っていない場合はなぜか０がくる
        convertDate = ""
        Exit Function
    End If
    If Len(text) <> 17 Then
        '正規表現を使うのはめんどくさいので長さだけを見る
        convertDate = ""
        err.Raise vbObjectError + 515, , "Error: Date format is wrong (" & text & "). Check the XMLRPC responses．"
        Exit Function
    End If
    d = DateSerial(Mid$(text, 1, 4), Mid$(text, 5, 2), Mid$(text, 7, 2))
    d = DateAdd("h", Int(Mid$(text, 10, 2)), d)
    d = DateAdd("n", Int(Mid$(text, 13, 2)), d)
    d = DateAdd("s", Int(Mid$(text, 16, 2)), d)
    
    d = DateAdd("h", m_timeDifference, d)
    
    convertDate = Format(d, "yyyy/mm/dd")
End Function

Public Property Get milestone() As Collection
    Set milestone = m_milestone
End Property

Public Property Get version() As Collection
    Set version = m_version
End Property

Public Property Get ticketType() As Collection
    Set ticketType = m_type
End Property

Public Property Get status() As Collection
    Set status = m_status
End Property

Public Property Get component() As Collection
    Set component = m_component
End Property

Public Property Get priority() As Collection
    Set priority = m_priority
End Property

Public Property Get resolution() As Collection
    Set resolution = m_resolution
End Property

Public Property Get severity() As Collection
    Set severity = m_severity
End Property

Public Property Get field() As Collection
    Set field = m_fieldN
End Property

Public Property Get URL() As String
    URL = m_URL & "/" & m_projectName
End Property
Public Property Get projectName() As String
    projectName = m_projectName
End Property

Public Property Get initialized() As Boolean
    initialized = m_initialized
End Property

Private Sub yield()
    DoEvents
End Sub
