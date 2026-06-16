#define MyAppName "Google Drive Folder Mounter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Antony Gh"
#define MyAppExeName "GDriveMounter.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=GoogleDriveFolderMounterSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LicenseFile=license.txt
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startup"; Description: "Mount at Windows startup"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\GDriveMounter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs
Source: "..\tools\winfsp.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: WinFspNeedsInstall
Source: "..\tools\rclone\rclone\rclone.exe"; DestDir: "{app}\tools\rclone"; Flags: ignoreversion; Check: RcloneBundled

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\GDriveMounter"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "msiexec"; Parameters: "/i ""{tmp}\winfsp.msi"" /quiet /norestart"; StatusMsg: "Installing WinFsp..."; Check: WinFspNeedsInstall
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function WinFspNeedsInstall: Boolean;
begin
  Result := not RegKeyExists(HKLM, 'SOFTWARE\WinFsp');
end;

function RcloneBundled: Boolean;
begin
  Result := FileExists(ExpandConstant('{src}\..\tools\rclone\rclone\rclone.exe'));
end;
