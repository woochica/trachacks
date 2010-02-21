Option Explicit

Call Main()
WScript.Quit 0

Private Sub Main()
    Dim objPrj
	dim file
    Dim FSO
    Dim commonFolder, sampleFolder, fileName, Module
	Dim objShell
	Set objShell = WScript.CreateObject("WScript.Shell")
    Set FSO = CreateObject("Scripting.FileSystemObject")
    Set objPrj = WScript.CreateObject("MSProject.Application")
	objPrj.FileNew
'================================================================
    sampleFolder = objShell.CurrentDirectory & "\"
    commonFolder = objShell.CurrentDirectory & "\..\Common\"

    If FSO.FolderExists(commonFolder) = False Then
        MsgBox commonFolder & " does not exist."
        Exit Sub
    End If
    Module = "TracXMLRPC"
    fileName = commonFolder & "TracXMLRPC.cls"
    If FSO.FileExists(fileName) = True Then
        objPrj.ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "ProjectModule"
    fileName = sampleFolder & "ProjectModule.bas"
    If FSO.FileExists(fileName) = True Then
        objPrj.ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "ProjectConnecter"
    fileName = sampleFolder & "ProjectConnecter.cls"
    If FSO.FileExists(fileName) = True Then
        objPrj.ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "ProjectMiscModule"
    fileName = sampleFolder & "ProjectMiscModule.bas"
    If FSO.FileExists(fileName) = True Then
        objPrj.ActiveProject.VBProject.VBComponents.import fileName
    End If
    Module = "TracSettingForm"
    fileName = sampleFolder & "TracSettingForm.frm"
    If FSO.FileExists(fileName) = True Then
        objPrj.ActiveProject.VBProject.VBComponents.import fileName
    End If
'================================================================
    objPrj.Visible = True
End Sub



