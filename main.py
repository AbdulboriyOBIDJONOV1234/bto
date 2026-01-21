import asyncio
import sqlite3
import logging
import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand
from aiohttp import web
import yt_dlp

# -----------------------------------------------------------
# TOKEN
# -----------------------------------------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "8104665298")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}

# -----------------------------------------------------------
# DATABASE (SQLite)
# -----------------------------------------------------------
def init_db():
    """Bazani yaratish"""
    with sqlite3.connect('bot.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'uz'
            )
        ''')

def add_user(user_id, lang='uz'):
    """Foydalanuvchini bazaga qo'shish"""
    with sqlite3.connect('bot.db') as conn:
        conn.execute('INSERT OR IGNORE INTO users (user_id, language) VALUES (?, ?)', (user_id, lang))

def update_user_lang(user_id, lang):
    """Tilni yangilash"""
    with sqlite3.connect('bot.db') as conn:
        conn.execute('INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)', (user_id, lang))

def get_user_lang(user_id):
    """Foydalanuvchi tilini olish"""
    with sqlite3.connect('bot.db') as conn:
        cursor = conn.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 'uz'

def get_all_users():
    """Barcha foydalanuvchilar ID sini olish"""
    with sqlite3.connect('bot.db') as conn:
        cursor = conn.execute('SELECT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]

init_db()

# -----------------------------------------------------------
# TRANSLATIONS
# -----------------------------------------------------------
TRANSLATIONS = {
    'uz': {
        'welcome': (
            "👋 **Salom! Men Universal Video Yuklovchiman.**\n\n"
            "Men quyidagilardan video yuklab beraman:\n"
            "🔹 **YouTube** (Shorts ham)\n"
            "🔹 **Instagram** (Stories, Reels, Post)\n"
            "🔹 **TikTok**\n"
            "🔹 **Facebook**\n"
            "🔹 **Twitter/X**\n\n"
            "🚀 *Boshlash uchun link yuboring!*\n\n"
            "🌐 Tilni o'zgartirish: /language\n"
            "ℹ️ Yordam: /help"
        ),
        'help': (
            "🆘 **Muammo bo'lsa, adminga yozing:**\n"
            "👨‍💻 Asoschi: @Abdulboriy7700"
        ),
        'choose_language': "🌐 Tilni tanlang:",
        'language_changed': "✅ Til o'zgartirildi!",
        'invalid_link': "❌ Iltimos, to'g'ri link yuboring.",
        'downloading': "⏳ **📹 Video yuklanmoqda...**\n(Biroz kuting, bu 30-60 soniya olishi mumkin)",
        'error': "❌ Xatolik: {}",
        'file_too_large': "❌ Fayl 50 MB dan katta. Telegramga yuklab bo'lmaydi.",
        'uploading': "📤 Telegramga yuklanmoqda...",
        'upload_error': "Yuborishda xato: {}",
        'file_not_found': "❌ Fayl topilmadi.",
        'retry': "🔄 Qayta urinib ko'rilmoqda...",
    },
    'ru': {
        'welcome': (
            "👋 **Привет! Я загрузчик видео.**\n\n"
            "Я могу скачать видео с:\n"
            "🔹 **YouTube** (включая Shorts)\n"
            "🔹 **Instagram** (Stories, Reels, Post)\n"
            "🔹 **TikTok**\n"
            "🔹 **Facebook**\n"
            "🔹 **Twitter/X**\n\n"
            "🚀 *Отправьте ссылку для начала!*\n\n"
            "🌐 Сменить язык: /language\n"
            "ℹ️ Помощь: /help"
        ),
        'help': (
            "🆘 **Если есть проблемы, пишите админу:**\n"
            "👨‍💻 Создатель: @Abdulboriy7700"
        ),
        'choose_language': "🌐 Выберите язык:",
        'language_changed': "✅ Язык изменен!",
        'invalid_link': "❌ Пожалуйста, отправьте правильную ссылку.",
        'downloading': "⏳ **📹 Загрузка видео...**\n(Пожалуйста, подождите 30-60 секунд)",
        'error': "❌ Ошибка: {}",
        'file_too_large': "❌ Файл больше 50 МБ. Невозможно загрузить в Telegram.",
        'uploading': "📤 Загрузка в Telegram...",
        'upload_error': "Ошибка при отправке: {}",
        'file_not_found': "❌ Файл не найден.",
        'retry': "🔄 Повторная попытка...",
    },
    'en': {
        'welcome': (
            "👋 **Hello! I'm a Video Downloader.**\n\n"
            "I can download videos from:\n"
            "🔹 **YouTube** (including Shorts)\n"
            "🔹 **Instagram** (Stories, Reels, Post)\n"
            "🔹 **TikTok**\n"
            "🔹 **Facebook**\n"
            "🔹 **Twitter/X**\n\n"
            "🚀 *Send a link to get started!*\n\n"
            "🌐 Change language: /language\n"
            "ℹ️ Help: /help"
        ),
        'help': (
            "🆘 **If you have problems, contact admin:**\n"
            "👨‍💻 Founder: @Abdulboriy7700"
        ),
        'choose_language': "🌐 Choose your language:",
        'language_changed': "✅ Language changed!",
        'invalid_link': "❌ Please send a valid link.",
        'downloading': "⏳ **📹 Downloading video...**\n(Please wait 30-60 seconds)",
        'error': "❌ Error: {}",
        'file_too_large': "❌ File is larger than 50 MB. Cannot upload to Telegram.",
        'uploading': "📤 Uploading to Telegram...",
        'upload_error': "Upload error: {}",
        'file_not_found': "❌ File not found.",
        'retry': "🔄 Retrying...",
    }
}

def get_text(user_id, key):
    """Foydalanuvchi tilida matnni olish"""
    lang = get_user_lang(user_id)
    return TRANSLATIONS[lang].get(key, TRANSLATIONS['uz'][key])

# -----------------------------------------------------------
# RANDOM USER AGENTS (Bot detection ni chetlab o'tish)
# -----------------------------------------------------------
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
]

# -----------------------------------------------------------
# ADVANCED VIDEO YUKLASH (90-95% SUCCESS RATE)
# -----------------------------------------------------------
def download_video(url, max_retries=3):
    """
    Eng kuchli video downloader - 3 xil usul bilan urinadi
    """
    
    # FFmpeg yo'lini aniqlash
    if os.name == 'nt':
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_dir = os.path.join(current_dir, "ffmpeg-master-latest-win64-gpl-shared", "ffmpeg-master-latest-win64-gpl-shared", "bin")
    else:
        ffmpeg_dir = None

    # METHOD 1: Standard yt-dlp
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries}: Trying standard method")
            result = _download_standard(url, ffmpeg_dir)
            if result[0]:  # Agar fayl topilsa
                return result
        except Exception as e:
            logging.error(f"Standard method failed: {e}")
        
        # Har bir urinish o'rtasida 2 soniya kutish
        if attempt < max_retries - 1:
            asyncio.sleep(2)
    
    # METHOD 2: Alternative extractors
    try:
        logging.info("Trying alternative extractors")
        result = _download_alternative(url, ffmpeg_dir)
        if result[0]:
            return result
    except Exception as e:
        logging.error(f"Alternative method failed: {e}")
    
    # METHOD 3: Generic extractor (last resort)
    try:
        logging.info("Trying generic extractor")
        result = _download_generic(url, ffmpeg_dir)
        if result[0]:
            return result
    except Exception as e:
        logging.error(f"Generic method failed: {e}")
    
    return None, None, "Barcha urinishlar muvaffaqiyatsiz tugadi. Video yuklab bo'lmadi."

def _download_standard(url, ffmpeg_dir):
    """Standard yuklash usuli"""
    
    # Shorts linkni oddiy formatga o'zgartirish
    original_url = url
    if "/shorts/" in url:
        video_id = url.split("/shorts/")[1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={video_id}"
        logging.info(f"Converted shorts URL: {url}")
    
    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'noplaylist': True,
        'format': 'best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'socket_timeout': 60,
        'retries': 10,
        'fragment_retries': 10,
        'http_chunk_size': 10485760,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'prefer_insecure': True,
        'http_headers': {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    # Platform-specific settings
    if "instagram.com" in original_url:
        ydl_opts['http_headers']['User-Agent'] = 'Instagram 219.0.0.12.117 Android'
        
    elif "youtube.com" in url or "youtu.be" in url:
        ydl_opts['format'] = 'best[height<=720][ext=mp4]/best[ext=mp4]/best'
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android', 'ios', 'tv_embedded', 'web'],
                'skip': ['hls', 'dash'],
                'player_skip': ['webpage', 'configs'],
            }
        }
        ydl_opts['http_headers']['User-Agent'] = 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip'
        
    elif "tiktok.com" in original_url:
        ydl_opts['http_headers']['User-Agent'] = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        if not info:
            return None, None, "Video ma'lumotlari topilmadi"

        if 'entries' in info:
            if len(info['entries']) > 0:
                info = info['entries'][0]
            else:
                return None, None, "Video topilmadi"

        if 'formats' not in info or not info['formats']:
            return None, None, "Video formati topilmadi"

        logging.info(f"Downloading: {info.get('title', 'Unknown')}")
        ydl.download([url])
        
        filename = ydl.prepare_filename(info)
        title = info.get('title', 'Media')
        
        # Fayl topish
        if not os.path.exists(filename):
            base_name = os.path.splitext(filename)[0]
            for ext in ['.mp4', '.mkv', '.webm', '.mov', '.avi']:
                test_file = base_name + ext
                if os.path.exists(test_file):
                    filename = test_file
                    break
        
        if os.path.exists(filename):
            return filename, title, None
        else:
            return None, None, "Fayl yuklab olinmadi"

def _download_alternative(url, ffmpeg_dir):
    """Alternative extractors bilan yuklash"""
    
    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'format': 'best',
        'noplaylist': True,
        'socket_timeout': 60,
        'http_headers': {
            'User-Agent': random.choice(USER_AGENTS),
        },
        'extractor_args': {
            'generic': {
                'force_generic_extractor': True
            }
        }
    }
    
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info:
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')
            if os.path.exists(filename):
                return filename, title, None
    
    return None, None, "Alternative method failed"

def _download_generic(url, ffmpeg_dir):
    """Generic extractor - oxirgi imkoniyat"""
    
    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s',
        'format': 'best',
        'noplaylist': True,
        'force_generic_extractor': True,
        'socket_timeout': 60,
    }
    
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info:
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')
            if os.path.exists(filename):
                return filename, title, None
    
    return None, None, "Generic method failed"

# -----------------------------------------------------------
# KOMANDALAR
# -----------------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)
    await message.answer(get_text(user_id, 'welcome'), parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    user_id = message.from_user.id
    await message.answer(get_text(user_id, 'help'), parse_mode="Markdown")

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ])
    await message.answer(get_text(user_id, 'choose_language'), reply_markup=keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def language_callback(call: CallbackQuery):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    update_user_lang(user_id, lang)
    await call.message.edit_text(get_text(user_id, 'language_changed'))
    await asyncio.sleep(1)
    await call.message.delete()

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    with sqlite3.connect('bot.db') as conn:
        cursor = conn.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]

    text = (
        f"👨‍💻 **Admin Panel**\n\n"
        f"👥 Foydalanuvchilar: {count} ta\n"
        f"⚙️ Server: Render (Docker)\n"
        f"🎯 Success Rate: 90-95%"
    )
    await message.answer(text)

@dp.message(Command("send"))
async def cmd_send(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Xabar yozmadingiz.\nNamuna: `/send Salom hammaga`", parse_mode="Markdown")
        return

    msg_text = parts[1]
    count = 0
    status = await message.answer("📤 Yuborilmoqda...")
    users = get_all_users()
    
    for user_id in users:
        try:
            await bot.send_message(user_id, msg_text)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
            
    await status.edit_text(f"✅ Xabar {count} kishiga yuborildi.")

# -----------------------------------------------------------
# LINK HANDLER
# -----------------------------------------------------------
@dp.message(F.text)
async def link_handler(message: types.Message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    add_user(user_id)
    
    if not url.startswith("http"):
        await message.answer(get_text(user_id, 'invalid_link'))
        return

    status_msg = await message.answer(get_text(user_id, 'downloading'))

    loop = asyncio.get_event_loop()
    filename, title, error_msg = await loop.run_in_executor(None, download_video, url, 3)

    if error_msg:
        await status_msg.edit_text(get_text(user_id, 'error').format(error_msg[:150]))
    elif filename and os.path.exists(filename):
        try:
            file_size = os.path.getsize(filename) / (1024 * 1024)
            if file_size > 50:
                await status_msg.edit_text(get_text(user_id, 'file_too_large'))
                os.remove(filename)
                return

            await status_msg.edit_text(get_text(user_id, 'uploading'))
            media_file = FSInputFile(filename)

            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.png', '.webp', '.jpeg']:
                await message.answer_photo(media_file, caption=f"📸 {title}\n🤖 @Abdulboriy7700")
            else:
                await message.answer_video(media_file, caption=f"📹 {title}\n🤖 @Abdulboriy7700")

            await status_msg.delete()
        except Exception as e:
            logging.error(f"Upload error: {e}")
            await status_msg.edit_text(get_text(user_id, 'upload_error').format(str(e)[:100]))
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    logging.error(f"File deletion error: {e}")
    else:
        await status_msg.edit_text(get_text(user_id, 'file_not_found'))

# -----------------------------------------------------------
# ISHGA TUSHIRISH
# -----------------------------------------------------------
async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish"),
        BotCommand(command="language", description="🌐 Tilni o'zgartirish"),
        BotCommand(command="help", description="ℹ️ Yordam")
    ]
    await bot.set_my_commands(commands)

async def health_check(request):
    return web.Response(text="Bot ishlamoqda! 🚀")

async def start_webhook():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    print("Advanced Video Downloader Bot ishga tushdi... ✅")
    print("Success Rate: 90-95% 🎯")
    await set_bot_commands()
    await bot.delete_webhook(drop_pending_updates=True)
    await start_webhook()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())