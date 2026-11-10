param(
    [ValidateSet('Install', 'Status', 'Run', 'Remove')]
    [string]$Action = 'Status'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\pythonw.exe'
$taskName = 'LLMEngineeringRadar-Daily'
$arguments = '-u -m trendradar.daily'
$existing = Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue
if ($existing) {
    $owned = @($existing.Actions)
    if ($owned.Count -ne 1 -or $owned[0].Execute -ne $python -or
        $owned[0].Arguments -ne $arguments -or $owned[0].WorkingDirectory -ne $projectRoot) {
        throw 'A different task uses this name. No changes were made.'
    }
}

if ($Action -eq 'Install') {
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Missing .venv pythonw.exe. Run uv sync first.' }
    $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $beijing = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow, 'China Standard Time')
    $boundary = $beijing.ToString('yyyy-MM-dd') + 'T20:00:00+08:00'
    $xmlPython = [System.Security.SecurityElement]::Escape($python)
    $xmlRoot = [System.Security.SecurityElement]::Escape($projectRoot)
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Local LLM engineering report, daily at 20:00 Beijing time.</Description></RegistrationInfo>
  <Triggers><CalendarTrigger><StartBoundary>$boundary</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>
  <Principals><Principal id="Author"><UserId>$sid</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable><AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <RestartOnFailure><Interval>PT30M</Interval><Count>2</Count></RestartOnFailure>
  </Settings>
  <Actions Context="Author"><Exec><Command>$xmlPython</Command><Arguments>$arguments</Arguments><WorkingDirectory>$xmlRoot</WorkingDirectory></Exec></Actions>
</Task>
"@
    Register-ScheduledTask -TaskName $taskName -TaskPath '\' -Xml $xml -Force | Out-Null
    Write-Output 'Installed: daily 20:00 Asia/Shanghai; current user must be logged in.'
    $existing = Get-ScheduledTask -TaskName $taskName -TaskPath '\'
}
if ($Action -eq 'Remove') {
    if ($existing) { Unregister-ScheduledTask -TaskName $taskName -TaskPath '\' -Confirm:$false }
    Write-Output 'Removed scheduled task. Reports and credentials were preserved.'
    exit 0
}
if (-not $existing) { Write-Output 'Not installed. Run install-daily-task.bat.'; exit 1 }
if ($Action -eq 'Run') {
    Start-ScheduledTask -InputObject $existing
    Write-Output 'Triggered. See output/daily/latest.json and its log path.'
    $existing = Get-ScheduledTask -TaskName $taskName -TaskPath '\'
}
$existing | Select-Object TaskName, State | Format-List
Get-ScheduledTaskInfo -InputObject $existing | Select-Object LastRunTime, NextRunTime, LastTaskResult | Format-List
Write-Output 'Schedule: 20:00 Beijing time (+08:00). Runs without a visible window.'
$statusPath = Join-Path $projectRoot 'output\daily\latest.json'
if (Test-Path -LiteralPath $statusPath) { Get-Content -LiteralPath $statusPath -Encoding UTF8 }
