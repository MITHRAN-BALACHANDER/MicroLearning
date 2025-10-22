"""
Main Telegram Bot - MicroLearning with Multiple Agno Agents
"""
import asyncio
import warnings
import os

# Suppress warnings for cleaner logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='resume_download')
os.environ['ANONYMIZED_TELEMETRY'] = 'False'  # Disable ChromaDB telemetry

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from loguru import logger
import sys

from config.settings import TELEGRAM_BOT_TOKEN, LOG_FILE, LOG_LEVEL
from database.operations import init_db, get_or_create_user, get_user_progress
from agents.orchestrator import AgentOrchestrator, AgentType

# Configure logging
logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
logger.add(LOG_FILE, rotation="1 day", retention="7 days", level=LOG_LEVEL)


class MicroLearningBot:
    """Main bot class integrating all Agno agents"""
    
    def __init__(self):
        self.app = None
        self.orchestrator = None
        logger.info("Initializing MicroLearning Bot...")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Register user
        db_user = get_or_create_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        welcome_message = f"""
👋 **Welcome to MicroLearning Bot, {user.first_name}!**

I'm powered by multiple AI agents to help you learn effectively:

🎥 **Video Agent** - Delivers daily learning videos
📝 **Question Agent** - Tests your understanding
📚 **RAG Agent** - Answers questions from company docs

**Available Commands:**
/video - Get today's learning video
/quiz - Take a quiz on recent content
/ask [question] - Ask about company manuals/SOPs
/progress - View your learning progress
/docs - List available documents
/help - Show this help message

Let's start your learning journey! 🚀
"""
        
        await update.message.reply_text(welcome_message)
        logger.info(f"New user registered: {telegram_id}")
    
    async def video_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /video command - Send next video"""
        telegram_id = str(update.effective_user.id)
        
        await update.message.reply_text("📹 Fetching your next video...")
        
        video_agent = await self.orchestrator.get_agent(AgentType.VIDEO)
        result = await video_agent.send_daily_video(telegram_id)
        
        if not result["success"]:
            await update.message.reply_text(f"❌ {result['error']}")
    
    async def quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quiz command - Start quiz session"""
        telegram_id = str(update.effective_user.id)
        
        await update.message.reply_text("📝 Preparing your quiz...")
        
        question_agent = await self.orchestrator.get_agent(AgentType.QUESTION)
        result = await question_agent.start_quiz(telegram_id)
        
        if not result["success"]:
            await update.message.reply_text(f"❌ {result['error']}")
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command - Query company documents"""
        telegram_id = str(update.effective_user.id)
        
        # Get query from command arguments
        query = ' '.join(context.args) if context.args else None
        
        if not query:
            await update.message.reply_text(
                "❓ Please provide a question.\n\n"
                "Example: `/ask What is the vacation policy?`"
            )
            return
        
        await update.message.reply_text("🔍 Searching company documents...")
        
        try:
            rag_agent = await self.orchestrator.get_agent(AgentType.RAG)
            result = await rag_agent.query_documents(query, telegram_id)
            
            if not result["success"]:
                await update.message.reply_text(f"❌ {result.get('error', 'Unknown error occurred')}")
            elif result.get("message"):
                # If agent didn't send message, send it from here
                logger.info(f"RAG query successful, message should have been sent by agent")
        except Exception as e:
            logger.error(f"Error in ask_command: {str(e)}")
            await update.message.reply_text(
                f"❌ Sorry, I encountered an error while searching the documents.\n\n"
                f"Error: {str(e)}"
            )
    
    async def progress_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /progress command - Show user progress"""
        telegram_id = str(update.effective_user.id)
        
        video_agent = await self.orchestrator.get_agent(AgentType.VIDEO)
        result = await video_agent.get_user_video_progress(telegram_id)
        
        if result["success"]:
            progress = result["progress"]
            message = f"""
📊 **Your Learning Progress**

🎥 **Videos:**
  • Watched: {progress['watched_videos']}/{progress['total_videos']}
  • Completion: {progress['completion_rate']:.1f}%

📝 **Quizzes:**
  • Questions Answered: {progress['total_questions_answered']}
  • Average Score: {progress['average_score']}/10

Keep up the great work! 🌟
"""
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"❌ {result['error']}")
    
    async def docs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /docs command - List available documents"""
        telegram_id = str(update.effective_user.id)
        
        rag_agent = await self.orchestrator.get_agent(AgentType.RAG)
        await rag_agent.list_available_documents(telegram_id)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **MicroLearning Bot Help**

**Commands:**

🎥 `/video` - Get your next learning video

📝 `/quiz` - Start a quiz on recent content
   After watching a video, test your understanding!

🔍 `/ask [question]` - Ask about company documents
   Example: /ask What is the remote work policy?

📚 `/docs` - List all available documents
   See what manuals and SOPs are available

📊 `/progress` - View your learning statistics
   Track your videos watched and quiz scores

**How it works:**

1. **Daily Videos** - Request a video with /video
2. **Take Quizzes** - After watching, use /quiz
3. **Ask Questions** - Use /ask for company info

**Agents:**
• Video Agent - Manages content delivery
• Question Agent - Creates and evaluates quizzes
• RAG Agent - Answers questions from documents

Need more help? Contact your administrator.
"""
        await update.message.reply_text(help_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        telegram_id = str(update.effective_user.id)
        message_text = update.message.text
        
        # Check if user is in active quiz
        question_agent = await self.orchestrator.get_agent(AgentType.QUESTION)
        
        if telegram_id in question_agent.active_quizzes:
            # This is a quiz answer
            await question_agent.evaluate_answer(telegram_id, message_text)
        else:
            # Route to orchestrator for dynamic handling
            result = await self.orchestrator.process_message(telegram_id, message_text)
            
            if result["success"]:
                agent_type = result["agent"]
                await update.message.reply_text(
                    f"I'll help you with that! Use the appropriate command:\n\n"
                    f"• `/video` for videos\n"
                    f"• `/quiz` for quizzes\n"
                    f"• `/ask [question]` for documents\n"
                    f"• `/help` for all commands"
                )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or contact support."
            )
    
    async def post_init(self, application: Application):
        """Initialize after bot starts"""
        logger.info("Bot started successfully!")
        
        # Initialize orchestrator with bot
        self.orchestrator = AgentOrchestrator(application.bot)
        
        # Log agent status
        status = self.orchestrator.get_all_agents_status()
        logger.info(f"Agent Status: {status}")
    
    def run(self):
        """Run the bot"""
        try:
            # Initialize database
            logger.info("Initializing database...")
            init_db()
            
            # Create application
            self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Register handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("video", self.video_command))
            self.app.add_handler(CommandHandler("quiz", self.quiz_command))
            self.app.add_handler(CommandHandler("ask", self.ask_command))
            self.app.add_handler(CommandHandler("progress", self.progress_command))
            self.app.add_handler(CommandHandler("docs", self.docs_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            
            # Message handler
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Error handler
            self.app.add_error_handler(self.error_handler)
            
            # Post init
            self.app.post_init = self.post_init
            
            logger.info("Starting bot...")
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise


if __name__ == "__main__":
    bot = MicroLearningBot()
    bot.run()
