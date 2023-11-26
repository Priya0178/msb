import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from info import ADMINS
import os
import re
from utils import save_file
import pyromod.listen
logger = logging.getLogger(__name__)
lock = asyncio.Lock()


@Client.on_message((filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming & filters.user(ADMINS) )
async def index_files(bot, message):
    """Save channel or group files"""
    if lock.locked():
        await message.reply('Wait until previous process complete.')
    else:
        while True:
            #await message.reply(text = "Forward me last message of a channel which I should save to my database.\n\nYou can forward posts from any public channel, but for private channels bot should be an admin in the channel.\n\nMake sure to forward with quotes (Not as a copy)")
            #last_message=await bot.listen(message.chat.id, filters=filters.text, timeout=90)
            last_message = message.text
            try:
                regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
                match = regex.match(last_message)
                if not match:
                    return await message.reply('Invalid link')
                chat_id = match.group(4)
                last_msg_id = int(match.group(5))
                if chat_id.isnumeric():
                    chat_id  = int(("-100" + chat_id))
                await bot.get_messages(chat_id, last_msg_id)
                break
            except Exception as e:
                await message.reply_text(f"This Is An Invalid Message, Either the channel is private and bot is not an admin in the forwarded chat, or you forwarded message as copy.\nError caused Due to <code>{e}</code>")
                continue

        msg = await message.reply('Processing...⏳')
        total_files = 0
        async with lock:
            try:
                total=last_msg_id + 1
                current=int(os.environ.get("SKIP", 2))
                nyav=0
                while True:
                    try:
                        message = await bot.get_messages(chat_id=chat_id, message_ids=current, replies=0)
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        message = await bot.get_messages(
                            chat_id,
                            current,
                            replies=0
                            )
                    except Exception as e:
                        print(e)
                        pass
                    try:
                        for file_type in ("document", "video", "audio"):
                            media = getattr(message, file_type, None)
                            if media is not None:
                                break
                            else:
                                continue
                        media.file_type = file_type
                        media.caption = message.caption
                        await save_file(media)
                        total_files += 1
                    except Exception as e:
                        print(e)
                        pass
                    current+=1
                    nyav+=1
                    if nyav == 20:
                        await msg.edit(f"Total messages fetched: {current}\nTotal messages saved: {total_files}")
                        nyav -= 20
                    if current == total:
                        break
                    else:
                        continue
            except Exception as e:
                logger.exception(e)
                await msg.edit(f'Error: {e}')
            else:
                await msg.edit(f'Total {total_files} Saved To DataBase!')
