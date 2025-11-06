# ============================================================
# Git Safety Verification Script
# ============================================================
# Run this before pushing to ensure no sensitive data is committed
# ============================================================

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "   Git Safety Verification - MicroLearning Project" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$allSafe = $true

# Check 1: Verify .env files are ignored
Write-Host "1. Checking .env files are excluded..." -ForegroundColor Yellow
$envFiles = @("Agents/.env", "backend/.env")
foreach ($file in $envFiles) {
    $winPath = $file -replace '/', '\'
    if (Test-Path $winPath) {
        $ignored = git check-ignore $file 2>$null
        if ($ignored) {
            Write-Host "   ✅ $file is properly ignored" -ForegroundColor Green
        } else {
            Write-Host "   ❌ WARNING: $file is NOT ignored!" -ForegroundColor Red
            $allSafe = $false
        }
    }
}

# Check 2: Verify database is ignored
Write-Host "`n2. Checking database files are excluded..." -ForegroundColor Yellow
$dbFiles = @("microlearning.db", "Agents\microlearning.db")
foreach ($file in $dbFiles) {
    if (Test-Path $file) {
        $ignored = git check-ignore $file 2>$null
        if ($ignored) {
            Write-Host "   ✅ $file is properly ignored" -ForegroundColor Green
        } else {
            Write-Host "   ❌ WARNING: $file is NOT ignored!" -ForegroundColor Red
            $allSafe = $false
        }
    }
}

# Check 3: Verify virtual environment is ignored
Write-Host "`n3. Checking virtual environment is excluded..." -ForegroundColor Yellow
if (Test-Path "micro") {
    $ignored = git check-ignore "micro" 2>$null
    if ($ignored) {
        Write-Host "   ✅ micro/ virtual environment is properly ignored" -ForegroundColor Green
    } else {
        Write-Host "   ❌ WARNING: micro/ is NOT ignored!" -ForegroundColor Red
        $allSafe = $false
    }
}

# Check 4: Verify node_modules are ignored
Write-Host "`n4. Checking node_modules are excluded..." -ForegroundColor Yellow
$nodeModules = @("backend\node_modules", "Frontend\node_modules")
foreach ($dir in $nodeModules) {
    if (Test-Path $dir) {
        $ignored = git check-ignore $dir 2>$null
        if ($ignored) {
            Write-Host "   ✅ $dir is properly ignored" -ForegroundColor Green
        } else {
            Write-Host "   ❌ WARNING: $dir is NOT ignored!" -ForegroundColor Red
            $allSafe = $false
        }
    }
}

# Check 5: Verify logs are ignored
Write-Host "`n5. Checking log files are excluded..." -ForegroundColor Yellow
if (Test-Path "Agents\logs") {
    $ignored = git check-ignore "Agents\logs" 2>$null
    if ($ignored) {
        Write-Host "   ✅ Agents/logs/ is properly ignored" -ForegroundColor Green
    } else {
        Write-Host "   ❌ WARNING: Agents/logs/ is NOT ignored!" -ForegroundColor Red
        $allSafe = $false
    }
}

# Check 6: Verify uploads are ignored
Write-Host "`n6. Checking upload directories are excluded..." -ForegroundColor Yellow
$uploads = @("backend\uploads", "Agents\data\videos\uploads", "Agents\data\videos\compiled")
foreach ($dir in $uploads) {
    if (Test-Path $dir) {
        $ignored = git check-ignore $dir 2>$null
        if ($ignored) {
            Write-Host "   ✅ $dir is properly ignored" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  WARNING: $dir is NOT ignored!" -ForegroundColor Red
            $allSafe = $false
        }
    }
}

# Check 7: Verify ChromaDB is ignored
Write-Host "`n7. Checking ChromaDB data is excluded..." -ForegroundColor Yellow
if (Test-Path "Agents\data\chroma_db") {
    $ignored = git check-ignore "Agents\data\chroma_db" 2>$null
    if ($ignored) {
        Write-Host "   ✅ Agents/data/chroma_db/ is properly ignored" -ForegroundColor Green
    } else {
        Write-Host "   ❌ WARNING: Agents/data/chroma_db/ is NOT ignored!" -ForegroundColor Red
        $allSafe = $false
    }
}

# Check 8: Look for accidentally staged sensitive files
Write-Host "`n8. Checking for staged sensitive files..." -ForegroundColor Yellow
$staged = git diff --cached --name-only 2>$null
$sensitivePatterns = @("\.env$", "\.db$", "\.sqlite", "\.log$", "node_modules", "\.pyc$", "__pycache__")
$foundSensitive = $false

if ($staged) {
    foreach ($file in $staged) {
        foreach ($pattern in $sensitivePatterns) {
            if ($file -match $pattern) {
                Write-Host "   ❌ WARNING: Sensitive file staged: $file" -ForegroundColor Red
                $foundSensitive = $true
                $allSafe = $false
            }
        }
    }
}

if (-not $foundSensitive) {
    Write-Host "   ✅ No sensitive files are staged" -ForegroundColor Green
}

# Check 9: Check for large files
Write-Host "`n9. Checking for large files (>10MB)..." -ForegroundColor Yellow
$largeFiles = git ls-files --others --exclude-standard | ForEach-Object { 
    if (Test-Path $_) {
        $size = (Get-Item $_).Length
        if ($size -gt 10MB) {
            [PSCustomObject]@{
                File = $_
                Size = [math]::Round($size / 1MB, 2)
            }
        }
    }
}

if ($largeFiles) {
    Write-Host "   ⚠️  Found large files:" -ForegroundColor Yellow
    $largeFiles | ForEach-Object {
        Write-Host "      - $($_.File) ($($_.Size) MB)" -ForegroundColor Yellow
    }
    Write-Host "   Consider adding these to .gitignore if they're not needed" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ No large files found" -ForegroundColor Green
}

# Final Summary
Write-Host "`n============================================================" -ForegroundColor Cyan
if ($allSafe) {
    Write-Host "   ✅ ALL CHECKS PASSED - SAFE TO PUSH!" -ForegroundColor Green
    Write-Host "============================================================`n" -ForegroundColor Cyan
    
    Write-Host "Ready to commit and push:" -ForegroundColor White
    Write-Host "  git add ." -ForegroundColor Gray
    Write-Host "  git commit -m 'feat: Add KIE.AI video generation'" -ForegroundColor Gray
    Write-Host "  git push origin main`n" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  WARNINGS FOUND - REVIEW BEFORE PUSHING" -ForegroundColor Red
    Write-Host "============================================================`n" -ForegroundColor Cyan
    Write-Host "Please fix the warnings above before pushing to Git." -ForegroundColor Yellow
}

# Show current status
Write-Host "`nCurrent Git Status:" -ForegroundColor Cyan
git status --short
