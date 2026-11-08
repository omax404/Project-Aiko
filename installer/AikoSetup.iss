; ─────────────────────────────────────────────────────────────────────────────
; Project Aiko v2.0 — Inno Setup Windows Installer Script
; Compiles into a single one-click AikoSetup-2.0.0.exe installer
; ─────────────────────────────────────────────────────────────────────────────

#define MyAppName "Aiko Companion"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Project Aiko"
#define MyAppURL "https://github.com/omax404/Project-Aiko"
#define MyAppExeName "LAUNCH_AIKO.bat"

[Setup]
AppId={{8F9E4A21-6C15-4D87-9B3C-7A1E50F92B10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\AikoCompanion
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=AikoSetup-{#MyAppVersion}
SetupIconFile=..\aiko-app\src-tauri\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "installollama"; Description: "Install Ollama local AI runtime (if not already installed)"; GroupDescription: "AI Runtime:"; Flags: unchecked

[Files]
Source: "..\launch.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LAUNCH_AIKO.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\INSTALL_AIKO.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.lock"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\user_settings.example.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\core\*"; DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\aiko-app\dist\*"; DestDir: "{app}\aiko-app\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\aiko-app\src-tauri\icons\*"; DestDir: "{app}\aiko-app\src-tauri\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\aiko-app\src-tauri\target\release\aiko-app.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\aiko-app\src-tauri\icons\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\aiko-app\src-tauri\icons\icon.ico"; Tasks: desktopicon

[Run]
Filename: "winget"; Parameters: "install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements"; StatusMsg: "Installing Ollama runtime..."; Tasks: installollama; Flags: runhidden waituntilterminated skipifdoesntexist
Filename: "{app}\INSTALL_AIKO.bat"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: postinstall shellexec skipifsilent
