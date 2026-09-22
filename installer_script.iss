[Setup]
AppName=SocialDart
AppVersion=1.0.0
DefaultDirName={autopf}\SocialDart
DefaultGroupName=SocialDart
UninstallDisplayIcon={app}\app.exe
SetupIconFile=assets\taskbar.ico
OutputDir=.
OutputBaseFilename=SocialDart-Setup-v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SocialDart"; Filename: "{app}\app.exe"
Name: "{autodesktop}\SocialDart"; Filename: "{app}\app.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\app.exe"; Description: "{cm:LaunchProgram,SocialDart}"; Flags: nowait postinstall skipifsilent