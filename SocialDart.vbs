Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

If fso.FileExists(strPath & "\.venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & strPath & "\.venv\Scripts\pythonw.exe"" """ & strPath & "\app.py""", 0, False
Else
    WshShell.Run "pythonw """ & strPath & "\app.py""", 0, False
End If
