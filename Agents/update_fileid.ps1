# Update Video File ID Script
# Make sure virtual environment is activated first

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Video File ID Updater" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Activating venv..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
        Write-Host "Please run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "✅ Virtual environment active" -ForegroundColor Green
Write-Host ""

# The correct file_id
$fileId = "BAACAgUAAxkBAAEYkKNo-HHjoy8w1dgnhlZ9VNsR-2FQfAACpxgAAiIGyFeB48pUoTaIxzYE"

Write-Host "Updating video file_id to:" -ForegroundColor Yellow
Write-Host $fileId -ForegroundColor White
Write-Host ""

# Update using Python
$pythonCode = @"
from database.operations import SessionLocal
from database.models import Video

db = SessionLocal()
try:
    v = db.query(Video).filter(Video.id == 1).first()
    if not v:
        print('❌ Video not found!')
    else:
        v.file_id = '$fileId'
        db.commit()
        print('✅ Updated successfully!')
        print(f'   Video: {v.title}')
        print(f'   New file_id: {v.file_id[:50]}...')
finally:
    db.close()
"@

python -c $pythonCode

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Done! Now test /video in your bot!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Update failed" -ForegroundColor Red
}
