import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import START_MSG, CHANNELS, ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION
from utils import Media, get_file_details
from pyrogram.errors import UserNotParticipant
logger = logging.getLogger(__name__)
from helper_funcs.display_progress import progress_for_pyrogram
from helper_funcs.help_Nekmo_ffmpeg import take_screen_shot
import time
from pyrogram.types import InputMediaPhoto
import shutil
from helper_funcs.help_Nekmo_ffmpeg import generate_screen_shots

class Config(object):
    DOWNLOAD_LOCATION = "./DOWNLOADS"

class Translation(object):
    DOWNLOAD_START = "Getting things ready for you\nStarting Download..."
    UPLOAD_START = "Its almost over,Now Let me Upload it to Telegram "
    AFTER_SUCCESSFUL_UPLOAD_MSG = "Succesfully Uploaded by Movie Search Bot"
    REPLY_TO_DOC_FOR_SCSS = "Reply to a movie file to get screenshots"


@Client.on_message(filters.command("start"))
async def start(bot, cmd):
    usr_cmdall1 = cmd.text
    if usr_cmdall1.startswith("/start subinps"):
        if AUTH_CHANNEL:
            invite_link = await bot.create_chat_invite_link(int(AUTH_CHANNEL))
            try:
                user = await bot.get_chat_member(int(AUTH_CHANNEL), cmd.from_user.id)
                if user.status == "kicked":
                    await bot.send_message(
                        chat_id=cmd.from_user.id,
                        text="Sorry Sir, You are Banned to use me.",
                        
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                ident, file_id = cmd.text.split("_-_-_-_")
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="**Please Join My Updates Channel to use this Bot!**",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton(" 🔄 Try Again", callback_data=f"checksub#{file_id}")
                            ]
                        ]
                    ),
                    
                )
                return
            except Exception:
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="Something went Wrong.",
                    
                    disable_web_page_preview=True
                )
                return
        try:
            ident, file_id = cmd.text.split("_-_-_-_")
            filedetails = await get_file_details(file_id)
            for files in filedetails:
                title = files.file_name
                size=files.file_size
                f_caption=files.caption
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
                    except Exception as e:
                        print(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{files.file_name}"
                buttons = [
                    [
                        InlineKeyboardButton('Search again', switch_inline_query_current_chat=''),
                        InlineKeyboardButton('Go Inline', switch_inline_query='')
                    ]
                    ]
                await bot.send_cached_media(
                    chat_id=cmd.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(buttons)
                    )
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")
    elif len(cmd.command) > 1 and cmd.command[1] == 'subscribe':
        invite_link = await bot.create_chat_invite_link(int(AUTH_CHANNEL))
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
                    ]
                ]
            )
        )
    else:
        await cmd.reply_text(
            START_MSG,
            
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Search Here", switch_inline_query_current_chat=''),
                        InlineKeyboardButton("Go Inline", switch_inline_query='')
                    ],
                    [
                        InlineKeyboardButton("About", callback_data="about")
                    ]
                ]
            )
        )


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')
@Client.on_message(filters.command('about'))
async def bot_info(bot, message):
    buttons = [
        [
            InlineKeyboardButton('Update Channel', url='https://t.me/subin_works'),
            InlineKeyboardButton('Source Code', url='https://github.com/subinps/Media-Search-bot')
        ]
        ]
    await message.reply(text="<b>Developer : <a href='https://t.me/subinps_bot'>SUBIN</a>\nLanguage : <code>Python3</code>\nLibrary : <a href='https://docs.pyrogram.org/'>Pyrogram asyncio</a>\nSource Code : <a href='https://github.com/subinps/Media-Search-bot'>Click here</a>\nUpdate Channel : <a href='https://t.me/subin_works'>XTZ Bots</a> </b>", reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)


@Client.on_message(filters.command("ss"))
async def generatescreenshots(bot, update):
    if update.reply_to_message is not None:
        download_location = Config.DOWNLOAD_LOCATION + "/"
        a = await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.DOWNLOAD_START,
            reply_to_message_id=update.message_id
        )
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=update.reply_to_message,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(
                Translation.DOWNLOAD_START,
                a,
                c_time
            )
        )
        if the_real_download_location is not None:
            await bot.edit_message_text(
                text="File succesfully downloaded.\nNow taking screenshots",
                chat_id=update.chat.id,
                message_id=a.message_id
            )
            tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
            if not os.path.isdir(tmp_directory_for_each_user):
                os.makedirs(tmp_directory_for_each_user)
            images = await generate_screen_shots(
                the_real_download_location,
                tmp_directory_for_each_user,
                False,
                None,
                5,
                9
            )
            await bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.chat.id,
                message_id=a.message_id
            )
            media_album_p = []
            if images is not None:
                i = 0
                caption = "Made With Love **Movie Search Bot**"
                for image in images:
                    if os.path.exists(image):
                        if i == 0:
                            media_album_p.append(
                                InputMediaPhoto(
                                    media=image,
                                    caption=caption,
                                    parse_mode="html"
                                )
                            )
                        else:
                            media_album_p.append(
                                InputMediaPhoto(
                                    media=image
                                )
                            )
                        i = i + 1
            await bot.send_media_group(
                chat_id=update.chat.id,
                disable_notification=False,
                reply_to_message_id=a.message_id,
                media=media_album_p
            )
            #
            try:
                shutil.rmtree(tmp_directory_for_each_user)
                os.remove(the_real_download_location)
            except:
                pass
            await bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.chat.id,
                message_id=a.message_id,
                disable_web_page_preview=True
            )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.REPLY_TO_DOC_FOR_SCSS,
            reply_to_message_id=update.message_id
        ) 
