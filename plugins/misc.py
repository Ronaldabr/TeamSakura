import os
from Script import script
from info import PICS
import random
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from utils import extract_user, get_file_id, get_poster, last_online
import time
from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

@Client.on_message(filters.command('id'))
async def showid(client, message):
    chat_type = message.chat.type
    if chat_type == "private":
        user_id = message.chat.id
        first = message.from_user.first_name
        last = message.from_user.last_name or ""
        username = message.from_user.username
        dc_id = message.from_user.dc_id or ""
        await message.reply_text(
            f"<b>➲ First Name:</b> {first}\n<b>➲ Last Name:</b> {last}\n<b>➲ Username:</b> {username}\n<b>➲ Telegram ID:</b> <code>{user_id}</code>\n<b>➲ Data Centre:</b> <code>{dc_id}</code>",
            quote=True
        )

    elif chat_type in ["group", "supergroup"]:
        _id = ""
        _id += (
            "<b>➲ Chat ID</b>: "
            f"<code>{message.chat.id}</code>\n"
        )
        if message.reply_to_message:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id}</code>\n"
                "<b>➲ Replied User ID</b>: "
                f"<code>{message.reply_to_message.from_user.id}</code>\n"
            )
            file_info = get_file_id(message.reply_to_message)
        else:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id}</code>\n"
            )
            file_info = get_file_id(message)
        if file_info:
            _id += (
                f"<b>{file_info.message_type}</b>: "
                f"<code>{file_info.file_id}</code>\n"
            )
        await message.reply_text(
            _id,
            quote=True
        )

