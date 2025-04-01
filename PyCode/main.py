from telethon.sync import TelegramClient
import re
from datetime import datetime

api_id = 27948937
api_hash = 'c080ddb27bcafabd88c52b78f7c6a0e1'
phone_number = '+66614051808'
channels = ['@Pro_Blockchain', '@forklog', '@invcryptonews']

with TelegramClient('Get_msg', api_id, api_hash) as client:
    for channel in channels:
        print(channel + '\n')
        messages = client.get_messages(channel, limit=3)
        print(messages[0].date.strftime("%Y-%m-%d %H:%M:%S"))

        # for msg in messages:
        #     print(re.sub(r"\(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+", "", msg.text).split('\n')[0],
        #           msg.id)
