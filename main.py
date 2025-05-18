import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import openpyxl

# Load environment variables
load_dotenv()

# Define your bot token here
TELEGRAM_API_TOKEN = "7131704065:AAE98jOe_nanKDYoDB45zCv0sDq0lm9yCw4"

# Define states for conversation
EMAIL, PASSWORD = range(2)

# Path to the Excel file
EXCEL_FILE_PATH = 'data.xlsx'

# Database to store user information (for simplicity, using a dictionary)
user_db = {}


# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Check if the user wants to log in
    if update.message.text.lower() == 'i want to log in':
        return LOGIN
    else:
        await update.message.reply_text(
            'Hi! I am your bot. You can log in by typing "/login".')


# Login command handler
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Please enter your email:')
    return EMAIL


# Email message handler
async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    user_id = update.message.chat_id
    user_db[user_id] = {'email': email}
    await update.message.reply_text('Please enter your password:')
    return PASSWORD


# Password message handler
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    user_id = update.message.chat_id
    user_db[user_id]['password'] = password

    # Save user data to Excel file
    save_user_data(user_db)

    await update.message.reply_text('Your account has been registered.')
    return ConversationHandler.END


# Cancel command handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Registration cancelled.')
    return ConversationHandler.END


# Function to save user data to Excel file
def save_user_data(users):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(('User ID', 'Email', 'Password'))
    for user_id, info in users.items():
        sheet.append((user_id, info['email'], info['password']))
    wb.save(EXCEL_FILE_PATH)


def main() -> None:
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # Define the conversation handler with states EMAIL and PASSWORD
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWORD:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Register the handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()
