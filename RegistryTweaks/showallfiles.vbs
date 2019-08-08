Set WshShell = CreateObject("WScript.Shell")
strBaseKey = "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\"
strProtected = WshShell.RegRead(strBaseKey & "ShowSuperHidden")

If strProtected = 0 Then
	WshShell.RegWrite strBaseKey & "ShowSuperHidden", 1,"REG_DWORD"
	WshShell.RegWrite strBaseKey & "Hidden", 1,"REG_DWORD"
Else
	WshShell.RegWrite strBaseKey & "ShowSuperHidden", 0,"REG_DWORD"
	WshShell.RegWrite strBaseKey & "Hidden", 2,"REG_DWORD"
End If
WshShell.SendKeys "{F5}"