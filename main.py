import logging
import threading

import discord
from discord.ext import commands

from command.payment_commands import dang_ky_lenh
from constants.config import TOKEN_BOT, WEBHOOK_HOST, WEBHOOK_PORT
from services.webhook_service import dang_ky_webhook
from utils.logging_config import thiet_lap_logging

# Cấu hình ghi log
thiet_lap_logging()

# Cấu hình bot Discord
quyen = discord.Intents.default()
quyen.message_content = True
bot = commands.Bot(command_prefix='!', intents=quyen)

# Đăng ký slash command và webhook
dang_ky_lenh(bot)
app = dang_ky_webhook(bot)


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        logging.info(f'Đăng nhập với {bot.user}')
        logging.info("Bot đã sẵn sàng hoạt động")
    except Exception as e:
        logging.error(f"Lỗi khởi tạo bot: {e}")


def chay_bot():
    try:
        bot.run(TOKEN_BOT)
    except Exception as e:
        logging.error(f"Lỗi chạy bot: {e}")


if __name__ == "__main__":
    threading.Thread(target=chay_bot, daemon=True).start()
    app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT, debug=False)
