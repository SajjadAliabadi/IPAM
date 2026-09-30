$pwd = (Get-Location).Path

$action1 = New-ScheduledTaskAction -Execute "$pwd\start_ipam.bat" -WorkingDirectory "$pwd"
$trigger1 = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action1 -Trigger $trigger1 -TaskName "IPAM_WebServer" -Description "IPAM CherryPy Server" -User "NT AUTHORITY\SYSTEM" -RunLevel Highest -Force

$action2 = New-ScheduledTaskAction -Execute "$pwd\start_scanner.bat" -WorkingDirectory "$pwd"
$trigger2 = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action2 -Trigger $trigger2 -TaskName "IPAM_AutoScanner" -Description "IPAM Background Scanner" -User "NT AUTHORITY\SYSTEM" -RunLevel Highest -Force

Write-Host "Deployment tasks registered successfully! They will run automatically on Windows startup."
