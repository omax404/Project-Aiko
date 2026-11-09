' Project Aiko — Zero-Terminal Windows Launcher
' Launches Aiko in the background with zero black CMD console flashing
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

batPath = strDir & "\LAUNCH_AIKO.bat"
' 0 = Hide window, False = Do not wait for script to finish
WshShell.Run """" & batPath & """", 0, False
