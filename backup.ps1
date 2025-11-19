# Yedekleme scripti
$BackupPath = "D:\backups\ikportal"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupPath\hr_system_$Date.db"

# Klasör yoksa oluştur
if (!(Test-Path $BackupPath)) {
    New-Item -Path $BackupPath -ItemType Directory -Force
}

# Veritabanını yedekle
Copy-Item "D:\www\ikportal.teamguerilla.com\hr_system.db" $BackupFile

# 30 günden eski yedekleri sil
Get-ChildItem $BackupPath -Filter "*.db" | 
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } | 
    Remove-Item

Write-Host "Yedek alındı: $BackupFile" -ForegroundColor Green