@echo off
setlocal
echo Stopping VK Social Radar on port 8765...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$connections = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue; " ^
  "if (-not $connections) { Write-Host 'Server is not running.'; exit 0 }; " ^
  "$pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique; " ^
  "foreach ($processId in $pids) { Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped PID ' + $processId) }"

echo Done.
pause
