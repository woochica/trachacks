Attribute VB_Name = "ProjectModule"
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
Const svnCommonFolder = "\..\Common\"
Const svnExcelFolder = "\"
Const moduleName = "TracXMLRPC"

Public Sub ExportVBAModules()
    On Error GoTo err
    Dim FSO
    Set FSO = CreateObject("Scripting.FileSystemObject")
    Dim commonFolder As String
    Dim fileName As String
    Dim sampleFolder As String
    sampleFolder = ActiveProject.path & svnExcelFolder
    commonFolder = ActiveProject.path & svnCommonFolder
    If FSO.FolderExists(commonFolder) = False Then
        MsgBox commonFolder & " does not exist."
        Exit Sub
    End If
    
    ActiveProject.VBProject.VBComponents.item("TracXMLRPC").Export commonFolder & "TracXMLRPC.cls"
    ActiveProject.VBProject.VBComponents.item("ProjectConnecter").Export sampleFolder & "ProjectConnecter.cls"
    ActiveProject.VBProject.VBComponents.item("ProjectMiscModule").Export sampleFolder & "ProjectMiscModule.bas"
    ActiveProject.VBProject.VBComponents.item("TracSettingForm").Export sampleFolder & "TracSettingForm.frm"
    Exit Sub
err:
    Debug.Print err.description
End Sub

Public Sub ImportVBAModules()
    On Error GoTo err
    Dim FSO
    Set FSO = CreateObject("Scripting.FileSystemObject")
    Dim commonFolder As String
    Dim fileName As String
    Dim sampleFolder As String
    sampleFolder = ActiveProject.path & svnExcelFolder
    commonFolder = ActiveProject.path & svnCommonFolder
    If FSO.FolderExists(commonFolder) = False Then
        MsgBox commonFolder & " does not exist."
        Exit Sub
    End If
    Module = "TracXMLRPC"
    fileName = commonFolder & "TracXMLRPC.cls"
    If FSO.FileExists(fileName) = True Then
        ActiveProject.VBProject.VBComponents.Remove ActiveProject.VBProject.VBComponents.item(Module)
        ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "ProjectConnecter"
    fileName = sampleFolder & "ProjectConnecter.cls"
    If FSO.FileExists(fileName) = True Then
        ActiveProject.VBProject.VBComponents.Remove ActiveProject.VBProject.VBComponents.item(Module)
        ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "ProjectMiscModule"
    fileName = sampleFolder & "ProjectMiscModule.bas"
    If FSO.FileExists(fileName) = True Then
        ActiveProject.VBProject.VBComponents.Remove ActiveProject.VBProject.VBComponents.item(Module)
        ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "TracSettingForm"
    fileName = sampleFolder & "TracSettingForm.frm"
    If FSO.FileExists(fileName) = True Then
        ActiveProject.VBProject.VBComponents.Remove ActiveProject.VBProject.VBComponents.item(Module)
        ActiveProject.VBProject.VBComponents.import fileName
    End If
    
    Exit Sub
err:
    Debug.Print err.description
End Sub

Public Sub init()
    Dim form1 As TracSettingForm
    Set form1 = New TracSettingForm
    form1.Show vbModal
    Unload form1
End Sub





