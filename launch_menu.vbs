' Cruise Logs Launcher - VBS Wrapper
' This script launches the Python launcher without showing a console window

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this VBS file is located
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Try to find Anaconda installation
strAnacondaPath = ""
Dim anacondaPaths(3)
anacondaPaths(0) = objShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\anaconda3"
anacondaPaths(1) = objShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\Anaconda3"
anacondaPaths(2) = "C:\ProgramData\anaconda3"
anacondaPaths(3) = "C:\Anaconda3"

For i = 0 To 3
    If objFSO.FolderExists(anacondaPaths(i)) Then
        strAnacondaPath = anacondaPaths(i)
        Exit For
    End If
Next

If strAnacondaPath = "" Then
    MsgBox "Could not find Anaconda installation. Please ensure Anaconda is installed.", vbCritical, "Cruise Logs Launcher"
    WScript.Quit 1
End If

' Build the command to run
' Use pythonw.exe from Anaconda base environment
strPythonw = strAnacondaPath & "\pythonw.exe"
strLauncher = strScriptDir & "\launcher.py"

' Check if files exist
If Not objFSO.FileExists(strPythonw) Then
    MsgBox "Could not find pythonw.exe at: " & strPythonw, vbCritical, "Cruise Logs Launcher"
    WScript.Quit 1
End If

If Not objFSO.FileExists(strLauncher) Then
    MsgBox "Could not find launcher.py at: " & strLauncher, vbCritical, "Cruise Logs Launcher"
    WScript.Quit 1
End If

' Run pythonw launcher.py hidden (0 = hidden window, False = don't wait)
objShell.CurrentDirectory = strScriptDir
objShell.Run """" & strPythonw & """ """ & strLauncher & """", 0, False

' Clean up
Set objShell = Nothing
Set objFSO = Nothing
