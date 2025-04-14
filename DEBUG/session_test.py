from telethon.sync import TelegramClient
import logging

logging.basicConfig(level=logging.INFO)
api_id = 27948937
api_hash = "c080ddb27bcafabd88c52b78f7c6a0e1"

with TelegramClient("Get_msg.session", api_id, api_hash) as client:
    logging.info("Connected to Telegram API")
    me = client.get_me()
    logging.info(f"Authorized as {me.username}")