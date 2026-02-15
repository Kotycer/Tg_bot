# Built-in -----
from flask import Flask
import threading
import csv
from datetime import datetime
import os
# External ----- [Check requirement.txt for pip Install]
from dotenv import load_dotenv
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import gspread
from google.oauth2.service_account import Credentials
import json



load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = Groq(api_key= os.getenv("GROQ_API_KEY"))
ADMIN_ID = os.getenv("ADMIN_ID")


creds_dict = json.loads(os.getenv("GOOGLE_CREDS"))

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

client = gspread.authorize(credentials)

sheet = client.open_by_key("11IcuJfVklDJyGYyp5mJS3WlCGYbH3ooO51RUcTbnvPI").sheet1



async def start (update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stage"] = "service"

    await update.message.reply_text(
        "Hi! Thanks for reaching out. I've received your message and will respond soon.",
        reply_markup=service_keyboard
    )

async def notify_admin(context, username, message):
    alert = f"🚨 New Lead Received!\n\nUser:{username}\nMessage:{message}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=alert)


service_keyboard = ReplyKeyboardMarkup(
    [
        ["Logo Design","Website Devlopement"],
        ["Seo", "Social Media"],
        ["Other"]
    ],
    one_time_keyboard=True,
    resize_keyboard=True
)

def generate_ai_summary(service, budget, timeline, extra):
    prompt= F"""
    A freelancer received this lead:

    Service:{service}
    Budget:{budget}
    Timeline:{timeline}
    Extra:{extra}

    1. Wirte a short Summary.
    2. Give Priority: High / Medium  / Low.
    """
    response = GROQ_API_KEY.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user", "content": prompt}]
    )
    return response.choices[0].message.content

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    username = update.message.from_user.username
    stage = context.user_data.get("stage")

    # ---------------------------
    # GLOBAL RESTART
    # ---------------------------
    if user_message.lower() in ["start", "/start"]:
        context.user_data.clear()
        context.user_data["stage"] = "service"

        await update.message.reply_text(
            "Let's begin 😊\nWhat service are you looking for?",
            reply_markup=service_keyboard
        )
        return

    # ---------------------------
    # NEW USER ENTRY
    # ---------------------------
    if not stage:
        context.user_data["stage"] = "service"

        await update.message.reply_text(
            "Hi! I'll help you connect quickly.\nWhat service do you need?",
            reply_markup=service_keyboard
        )
        return

    # ---------------------------
    # SERVICE STAGE
    # ---------------------------
    if stage == "service":

        # ignore greetings
        if user_message.lower() in ["hi", "hello", "hey"]:
            await update.message.reply_text(
                "Please select a service from options.",
                reply_markup=service_keyboard
            )
            return

        context.user_data["service"] = user_message
        context.user_data["stage"] = "budget"

        await update.message.reply_text("Got it 👍 What's your approximate budget in $?")
        return

    # ---------------------------
    # BUDGET STAGE
    # ---------------------------
    if stage == "budget":
        context.user_data["budget"] = user_message
        context.user_data["stage"] = "timeline"

        await update.message.reply_text("Thanks! What's your expected timeline in Days?")
        return

    # ---------------------------
    # TIMELINE STAGE
    # ---------------------------
    if stage == "timeline":
        context.user_data["timeline"] = user_message
        context.user_data["stage"] = "extra"

        await update.message.reply_text(
            "Perfect. If you have extra details, type them now."
        )
        return

    # ---------------------------
    # EXTRA + FINAL
    # ---------------------------
    if stage == "extra":
        context.user_data["extra"] = user_message

        service = context.user_data.get("service")
        budget = context.user_data.get("budget")
        timeline = context.user_data.get("timeline")
        extra = context.user_data.get("extra")

        ai_summary = generate_ai_summary(service, budget, timeline, extra)

        save_to_csv(username, str(context.user_data))

        alert = f"""
🚨 New Lead

Service: {service}
Budget: {budget}
Timeline: {timeline}
Extra: {extra}

🧠 AI Insight:
{ai_summary}
"""

        await context.bot.send_message(chat_id=ADMIN_ID, text=alert)

        await update.message.reply_text(
            "Thanks! Your requirement is shared.\nType 'start' anytime to begin again."
        )

        context.user_data["stage"] = "completed"
        return

    # ---------------------------
    # COMPLETED STATE
    # ---------------------------
    if stage == "completed":
        await update.message.reply_text(
            "Conversation finished.\nType 'start' to begin again."
        )
        return



def save_to_csv(username, message):
    file_name = "database.csv"

    with open(file_name, mode="a",newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([ 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username,
            message
        ])

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("start", start))
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path="webhook",
        webhook_url="https://tg-bot-c2j0.onrender.com/webhook"
    )
















