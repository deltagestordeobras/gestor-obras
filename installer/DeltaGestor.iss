#define MyAppName "DELTA Gestor de Obras"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Delta Sistemas"
#define MyAppExeName "DeltaGestor.exe"

[Setup]
AppId={{6E6A5C2F-473B-4C2A-9E4A-202606180001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Delta Sistemas\DELTA Gestor
DefaultGroupName=Delta Sistemas
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=DELTA_Gestor_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
SetupIconFile=..\icons\favicon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Dirs]
Name: "{app}\data"
Name: "{app}\uploads"
Name: "{app}\recibos"
Name: "{app}\logs"
Name: "{app}\backups"

[Files]
Source: "..\dist\DeltaGestor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\*.db,backups_bancos_antigos\*,uploads\*,recibos\*,logs\*,.streamlit\secrets.toml"

[Icons]
Name: "{group}\DELTA Gestor de Obras"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Desinstalar DELTA Gestor"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DELTA Gestor de Obras"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir DELTA Gestor de Obras"; Flags: nowait postinstall skipifsilent

[Code]
function Timestamp(): String;
begin
  Result := GetDateTimeString('yyyy-mm-dd_hh-nn-ss', '-', '-');
end;

procedure BackupBancoCliente();
var
  Banco, PastaBackup, Destino: String;
begin
  Banco := ExpandConstant('{app}\data\gestor.db');
  if FileExists(Banco) then
  begin
    PastaBackup := ExpandConstant('{app}\backups');
    ForceDirectories(PastaBackup);
    Destino := PastaBackup + '\gestor_' + Timestamp() + '.db';
    if CopyFile(Banco, Destino, False) then
      Log('Backup do banco criado em: ' + Destino)
    else
      Log('Nao foi possivel criar backup do banco em: ' + Destino);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    BackupBancoCliente();
end;