@Client.on_message(filters.command(["info"]))
async def who_is(client, message):
    # https://github.com/SpEcHiDe/PyroGramBot/blob/master/pyrobot/plugins/admemes/whois.py#L19
    status_message = await message.reply_text(
        "`Fetching user info...`"
    )
    await status_message.edit(
        "`Processing user info...`"
    )
    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        await status_message.edit(str(error))
        return
    if from_user is None:
        await status_message.edit("no valid user_id / message specified")
    else:
        message_out_str = ""
        message_out_str += f"<b>➲First Name:</b> {from_user.first_name}\n"
        last_name = from_user.last_name or "<b>None</b>"
        message_out_str += f"<b>➲Last Name:</b> {last_name}\n"
        message_out_str += f"<b>➲Telegram ID:</b> <code>{from_user.id}</code>\n"
        username = from_user.username or "<b>None</b>"
        dc_id = from_user.dc_id or "[User Doesnt Have A Valid DP]"
        message_out_str += f"<b>➲Data Centre:</b> <code>{dc_id}</code>\n"
        message_out_str += f"<b>➲User Name:</b> @{username}\n"
        message_out_str += f"<b>➲User 𝖫𝗂𝗇𝗄:</b> <a href='tg://user?id={from_user.id}'><b>Click Here</b></a>\n"
        if message.chat.type in (("supergroup", "channel")):
            try:
                chat_member_p = await message.chat.get_member(from_user.id)
                joined_date = datetime.fromtimestamp(
                    chat_member_p.joined_date or time.time()
                ).strftime("%Y.%m.%d %H:%M:%S")
                message_out_str += (
                    "<b>➲Joined this Chat on:</b> <code>"
                    f"{joined_date}"
                    "</code>\n"
                )
            except UserNotParticipant:
                pass
        chat_photo = from_user.photo
        if chat_photo:
            local_user_photo = await client.download_media(
                message=chat_photo.big_file_id
            )
            buttons = [[
                InlineKeyboardButton('🔐 Close', callback_data='close_data')
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_photo(
                photo=local_user_photo,
                quote=True,
                reply_markup=reply_markup,
                caption=message_out_str,
                parse_mode="html",
                disable_notification=True
            )
            os.remove(local_user_photo)
        else:
            buttons = [[
                InlineKeyboardButton('🔐 Close', callback_data='close_data')
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_text(
                text=message_out_str,
                reply_markup=reply_markup,
                quote=True,
                parse_mode="html",
                disable_notification=True
            )
        await status_message.delete()

@Client.on_message(filters.command(["imdb", 'search']))
async def imdb_search(client, message):
    if ' ' in message.text:
        k = await message.reply('Searching ImDB')
        r, title = message.text.split(None, 1)
        movies = await get_poster(title, bulk=True)
        if not movies:
            return await message.reply("No results Found")
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{movie.get('title')} - {movie.get('year')}",
                    callback_data=f"imdb#{movie.movieID}",
                )
            ]
            for movie in movies
        ]
        await k.edit('Here is what i found on IMDb', reply_markup=InlineKeyboardMarkup(btn))
    else:
        await message.reply('Give me a movie Name')

@Client.on_callback_query(filters.regex('^imdb'))
async def imdb_callback(bot: Client, query: CallbackQuery):
    i, movie = query.data.split('#')
    imdb = await get_poster(query=movie, id=True)
    btn = [
            [
                InlineKeyboardButton(
                    text=f"{imdb.get('title')} - {imdb.get('year')}",
                    url=imdb['url'],
                )
            ]
        ]
    if imdb.get('poster'):
        await query.message.reply_photo(photo=imdb['poster'], caption=f"IMDb Data:\n\n🏷 Title:<a href={imdb['url']}>{imdb.get('title')}</a>\n🎭 Genres: {imdb.get('genres')}\n📆 Year:<a href={imdb['url']}/releaseinfo>{imdb.get('year')}</a>\n🌟 Rating: <a href={imdb['url']}/ratings>{imdb.get('rating')}</a> / 10\n🖋 StoryLine: <code>{imdb.get('plot')} </code>", reply_markup=InlineKeyboardMarkup(btn))
        await query.message.delete()
    else:
        await query.message.edit(f"IMDb Data:\n\n🏷 Title:<a href={imdb['url']}>{imdb.get('title')}</a>\n🎭 Genres: {imdb.get('genres')}\n📆 Year:<a href={imdb['url']}/releaseinfo>{imdb.get('year')}</a>\n🌟 Rating: <a href={imdb['url']}/ratings>{imdb.get('rating')}</a> / 10\n🖋 StoryLine: <code>{imdb.get('plot')} </code>", reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    await query.answer()
        
@Client.on_message(filters.command(["stickerid"]))
async def stickerid(bot, message):   
    if message.reply_to_message.sticker:
       await message.reply(f"**ʜᴇʀᴇ ɪs ʏᴏᴜʀ sᴛɪᴄᴋᴇʀ ɪᴅ**  \n `{message.reply_to_message.sticker.file_id}` \n \n ** ᴜɴɪǫᴜᴇ ɪᴅ ɪs ** \n\n`{message.reply_to_message.sticker.file_unique_id}`", quote=True)
    else: 
       await message.reply("ɴɪᴄᴇ,ɪᴛs ɴᴏᴛ ᴀ sᴛɪᴄᴋᴇʀ")

@Client.on_message(filters.command("help"))
async def help(client, message):
        buttons = [[
            InlineKeyboardButton('𝖥𝗂𝗅𝗍𝖾𝗋', callback_data='hud'),
            InlineKeyboardButton('𝖨𝗆𝖽𝖻', callback_data='imbd'),
            InlineKeyboardButton('𝖯𝗎𝗋𝗀𝖾', callback_data='purge')
            ],[
            InlineKeyboardButton('𝖳𝗀𝗋𝖺𝗉𝗁', callback_data='tgraph'),
            InlineKeyboardButton('𝖬𝖾𝗆𝖾', callback_data='fun'),
            InlineKeyboardButton('𝖬𝗎𝗍𝖾', callback_data='mute')
            ],[
            InlineKeyboardButton('𝖡𝖺𝗇', callback_data='ban'),
            InlineKeyboardButton('𝖢𝗈𝗇𝗇𝖾𝖼𝗍𝗂𝗈𝗇', callback_data='coct'),
            InlineKeyboardButton('𝖯𝗂𝗇', callback_data='pin')
            ],[
            InlineKeyboardButton('𝖨𝗇𝖿𝗈', callback_data='info'),
            InlineKeyboardButton('𝖩𝗌𝗈𝗇', callback_data='json'),
            InlineKeyboardButton('𝖯𝗂𝗇𝗀', callback_data='ping')
            ],[
            InlineKeyboardButton('𝖢𝗈𝗏𝗂𝖽', callback_data='covid'),
            InlineKeyboardButton('𝖲𝗈𝗇𝗀', callback_data='song'),
            InlineKeyboardButton('𝖳𝖳𝖲', callback_data='tts'),
            ],[          
            InlineKeyboardButton('𝖯𝖺𝗌𝗍𝖾', callback_data='paste'),
            InlineKeyboardButton('𝖦-𝖳𝗋𝖺𝗇𝗌', callback_data='gtrans'),
            InlineKeyboardButton('𝖲𝗍𝗂𝖼𝗄𝖾𝗋 𝖨𝖣', callback_data='stick')
            ],[
            InlineKeyboardButton('𝖢𝗅𝗈𝗌𝖾', callback_data='close_data'),          
            InlineKeyboardButton('𝖲𝗍𝖺𝗍𝗌', callback_data='stats'),
            InlineKeyboardButton('𝖡𝖺𝖼𝗄', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.HELP_TXT.format(message.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )

@Client.on_message(filters.command("about"))
async def aboutme(client, message):
        buttons= [[
            InlineKeyboardButton('𝖲𝗈𝗎𝗋𝖼𝖾', url='https://t.me/Mc_linkez'),
            InlineKeyboardButton('𝖬𝗈𝗏𝗂𝖾𝗌', url='https://t.me/movies_club_2022'),
            InlineKeyboardButton('𝖡𝖺𝖼𝗄', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.ABOUT_TXT.format(message.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
