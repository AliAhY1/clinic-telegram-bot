# telegram_bot/send_message.py
import sys
from telegram import Bot
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

chat_id = sys.argv[1]
message = sys.argv[2]


async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    asyncio.run(main())
