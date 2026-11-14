; Jupiter TV Windows Installer
; Built with NSIS (Nullsoft Scriptable Install System)
; Download NSIS: https://nsis.sourceforge.io/

!include "MUI2.nsh"
!include "FileFunc.nsh"

; General
Name "Jupiter TV"
OutFile "JupiterTV-v0.1.0-installer.exe"
InstallDir "$PROGRAMFILES\JupiterTV"
InstallDirRegKey HKCU "Software\JupiterTV" ""

; Request admin for system-wide install
RequestExecutionLevel admin

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy application files
  File /r "apps\*.*"
  File /r "requirements-tv.txt"
  File /r "requirements-tv-locked.txt"
  File /r "docker-compose.jupiter.yml"
  
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\JupiterTV"
  CreateShortcut "$SMPROGRAMS\JupiterTV\Jupiter Desktop.lnk" "$INSTDIR\run-desktop.bat"
  CreateShortcut "$SMPROGRAMS\JupiterTV\Jupiter Mobile.lnk" "$INSTDIR\run-mobile.bat"
  CreateShortcut "$SMPROGRAMS\JupiterTV\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; Create desktop shortcuts
  CreateShortcut "$DESKTOP\Jupiter Desktop.lnk" "$INSTDIR\run-desktop.bat"
  CreateShortcut "$DESKTOP\Jupiter Mobile.lnk" "$INSTDIR\run-mobile.bat"
  
  ; Registry
  WriteRegStr HKCU "Software\JupiterTV" "" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\JupiterTV" "DisplayName" "Jupiter TV"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\JupiterTV" "UninstallString" "$INSTDIR\uninstall.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstaller
Section "Uninstall"
  Delete "$SMPROGRAMS\JupiterTV\*.*"
  RMDir "$SMPROGRAMS\JupiterTV"
  Delete "$DESKTOP\Jupiter Desktop.lnk"
  Delete "$DESKTOP\Jupiter Mobile.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\JupiterTV"
SectionEnd
