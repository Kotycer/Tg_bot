Lead Assistant Bot Setup Guide

1. Install Python (if not installed)

2. Open terminal inside project folder

3. Install libraries:
   pip install -r requirements.txt

4. Create Telegram bot:
   - open @BotFather
   - create new bot
   - copy token

5. Open .env file and paste:
   TELEGRAM_BOT_TOKEN=your_token
   GROQ_API_KEY=your_key
   ADMIN_ID=your_telegram_id

6. Run bot:
   python bot.py

Bot will start and capture leads automatically.
