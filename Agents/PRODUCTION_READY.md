# MicroLearning Bot - Production Ready 🚀

A Telegram bot for microlearning with AI-powered agents for video delivery, quizzes, and document Q&A.

## ✅ Production-Ready Features

- **Error Handling**: Comprehensive try-catch blocks with user-friendly error messages
- **Logging**: Structured logging with rotation and retention
- **Caption Truncation**: Automatic handling of Telegram's 1024 character limit
- **Timeout Handling**: Dynamic timeout calculation based on video file size
- **Environment Validation**: Pre-flight checks before startup
- **Database Validation**: Checks for data integrity
- **Graceful Shutdown**: Proper cleanup on exit

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
DATABASE_URL=sqlite:///./microlearning.db
LOG_LEVEL=INFO
```

### 3. Initialize Database & Videos

```bash
# Reset and add all videos from folder
python scripts/reset_videos_from_folder.py

# Generate questions for all videos
python scripts/generate_all_questions.py
```

### 4. Start Bot (Production Mode)

```bash
# With pre-flight checks
python start_bot.py

# Or directly
python main.py
```

## 📁 Project Structure

```
├── start_bot.py              # Production startup with validation
├── main.py                   # Main bot application
├── agents/                   # AI agents
│   ├── video_agent.py       # Video delivery with error handling
│   ├── question_agent.py    # Quiz management
│   └── rag_agent.py         # Document Q&A
├── database/                 # Database models & operations
├── scripts/                  # Utility scripts
│   ├── reset_videos_from_folder.py     # Reset videos from folder
│   └── generate_all_questions.py       # Generate questions with retry
└── data/
    └── videos/              # Video files
```

## 🛠️ Available Scripts

### Video Management
```bash
# Reset all videos from folder
python scripts/reset_videos_from_folder.py

# Generate questions (with auto-retry on quota)
python scripts/generate_all_questions.py
```

### Database Management
```bash
# Initialize database
python scripts/init_db.py

# Check database status
python scripts/verify_setup.py
```

##   Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and get welcome message |
| `/video` | Get next learning video |
| `/quiz` | Take quiz on recent content |
| `/ask [question]` | Ask about company documents |
| `/progress` | View learning progress |
| `/docs` | List available documents |
| `/help` | Show help message |

## ⚙️ Production Configuration

### Timeout Settings
- **Small videos (<5MB)**: 60 seconds
- **Medium videos (5-15MB)**: 80-180 seconds
- **Large videos (>15MB)**: Auto-calculated (30s + 10s/MB)

### Caption Limits
- Automatic truncation at 1024 characters
- Preserves title and footer text
- Adds "..." when truncated

### Error Messages
User-friendly error messages for:
- Caption too long
- Timeout errors
- File not found
- Network issues

##   Pre-Flight Checks

The `start_bot.py` script validates:

1. ✅ Environment variables
2. ✅ Required directories
3. ✅ Database connectivity
4. ✅ Video files existence
5. ✅ Questions for all videos

##   Monitoring

### Logs
- Location: `logs/bot.log`
- Rotation: Daily
- Retention: 7 days
- Format: Timestamped with context

### Health Checks
```bash
# Check video status
python -c "from database.operations import get_db; from database.models import Video; print(f'Videos: {get_db().__enter__().query(Video).count()}')"

# Check question coverage
python scripts/generate_all_questions.py  # Will show summary
```

## 🐛 Troubleshooting

### Issue: "Caption is too long"
**Fixed**: Automatic truncation implemented

### Issue: "Timed out"
**Fixed**: Dynamic timeout based on file size

### Issue: "API quota exceeded"
**Solution**: Script now auto-retries with delays. Wait 24 hours or upgrade API tier.

### Issue: Videos not sending
**Check**:
1. Video files exist in `data/videos/`
2. File paths in database are correct
3. File sizes are reasonable (<50MB recommended)

## 🔐 Security Notes

- Never commit `.env` file
- Rotate API keys regularly
- Use environment variables for all secrets
- Enable 2FA on Telegram bot

## 📈 Scaling Considerations

For production scale:
1. Use PostgreSQL instead of SQLite
2. Add Redis for caching
3. Implement message queue for video processing
4. Use CDN for video delivery
5. Add health check endpoint
6. Implement rate limiting

## 🎯 Next Steps

1. Set up monitoring (e.g., Sentry, Prometheus)
2. Add backup scripts for database
3. Implement video compression pipeline
4. Add analytics dashboard
5. Set up CI/CD pipeline

## 📞 Support

For issues:
1. Check logs in `logs/bot.log`
2. Run `python start_bot.py` for validation
3. Verify `.env` configuration

## 📄 License

See LICENSE file for details.

---

**Status**: ✅ Production Ready  
**Last Updated**: January 30, 2026  
**Version**: 1.0.0
