import os
import openpyxl
import bcrypt
from telegram import (Update, InputFile, ReplyKeyboardMarkup)
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          ContextTypes, ConversationHandler,
                          CallbackQueryHandler, filters)
from dotenv import load_dotenv

# Load env variables
load_dotenv()
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# States
EMAIL, PASSWORD = range(2)

# Excel file
EXCEL_FILE_PATH = 'data.xlsx'

# In-memory DB
user_db = {}


# Start command with keyboard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [['/login', '/logout'], ['/cancel']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        '👋 Welcome! Please choose an option below:', reply_markup=markup)
    return ConversationHandler.END


# Login command
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('📧 Please enter your email:')
    return EMAIL


# Email handler
async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    if not is_valid_email(email):
        await update.message.reply_text('❌ Invalid email format. Try again:')
        return EMAIL

    user_id = update.message.chat_id
    user_db[user_id] = {'email': email}
    await update.message.reply_text('🔒 Enter your password:')
    return PASSWORD


# Password handler
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    user_id = update.message.chat_id
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_db[user_id]['password'] = hashed_pw

    save_user_data(user_db)

    await update.message.reply_text('✅ You are registered successfully.')
    return ConversationHandler.END


# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ Registration cancelled.')
    return ConversationHandler.END


# Logout command
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id in user_db:
        del user_db[user_id]
        await update.message.reply_text('🚪 You have been logged out.')
    else:
        await update.message.reply_text('⚠️ You are not logged in.')


# Admin command to send Excel
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        await update.message.reply_text('⛔ Access denied.')
        return

    if os.path.exists(EXCEL_FILE_PATH):
        await update.message.reply_document(
            document=InputFile(EXCEL_FILE_PATH),
            filename="registered_users.xlsx",
            caption="📄 List of registered users")
    else:
        await update.message.reply_text("❗ No data file found.")


# Save user data to Excel
def save_user_data(users):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Users"
    sheet.append(('User ID', 'Email', 'Hashed Password'))
    for user_id, info in users.items():
        sheet.append((user_id, info['email'], info['password']))
    wb.save(EXCEL_FILE_PATH)


# Email validator
def is_valid_email(email):
    import re
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


# Main entry
def main():
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # Conversation handler for login
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWORD:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Register handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('logout', logout))
    application.add_handler(CommandHandler('users', users))
    application.add_handler(conv_handler)

    # Run bot
    application.run_polling()


if __name__ == '__main__':
    main()
