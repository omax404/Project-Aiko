' Project Aiko — Zero-Terminal Setup Wizard
' Launches the Python GUI wizard without a command prompt
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

pyExe = strDir & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(pyExe) Then
    pyExe = strDir & "\.venv\Scripts\python.exe"
End If
If Not fso.FileExists(pyExe) Then
    pyExe = "python"
End If

scriptPath = strDir & "\installer\setup_gui.py"
WshShell.CurrentDirectory = strDir
WshShell.Run """" & pyExe & """ """ & scriptPath & """", 0, False
