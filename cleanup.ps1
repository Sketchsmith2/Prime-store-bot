Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow

Get-ChildItem -Path "*.py" | Where-Object { $_.Name -ne "bot.py" } | ForEach-Object {
    Write-Host "  Deleting $($_.Name)" -ForegroundColor Gray
    Remove-Item $_.FullName -Force
}

Get-ChildItem -Path "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Deleting $($_.Name)" -ForegroundColor Gray
    Remove-Item $_.FullName -Force
}

Write-Host ""
Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Remaining:" -ForegroundColor Cyan
Get-ChildItem | Where-Object { $_.Name -notmatch 'venv|__pycache__|\.git' } | Format-Table Name -AutoSize