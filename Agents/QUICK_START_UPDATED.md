# 🚀 Quick Start - Updated System

## ⚡ Fast Setup (5 Minutes)

### **Step 1: Get Telegram Bot Token** (2 min)
1. Open Telegram
2. Search for `@BotFather`
3. Send: `/newbot`
4. Name your bot: `MicroLearning Bot`
5. Username: `yourname_microlearning_bot`
6. **Copy the token** (looks like: `1234567890:ABCdef...`)

### **Step 2: Configure** (1 min)
1. Open file: `d:\Projects\MicroLearning\Agents\.env`
2. Find line: `TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here`
3. Replace with: `TELEGRAM_BOT_TOKEN=your_actual_token`
4. Save file

### **Step 3: Start Bot** (1 min)
```powershell
cd d:\Projects\MicroLearning\Agents
.\start_bot.ps1
```

### **Step 4: Test in Telegram** (1 min)
1. Find your bot in Telegram
2. Send: `/start`
3. Send: `/help`
4. See available commands!

---

## 📱 Available User Commands

```
/start      - Register with the bot
/video      - Get next learning video
/quiz       - Take a quiz
/ask [q]    - Query company documents
/docs       - List available documents
/progress   - View your statistics
/help       - Show help message
```

---

## 🎬 Admin Dashboard (Optional)

### **Start Dashboard:**
```powershell
# In another terminal:
cd d:\Projects\MicroLearning\Agents
..\micro\Scripts\Activate.ps1
python admin_dashboard.py
```

### **Access:**
- URL: http://localhost:5000
- Username: `admin`
- Password: `admin123`

### **Admin Can:**
- Upload videos
- Generate AI videos (KIE.AI)
- Manage video library
- Track user progress
- View analytics

---

## 📚 Video Management

### **Option 1: Upload Video**
1. Dashboard → Videos → Add Video
2. Upload MP4 file
3. Add title & description
4. Set difficulty level
5. Save
6. **Users can now request via** `/video`

### **Option 2: Generate AI Video**
1. Dashboard → Generate Video
2. Enter description: "A professional meeting in modern office"
3. Select aspect ratio & frames
4. Click Generate
5. Wait 2-5 minutes
6. Download completed video
7. Add to library (Option 1 above)
8. **Users can now request via** `/video`

---

## ✅ What Changed?

### **Before:**
```
User: /generatevideo A sunset
Bot: Generating... (waits 5 min)
Bot: [Sends AI-generated video]
```

### **Now:**
```
User: /video
Bot: [Immediately sends video from admin library]
```

**Benefits:**
- ✅ Faster for users
- ✅ Better content quality
- ✅ Lower costs
- ✅ Admin controls curriculum

---

## 🔍 Check Status

### **View Logs:**
```powershell
Get-Content logs\bot.log -Tail 50
```

### **Check Database:**
```powershell
python check_db_direct.py
```

### **Test Connection:**
```
In Telegram: /start
Expected: Welcome message
```

---

## 🆘 Troubleshooting

### **"Invalid Token" Error:**
- Check `.env` file has correct token
- Token should be one line, no spaces
- Format: `1234567890:ABCdef...`

### **Bot Not Responding:**
- Is `python main.py` running?
- Check logs: `logs\bot.log`
- Try: Ctrl+C then restart

### **No Videos When Using `/video`:**
- Admin needs to add videos first
- Dashboard → Videos → Add Video
- Or use sample videos script:
  ```powershell
  python scripts\add_sample_videos.py
  ```

---

## 📖 Full Documentation

- **`VIDEO_SYSTEM_OVERVIEW.md`** - Complete guide
- **`CHANGELOG.md`** - What changed
- **`PROJECT_UPDATE_SUMMARY.md`** - Changes summary
- **`README.md`** - Project overview

---

## ✅ You're Ready!

```powershell
# Start bot:
.\start_bot.ps1

# Open Telegram and send:
/start
/video
/help
```

**That's it! 🎉**
