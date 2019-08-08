pause
pause

@echo off

:: Disable Updates ::
reg add "HKLM\SYSTEM\ControlSet001\Services\UsoSvc" /v "Start" /t REG_DWORD /d "4" /f
reg add "HKLM\SYSTEM\ControlSet001\Services\WaaSMedicSvc" /v "Start" /t REG_DWORD /d "4" /f
reg add "HKLM\SYSTEM\ControlSet001\Services\wuauserv" /v "Start" /t REG_DWORD /d "4" /f


:: WIFI Driver ::
pnputil /add-driver "..\Programs\Drivers\TL-WN721N\athuwbx.inf" /install   &&   echo PLease, Enter PASSWORD for WIFI to install firefox

:: Install Programs ::
..\Programs\blender.msi  /quiet	
..\Programs\7z.exe /S
..\Programs\391.35-desktop-win10-64bit-international-whql.exe  /S S    &&   C:\NVIDIA\DisplayDriver\391.35\Win10_64\International\setup.exe -s
..\Programs\far.msi /quiet
"..\Programs\Firefox Installer.exe" -ms
..\Programs\HONEYVIEW-SETUP.EXE /S
..\Programs\K-Lite_Codec_Pack_1455_Mega.exe /SILENT
..\Programs\TeamViewer_Setup.exe /S 
..\Programs\transmission-2.94-x64.msi /quiet INSTALLDIR="C:\Program Files\Transmission\"
..\Programs\VSCodeSetup-x64-1.23.1.exe /VERYSILENT
"C:\Program Files\7-Zip\7z.exe" x 3dmax.7z -o*   &&   3dsmax\max\Backburner.msi /quiet   &&   3dsmax\max\CLIC_x64_Release.msi /quiet   &&   3dsmax\max\3dsMax.msi /quiet
..\Programs\V-Ray\vray_adv_36003_max2018_x64.exe -gui=0 -configFile="..\Programs\V-Ray\config.xml" -quiet=1   &&   copy "..\Programs\V-Ray\vray2018.dlr"  "c:\Program Files\Autodesk\3ds Max 2018\plugins\"   &&   copy "..\Programs\V-Ray\vray_zzz2018.dll" "c:\Program Files\Chaos Group\V-Ray\RT for 3ds Max 2018 for x64\bin\plugins\"
..\Programs\Corona\corona-3dsmax-1.7.4.exe --acceptEulaAndAutoInstall   &&   copy "..\Programs\corona\fix\Corona_Release.dll" "c:\Program Files\Autodesk\3ds Max 2018\"   &&   copy "..\Programs\corona\fix\CoronaImage.exe" "C:\Program Files\Corona"   &&   copy "..\Programs\corona\fix\CoronaImageCmd.exe" "C:\Program Files\Corona"   &&   ..\Programs\corona\fix\Write_token-3dsmax.bat

:: Taskbar icons hide
REG ADD "HKCU\Software\Policies\Microsoft\Windows\Explorer" /V DisableNotificationCenter /T REG_DWORD /D 1 /F   &&   REG ADD "HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer" /V DisableNotificationCenter /T REG_DWORD /D 1 /F
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideClock /T REG_DWORD /D 1 /F   &&   REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideClock /T REG_DWORD /D 1 /F
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideSCANetwork /T REG_DWORD /D 1 /F   &&   REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideSCANetwork /T REG_DWORD /D 1 /F
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideSCAPower /T REG_DWORD /D 1 /F   &&   REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideSCAPower /T REG_DWORD /D 1 /F
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideSCAVolume /T REG_DWORD /D 1 /F   &&   REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V HideSCAVolume /T REG_DWORD /D 1 /F

:: Enable/Disable Notification Area from Taskbar
::powershell -windowstyle hidden -command "Start-Process cmd -ArgumentList '/s,/c,REG DELETE "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V NoTrayItemsDisplay /F & REG DELETE "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V NoTrayItemsDisplay /F & taskkill /f /im explorer.exe & start explorer.exe' -Verb runAs"
powershell -windowstyle hidden -command "Start-Process cmd -ArgumentList '/s,/c,REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V NoTrayItemsDisplay /T REG_DWORD /D 1 /F & REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /V NoTrayItemsDisplay /T REG_DWORD /D 1 /F & taskkill /f /im explorer.exe & start explorer.exe' -Verb runAs"

:: Copy Settings
xcopy /e /v Users c:\Users

:: Create Taskbar links
syspin.exe "C:\Program Files\Mozilla Firefox\firefox.exe" c:5386
syspin.exe "C:\Program Files\Transmission\transmission-qt.exe" c:5386
syspin.exe "D:\Programs\YouTubeDownloader\YouTubeDownloaderPortable.exe" c:5386
syspin.exe "C:\Program Files (x86)\TeamViewer\TeamViewer.exe c:5386
syspin.exe "D:\Programs\Calibre\calibre-portable.exe" c:5386
syspin.exe "C:\Program Files\Microsoft VS Code\Code.exe" c:5386
syspin.exe "D:\Programs\blender\blender.exe" c:5386
syspin.exe "C:\Program Files\Photoshop\Adobe Photoshop CC 2019\Photoshop.exe"  c:5386
syspin.exe "D:\Programs\Rainmeter\Rainmeter.exe" c:5386
syspin.exe "C:\Program Files\Far Manager\Far.exe" c:5386
syspin.exe "C:\Windows\System32\Taskmgr.exe" c:5386
syspin.exe "C:\Windows\explorer.exe" c:5386

::Add Links To Quick Access - DEFINE LIST OF LINKS IN add_to_qa_links.ps1
@echo off & setlocal    &&   set batchPath=%~dp0   &&   powershell.exe -noexit -file "%batchPath%add_to_qa_links.ps1" "MY-PC"

:: ENVIRONMENT VARIABLES  "set" - to see them all ; setx /M  - to modify SYSTEM scope section 
setx PATH "%PATH%;D:\Programs\Blender;C:\Program Files\Blender Foundation\blender;C:\Program Files\Far Manager;C:\Program Files\Autodesk\3ds Max 2018"

:: Thumbnails 
copy D:\Scripts\thumbnails\TxView.dll C:\Windows\System32   &&   regsvr32.exe C:\Windows\System32\TxView.dll   &&   regsvr32 "C:\Program Files\Autodesk\3ds Max 2018\MaxThumbnailShellExt.dll"   &&   blender -R

::Single-Click-to_Open_Items-Underline_when_point_at
REG ADD "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" /V IconUnderline /T REG_DWORD /D 2 /F   &&   REG ADD "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" /V ShellState /T REG_BINARY /D 240000001ea8000000000000000000000000000001000000130000000000000062000000 /F

:: Default App Associations
::dism /online /Export-DefaultAppAssociations:"D:\Scripts\MyDefaultAppAssociations.xml"
dism /online /Import-DefaultAppAssociations:"D:\Scripts\MyDefaultAppAssociations.xml"

label C:Sys
label D:Base

::Hide Drive Letters
REG ADD "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" /V ShowDriveLettersFirst /T REG_DWORD /D 2 /F

rd /s /q c:\NVIDIA
 
:: To kill and restart explorer
taskkill /f /im explorer.exe   &&   start explorer.exe

pause