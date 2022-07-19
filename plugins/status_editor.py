from Script import script
import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from database.ia_filterdb import Media
from utils import temp
from database.quickdb import add_inst_filter, remove_inst, get_ids, get, add_sent_files, count_sent_files
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

t = time.localtime()
current_time = time.strftime("%H:%M:%S", t)

prev_day_total_users = 35531
prev_day_total_files = 577448


@Client.on_message(filters.channel)
async def set_channel_ststs(client, message):
    post = await client.get_messages(int(1001552600483), 12)
    logger.exception(current_time, exc_info=True)
    # if current_time == '03:17:10':
    # logger.exception(current_time, exc_info=True)
    todaySentFiles = count_sent_files()
    total_users = await db.total_users_count()
    files = await Media.count_documents()
    todayUsers = total_users - prev_day_total_users
    todayFiles = files - prev_day_total_files

    try:
        await post.edit(
            text=script.POST_TEXT.format(
                todaySentFiles, todayUsers, todayFiles, total_users, files),
            disable_web_page_preview=True,
            reply_markup=post.reply_markup
        )
    except:
        logger.exception('Some error occured!', exc_info=True)
