# Kanged From @TroJanZheX
import asyncio
import os
import re
import ast
import time
from PIL import Image
import urllib.request
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty, MessageEmpty
from Script import script
import pyrogram
from database.admin_group import get_admingroup
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, get_name, getseries, send_more_files, gen_url
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.tvseriesfilters import add_tvseries_filter, update_tvseries_filter, getlinks, find_tvseries_filter, remove_tvseries
from database.quickdb import remove_inst, get_ids, add_sent_files, get_verification, remove_verification, add_verification
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}

DOWNLOAD_LOCATION = "./DOWNLOADS"


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    await tvseries_filters(client, message)
    await auto_filter(client, message)
    await manual_filters(client, message)


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_give_filter(client, message):
    k = await tvseries_filters(client, message)

    if k is False:
        await pm_auto_filter(client, message)


@Client.on_callback_query(filters.regex("^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("This is Not For You !!!", show_alert=True)
    try:
        offset = int(offset)
    except Exception:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)

        return
    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)

    try:
        n_offset = int(n_offset)
    except Exception:
        n_offset = 0
    if not files:
        return
    fileids = [file.file_id for file in files]
    dbid = fileids[0]
    fileids = "L_I_N_K".join(fileids)
    
    btn = [[InlineKeyboardButton(text=f"{get_size(file.file_size)} ║ {get_name(file.file_name)}", url=gen_url(
        f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{file.file_id}'))] for file in files]

    btn.insert(0, [InlineKeyboardButton("◈ All Files ◈", url=gen_url(
        f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{dbid}'))])

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append([InlineKeyboardButton("◄ Back", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(
            f"❏ Pages {round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages")])

    elif off_set is None:
        btn.append([InlineKeyboardButton(f"❏ {round(offset / 10) + 1} / {round(total / 10)}",
                   callback_data="pages"), InlineKeyboardButton("Next ►", callback_data=f"next_{req}_{key}_{n_offset}")])

    else:
        btn.append([InlineKeyboardButton("◄ Back", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(
            f"❏ {round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages"), InlineKeyboardButton("Next ►", callback_data=f"next_{req}_{key}_{n_offset}")])

    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex("^pmnext"))
async def pm_next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    try:
        offset = int(offset)
    except Exception:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)

        return
    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)

    try:
        n_offset = int(n_offset)
    except Exception:
        n_offset = 0
    if not files:
        return
    fileids = [file.file_id for file in files]
    dbid = fileids[0]
    fileids = "L_I_N_K".join(fileids)
    btn = [[InlineKeyboardButton(text=f"{get_size(file.file_size)} ║ {get_name(file.file_name)}", url=gen_url(
        f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{file.file_id}'))] for file in files]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append([InlineKeyboardButton("◄ Back", callback_data=f"pmnext_{req}_{key}_{off_set}"), InlineKeyboardButton(
            f"❏ Pages {round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages")])

    elif off_set is None:
        btn.append([InlineKeyboardButton(f"❏ {round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages"),
                   InlineKeyboardButton("Next ►", callback_data=f"pmnext_{req}_{key}_{n_offset}")])

    else:
        btn.append([InlineKeyboardButton("◄ Back", callback_data=f"pmnext_{req}_{key}_{off_set}"), InlineKeyboardButton(
            f"❏ {round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages"), InlineKeyboardButton("Next ►", callback_data=f"pmnext_{req}_{key}_{n_offset}")])

    btn.insert(0, [InlineKeyboardButton("◈ All Files ◈", url=gen_url(
        f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{dbid}'))])

    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex("^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("This is not for you", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    try:
        movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    except Exception:
        return await query.answer('Something went wrong...')
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)

    movie = movies[int(movie_)]
    await query.answer('Checking for Movie in database...')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)

        if files:
            k = movie, files, offset, total_results
            await auto_filter(bot, query, k)
        else:
            try:
                k = await query.message.edit('This Movie Not Found In DataBase. \nTry Request Again with correct spelling')

                await asyncio.sleep(10)
                await k.delete()
            except Exception:
                return


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode="md")
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)

    if query.data.startswith("gpfile"):
        ident, file_id = query.data.split("#")
        return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")

    if query.data.startswith("pmfile"):
        ident, file_id = query.data.split("#")
        idstring = await get_ids(file_id)
        if idstring:
            await remove_inst(file_id)
            idstring = idstring['links']
            fileids = idstring.split("L_I_N_K")
            sendmsglist = []
            for file_id in fileids:
                files_ = await get_file_details(file_id)
                if not files_:
                    try:
                        msg = await client.send_cached_media(
                            chat_id=query.from_user.id,
                            file_id=file_id
                        )
                        filetype = msg.media
                        file = getattr(msg, filetype)
                        title = file.file_name
                        size = get_size(file.file_size)
                        f_caption = f"<code>{title}</code>"
                        if CUSTOM_FILE_CAPTION:
                            try:
                                f_caption = CUSTOM_FILE_CAPTION.format(
                                    file_name='' if title is None else title, file_size='' if size is None else size, file_caption='')
                            except:
                                return
                        await msg.edit_caption(f_caption)
                        return
                    except:
                        pass
                files = files_[0]
                title = files.file_name
                size = get_size(files.file_size)
                f_caption = files.caption
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except Exception as e:
                        logger.exception(e)
                        f_caption = f_caption
                if f_caption is None:
                    f_caption = f"{files.file_name}"
                try:
                    k = await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption=f_caption,
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    logger.warning(f"Floodwait of {e.x} sec.")
                    k = await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption=f_caption,
                    )
                await asyncio.sleep(1)
                sendmsglist.append(k)
                await add_sent_files(query.from_user.id, file_id)

            await query.answer('𝕋𝕙𝕒𝕟𝕜 𝕐𝕠𝕦 𝔽𝕠𝕣 𝕌𝕤𝕚𝕟𝕘 𝕄𝕖')
            kk = await client.send_message(
                chat_id=query.from_user.id,
                text="""
                This Files Will delete in 10min Please Forward To Saved Messages folder before download. \n\nTurned On /notification for get new movie|tv Serieses
                """)

            await asyncio.sleep(600)
            for k in sendmsglist:
                await k.delete()
            sendmsglist = []
            return await kk.delete()

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')

        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{get_name(files.file_name)}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                return await query.answer(url=gen_url(f'https://telegram.dog/SpaciousUniverseBot?start=REAL-{file_id}'))

            k = await client.send_cached_media(
                chat_id=query.from_user.id,
                file_id=file_id,
                caption=f_caption,
                protect_content=True if ident == "filep" else False
            )
            sendmsglist = [k]
            await add_sent_files(query.from_user.id, file_id)
            files = await send_more_files(title)
            if files:
                for file in files[1:]:
                    try:
                        k = await client.send_cached_media(
                            chat_id=query.from_user.id,
                            file_id=file.file_id,
                            caption=f"<code>{file.file_name}</code>",
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        logger.warning(f"Floodwait of {e.x} sec.")
                        k = await client.send_cached_media(
                            chat_id=query.from_user.id,
                            file_id=file.file_id,
                            caption=f"<code>{file.file_name}</code>",
                        )
                    await asyncio.sleep(1)
                    sendmsglist.append(k)
                    await add_sent_files(query.from_user.id, file.file_id)

                await query.answer("𝕋𝕙𝕒𝕟𝕜 𝕐𝕠𝕦 𝔽𝕠𝕣 𝕌𝕤𝕚𝕟𝕘 𝕄𝕖 \n\n⭐Rate Me: <a href='https://t.me/tlgrmcbot?start=spaciousuniversebot-review'>Here</a>")
                kk = await client.send_message(
                    chat_id=query.from_user.id,
                    text="""
                    This Files Will delete in 10min Please Forward To Saved Messages folder before download. \n\nTurned On /notification for get new movie|tv Serieses
                    """)
                await asyncio.sleep(600)
                for k in sendmsglist:
                    await k.delete()
                sendmsglist = []
                return await kk.delete()

        except UserIsBlocked:
            await query.answer('Unblock the bot!', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=gen_url(f'https://telegram.dog/SpaciousUniverseBot?start=REAL-{file_id}'))
        except Exception as e:
            await query.answer(url=gen_url(f'https://telegram.dog/SpaciousUniverseBot?start=REAL-{file_id}'))

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('➕ Add Me To Your Groups ➕',
                                 url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton(
                '🔍 Search', switch_inline_query_current_chat=''),
            InlineKeyboardButton('🤖 Updates', url='https://t.me/TMWAD')
        ], [
            InlineKeyboardButton('ℹ️ Help', callback_data='help'),
            InlineKeyboardButton('😊 About', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(
                query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,

        )
        await query.answer('Piracy Is Crime')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton(
                'Manual Filter', callback_data='manuelfilter'),
            InlineKeyboardButton('Auto Filter', callback_data='autofilter')
        ], [
            InlineKeyboardButton('Connection', callback_data='coct'),
            InlineKeyboardButton('Extra Mods', callback_data='extra')
        ], [
            InlineKeyboardButton('🏠 Home', callback_data='start'),
            InlineKeyboardButton('🔮 Status', callback_data='stats')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,

        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('🤖 Updates', url='https://t.me/TMWAD'),
            InlineKeyboardButton('♥️ Source', callback_data='source')
        ], [
            InlineKeyboardButton('🏠 Home', callback_data='start'),
            InlineKeyboardButton('🔐 Close', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,

        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('⏹️ Buttons', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='manuelfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('👮‍♂️ Admin', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='extra')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,

        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,

        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,

        )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('Piracy Is Crime')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton(
                        'Bot PM', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["botpm"] else '❌ No',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton(
                        'IMDB', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton(
                        'Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('Piracy Is Crime')


async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"):
            return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                return await advantage_spell_chok(msg)

        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll

    fileids = [file.file_id for file in files]
    dbid = fileids[0]
    fileids = "L_I_N_K".join(fileids)

    btn = [
        [
            InlineKeyboardButton(
                text=f"{get_size(file.file_size)} ║ {get_name(file.file_name)}", url=gen_url(f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{file.file_id}')
            ),
        ]
        for file in files
    ]
    btn.insert(0,
               [InlineKeyboardButton(
                   "◈ All Files ◈", url=gen_url(f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{dbid}'))]
               )


    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"❏ 1/{round(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="Next ►", callback_data=f"next_{req}_{key}_{offset}")]
        )

    else:
        btn.append(
            [InlineKeyboardButton(text="❏ 1/1", callback_data="pages")]
        )

    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    Template = await get_admingroup(message.chat.id)
    if Template is not None:
        TEMPLATE = Template["template"]
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"Here is what i found for your query {search}"
    if imdb and imdb.get('poster'):
        try:
            await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
    else:
        await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    if spoll:
        await msg.message.delete()


async def pm_auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        if message.text.startswith("/"):
            return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                return await advantage_spell_chok(msg)

        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll

    fileids = [file.file_id for file in files]
    dbid = fileids[0]
    fileids = "L_I_N_K".join(fileids)
    btn = [
        [
            InlineKeyboardButton(
                text=f"{get_size(file.file_size)} ║ {get_name(file.file_name)}", url=gen_url(f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{file.file_id}')
            ),
        ]
        for file in files
    ]

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"❏ 1/{round(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="Next ►", callback_data=f"pmnext_{req}_{key}_{offset}")]
        )
        btn.insert(0, [InlineKeyboardButton("◈ All Files ◈", url=gen_url(
        f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{dbid}'))])

    else:
        btn.append(
            [InlineKeyboardButton(text="❏ 1/1", callback_data="pages")]
        )
        btn.insert(0, [InlineKeyboardButton("◈ All Files ◈", url=gen_url(
        f'https://telegram.dog/SpaciousUniverseBot?start=FEND-{dbid}'))])

    imdb = await get_poster(search, file=(files[0]).file_name)
    Template = await get_admingroup(message.chat.id)
    if Template is not None:
        IMDB_TEMPLATE = Template["template"]
    if imdb:
        cap = IMDB_TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"Here is what i found for your query {search}"
    if imdb and imdb.get('poster'):
        try:
            await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
    else:
        await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("I couldn't find any movie in that name.")
        await asyncio.sleep(8)
        await k.delete()
        return
    # look for imdb / wiki results
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    # removing duplicates https://stackoverflow.com/a/7961425
    gs_parsed = list(dict.fromkeys(gs_parsed))
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            # searching each keyword in imdb
            try:
                imdb_s = await get_poster(mov.strip(), bulk=True)
            except:
                continue
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip()
                  for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        name = msg.text
        name = name.replace(" ", "%20")
        btns = [
            [
                InlineKeyboardButton(
                    text="Check Spelling On Google 🧩", url=f"https://www.google.com/search?q={name}")
            ],
            [
                InlineKeyboardButton(
                    text="IMDB 💠", url=f"https://www.imdb.com/find?q={name}"),
                InlineKeyboardButton(
                    text="Wikipedia 💠", url=f"https://en.m.wikipedia.org/w/index.php?search={name}")
            ]
        ]
        try:
            k = await msg.reply(
                text="I couldn't find anything related to that.Please Check your spelling",
                reply_markup=InlineKeyboardMarkup(btns),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.exception(e)
            k = await msg.reply(
                text="I couldn't find anything related to that.Please Check your spelling",
                disable_web_page_preview=True,
            )
        await asyncio.sleep(30)
        await k.delete()
        return
    SPELL_CHECK[msg.id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(
        text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    await msg.reply("I couldn't find anything related to that\nDid you mean any one of these?",
                    reply_markup=InlineKeyboardMarkup(btn))


async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace(
                    "\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False


async def tvseries_filters(client, message, text=False):
    name = getseries(message.text)
    if len(name) < 3:
        return False

    elif name:
        seriess = await find_tvseries_filter(name)

        if len(seriess) > 4:
            return False
    else:
        return False

    if seriess:
        btns = [[InlineKeyboardButton(
            text=f"{name.capitalize()} TV Series", callback_data="pages")]]
        for series in seriess:
            language = series['language']
            quality = series['quality']
            links = series['seasonlink']
            links = links.split(",")

            btn = [[InlineKeyboardButton(text=f'Season {link + 1}', url=links[link]), InlineKeyboardButton(
                text=f'Season {link + 2}', url=links[link + 1])] for link in range(len(links) - 1) if link % 2 != 1]
            if len(links) % 2 == 1:
                btn.append([InlineKeyboardButton(
                    text=f'Season {len(links)}', url=links[-1])])

            btn.insert(0,
                       [InlineKeyboardButton(
                           text=f"{language} - {quality}", callback_data="pages")]
                       )
            btns.extend(btn)

        imdb = await get_poster(message.text) if IMDB else None
        if message.chat.type == enums.ChatType.GROUP:
            Template = await get_admingroup(message.chat.id)
            if Template is not None:
                IMDB_TEMPLATE = Template["template"]
        if imdb:
            cap = IMDB_TEMPLATE.format(
                title=imdb['title'],
                votes=imdb['votes'],
                aka=imdb["aka"],
                seasons=imdb["seasons"],
                box_office=imdb['box_office'],
                localized_title=imdb['localized_title'],
                kind=imdb['kind'],
                imdb_id=imdb["imdb_id"],
                cast=imdb["cast"],
                runtime=imdb["runtime"],
                countries=imdb["countries"],
                certificates=imdb["certificates"],
                languages=imdb["languages"],
                director=imdb["director"],
                writer=imdb["writer"],
                producer=imdb["producer"],
                composer=imdb["composer"],
                cinematographer=imdb["cinematographer"],
                music_team=imdb["music_team"],
                distributors=imdb["distributors"],
                release_date=imdb['release_date'],
                year=imdb['year'],
                genres=imdb['genres'],
                poster=imdb['poster'],
                plot=imdb['plot'],
                rating=imdb['rating'],
                url=imdb['url'],
                **locals()
            )
            if imdb.get('poster'):
                try:
                    if not os.path.isdir(DOWNLOAD_LOCATION):
                        os.makedirs(DOWNLOAD_LOCATION)
                    pic = imdb.get('poster')
                    urllib.request.urlretrieve(pic, "gfg.png")
                    im = Image.open("gfg.png")
                    width, height = im.size
                    left = 0
                    right = width
                    top = height / 5
                    bottom = height * 3 / 5
                    pic = im.crop((left, top, right, bottom))
                    img_location = DOWNLOAD_LOCATION + "tvseries" + ".png"
                    pic.save(img_location)

                except Exception as e:
                    logger.exception(e)
                    pic = imdb.get('poster')

                try:
                    await message.reply_photo(photo=img_location, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btns))
                except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                    poster = img_location.replace('.jpg', "._V1_UX360.jpg")
                    await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btns))
                except Exception as e:
                    logger.exception(e)
                    cap = "Here is what i found for your Request"
                    await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btns))

                os.remove(img_location)
        else:
            cap = "Here is what i found for your Request"
            await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btns))

    else:
        return False
