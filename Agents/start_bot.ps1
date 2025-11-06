# Start Telegram Bot - MicroLearning

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "  MICROLEARNING TELEGRAM BOT" -ForegroundColor Yellow
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "[OK] Virtual environment is active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "[WARN] Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "   Activating now..." -ForegroundColor Yellow
    & "..\micro\Scripts\Activate.ps1"
    Write-Host "[OK] Virtual environment activated!" -ForegroundColor Green
}

Write-Host ""

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "[OK] Configuration file (.env) found" -ForegroundColor Green
    
    # Check if token is set
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here") {
        Write-Host ""
        Write-Host "[ERROR] TELEGRAM BOT TOKEN NOT CONFIGURED!" -ForegroundColor Red
        Write-Host ""
        Write-Host "To get your token:" -ForegroundColor Yellow
        Write-Host "   1. Open Telegram" -ForegroundColor White
        Write-Host "   2. Search for @BotFather" -ForegroundColor White
        Write-Host "   3. Send: /newbot" -ForegroundColor White
        Write-Host "   4. Follow instructions" -ForegroundColor White
        Write-Host "   5. Copy the token BotFather gives you" -ForegroundColor White
        Write-Host ""
        Write-Host "Then update .env file:" -ForegroundColor Yellow
        Write-Host "   File: .\Agents\.env" -ForegroundColor White
        Write-Host "   Change: TELEGRAM_BOT_TOKEN=your_token_here" -ForegroundColor White
        Write-Host "   To: TELEGRAM_BOT_TOKEN=1234567890:ABCdef..." -ForegroundColor White
        Write-Host ""
        
        $continue = Read-Host "Do you have a token to enter now? (y/n)"
        if ($continue -eq "y") {
            $token = Read-Host "Enter your Telegram Bot Token"
            (Get-Content ".env") -replace "TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here", "TELEGRAM_BOT_TOKEN=$token" | Set-Content ".env"
            Write-Host "[OK] Token saved!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Please configure your token and run this script again." -ForegroundColor Yellow
            Write-Host ""
            exit
        }
    } else {
        Write-Host "[OK] Telegram Bot Token is configured" -ForegroundColor Green
    }
} else {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host "   Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] .env file created!" -ForegroundColor Green
    Write-Host "   Please edit it with your Telegram Bot Token" -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "  STARTING TELEGRAM BOT SERVER..." -ForegroundColor Yellow
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Bot Features:" -ForegroundColor Green
Write-Host "   * Admin-curated learning videos" -ForegroundColor White
Write-Host "   * Interactive quizzes" -ForegroundColor White
Write-Host "   * RAG document Q&A" -ForegroundColor White
Write-Host "   * Progress tracking" -ForegroundColor White
Write-Host ""
Write-Host "User Commands:" -ForegroundColor Green
Write-Host "   /start - Register and get started" -ForegroundColor White
Write-Host "   /video - Get next learning video" -ForegroundColor White
Write-Host "   /quiz - Take a quiz" -ForegroundColor White
Write-Host "   /ask [question] - Ask about documents" -ForegroundColor White
Write-Host "   /docs - List documents" -ForegroundColor White
Write-Host "   /progress - View progress" -ForegroundColor White
Write-Host "   /help - Show all commands" -ForegroundColor White
Write-Host ""
Write-Host "Admin Features (Web Dashboard):" -ForegroundColor Cyan
Write-Host "   * Upload videos" -ForegroundColor Gray
Write-Host "   * Generate AI videos (KIE.AI)" -ForegroundColor Gray
Write-Host "   * Manage video library" -ForegroundColor Gray
Write-Host "   * Track user progress" -ForegroundColor Gray
Write-Host ""
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Yellow
Write-Host ""

# Start the bot
python main.py
